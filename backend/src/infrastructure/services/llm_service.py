"""
LLM Service Implementation for CoinStack.

This module implements the ILLMService protocol using LiteLLM for unified
LLM provider access. Supports multiple providers (Anthropic, Google, OpenRouter,
Ollama) with automatic routing, caching, and cost tracking.

Architecture:
    - ConfigLoader: Loads and validates llm_config.yaml
    - LLMCache: SQLite-based response caching with TTL
    - CostTracker: Tracks usage costs per model/capability
    - RateLimiter: Per-coin enrichment rate limiting
    - LLMService: Main service implementing ILLMService

Usage:
    service = LLMService()
    result = await service.normalize_vocab("IMP CAES AVG", "issuer")
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional, Dict, List, Tuple

import yaml

try:
    import litellm
    from litellm import acompletion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    acompletion = None

from src.domain.llm import (
    ILLMService,
    LLMCapability,
    LLMResult,
    VocabNormalizationResult,
    LegendExpansionResult,
    AuctionParseResult,
    ProvenanceParseResult,
    ProvenanceEntry,
    CoinIdentificationResult,
    ReferenceValidationResult,
    LLMError,
    LLMParseError,
    LLMProviderUnavailable,
    LLMRateLimitExceeded,
    LLMBudgetExceeded,
    LLMCapabilityNotAvailable,
)

# Import image processing (optional - graceful degradation if not available)
try:
    from src.infrastructure.services.image_processor import (
        ImageProcessor,
        VisionCache,
        ImageConfig,
        ImageProcessingError,
    )
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False
    ImageProcessor = None  # type: ignore
    VisionCache = None  # type: ignore

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class ModelConfig:
    """Configuration for a single LLM model."""
    name: str
    provider: str
    model_id: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_tokens: int = 4096
    supports_vision: bool = False
    supports_json_mode: bool = True
    local: bool = False


@dataclass
class CapabilityConfig:
    """Configuration for a single capability."""
    name: str
    description: str
    requires_json: bool = True
    requires_vision: bool = False
    cacheable: bool = True
    streaming: bool = False
    profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)


class ConfigLoader:
    """Loads and validates LLM configuration from YAML."""
    
    DEFAULT_CONFIG_PATH = Path("config/llm_config.yaml")
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = {}
        self._models: Dict[str, ModelConfig] = {}
        self._capabilities: Dict[str, CapabilityConfig] = {}
        self._load()
    
    def _load(self):
        """Load and parse configuration file."""
        # Prefer path relative to this file so we always load the same config (backend/config/llm_config.yaml)
        backend_config = Path(__file__).resolve().parent.parent.parent.parent / "config" / "llm_config.yaml"
        paths_to_try = [
            backend_config,
            self.config_path,
            Path("config/llm_config.yaml"),
            Path("backend/config/llm_config.yaml"),
        ]
        
        for path in paths_to_try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Expand environment variables
                    content = self._expand_env_vars(content)
                    self._config = yaml.safe_load(content)
                logger.info("Loaded LLM config from %s (profile=%s)", path, self._config.get("settings", {}).get("active_profile", "?"))
                break
        else:
            logger.warning("LLM config not found, using defaults")
            self._config = self._default_config()
        
        self._parse_models()
        self._parse_capabilities()
    
    def _expand_env_vars(self, content: str) -> str:
        """Expand ${VAR} and ${VAR:-default} patterns."""
        def replace(match):
            var = match.group(1)
            if ":-" in var:
                var_name, default = var.split(":-", 1)
                return os.environ.get(var_name, default)
            return os.environ.get(var, "")
        
        return re.sub(r'\$\{([^}]+)\}', replace, content)
    
    def _default_config(self) -> Dict:
        """Return minimal default configuration."""
        return {
            "settings": {
                "active_profile": "development",
                "default_timeout": 60,
                "max_retries": 3,
                "track_costs": True,
                "monthly_budget_usd": 5.0,
                "cache_enabled": True,
                "rate_limit": {
                    "enrichments_per_coin": 3,
                    "window_minutes": 5,
                },
            },
            "providers": {},
            "models": {},
            "capabilities": {},
        }
    
    def _parse_models(self):
        """Parse model configurations."""
        models_config = self._config.get("models", {})
        for name, cfg in models_config.items():
            self._models[name] = ModelConfig(
                name=name,
                provider=cfg.get("provider", ""),
                model_id=cfg.get("model_id", ""),
                cost_per_1k_input=cfg.get("cost_per_1k_input", 0.0),
                cost_per_1k_output=cfg.get("cost_per_1k_output", 0.0),
                max_tokens=cfg.get("max_tokens", 4096),
                supports_vision=cfg.get("supports_vision", False),
                supports_json_mode=cfg.get("supports_json_mode", True),
                local=cfg.get("local", False),
            )
    
    def _parse_capabilities(self):
        """Parse capability configurations."""
        caps_config = self._config.get("capabilities", {})
        for name, cfg in caps_config.items():
            self._capabilities[name] = CapabilityConfig(
                name=name,
                description=cfg.get("description", ""),
                requires_json=cfg.get("requires_json", True),
                requires_vision=cfg.get("requires_vision", False),
                cacheable=cfg.get("cacheable", True),
                streaming=cfg.get("streaming", False),
                profiles=cfg.get("profiles", {}),
                parameters=cfg.get("parameters", {}),
            )
    
    @property
    def settings(self) -> Dict[str, Any]:
        return self._config.get("settings", {})
    
    @property
    def active_profile(self) -> str:
        return self.settings.get("active_profile", "development")
    
    @property
    def monthly_budget(self) -> float:
        return self.settings.get("monthly_budget_usd", 5.0)
    
    @property
    def rate_limit_config(self) -> Dict[str, Any]:
        return self.settings.get("rate_limit", {})
    
    def get_model(self, name: str) -> Optional[ModelConfig]:
        return self._models.get(name)
    
    def get_capability(self, name: str) -> Optional[CapabilityConfig]:
        return self._capabilities.get(name)
    
    def get_model_for_capability(
        self,
        capability: str,
        profile: Optional[str] = None
    ) -> Tuple[Optional[ModelConfig], List[str]]:
        """
        Get the primary model and fallback list for a capability.
        
        Returns:
            Tuple of (primary_model, fallback_model_names)
        """
        profile = profile or self.active_profile
        cap_cfg = self._capabilities.get(capability)
        
        if not cap_cfg:
            return None, []
        
        profile_cfg = cap_cfg.profiles.get(profile, {})
        primary_name = profile_cfg.get("primary")
        fallback_names = profile_cfg.get("fallback", [])
        
        primary = self._models.get(primary_name) if primary_name else None
        return primary, fallback_names
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get provider-specific configuration."""
        providers = self._config.get("providers", {})
        return providers.get(provider, {})


# =============================================================================
# CACHING
# =============================================================================

class LLMCache:
    """SQLite-based LLM response cache with TTL support."""
    
    def __init__(self, db_path: str = "data/llm_cache.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(str(self.db_path))
        return self._local.conn
    
    def _init_db(self):
        """Initialize cache database."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_cache (
                cache_key TEXT PRIMARY KEY,
                response TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                capability TEXT,
                model TEXT,
                cost_usd REAL DEFAULT 0.0
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_expires 
            ON llm_cache(expires_at)
        """)
        conn.commit()
    
    def _hash_key(self, capability: str, prompt: str, context: Optional[Dict] = None) -> str:
        """Generate cache key from inputs."""
        key_data = {
            "capability": capability,
            "prompt": prompt,
            "context": context or {},
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]
    
    async def get(
        self,
        capability: str,
        prompt: str,
        context: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached response if not expired."""
        cache_key = self._hash_key(capability, prompt, context)
        conn = self._get_conn()
        
        cursor = conn.execute(
            """
            SELECT response, created_at, model, cost_usd
            FROM llm_cache
            WHERE cache_key = ? AND expires_at > datetime('now')
            """,
            (cache_key,)
        )
        row = cursor.fetchone()
        
        if row:
            logger.debug(f"Cache hit for {capability}")
            return {
                "response": json.loads(row[0]),
                "created_at": row[1],
                "model": row[2],
                "cost_usd": row[3],
            }
        return None
    
    async def set(
        self,
        capability: str,
        prompt: str,
        response: Any,
        model: str,
        cost_usd: float,
        ttl_hours: int = 168,
        context: Optional[Dict] = None,
    ):
        """Cache response with TTL."""
        cache_key = self._hash_key(capability, prompt, context)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=ttl_hours)
        
        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO llm_cache 
            (cache_key, response, created_at, expires_at, capability, model, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cache_key,
                json.dumps(response),
                now.isoformat(),
                expires.isoformat(),
                capability,
                model,
                cost_usd,
            )
        )
        conn.commit()
    
    def clear_expired(self):
        """Remove expired entries."""
        conn = self._get_conn()
        conn.execute("DELETE FROM llm_cache WHERE expires_at < datetime('now')")
        conn.commit()


# =============================================================================
# COST TRACKING
# =============================================================================

class CostTracker:
    """Tracks LLM usage costs in SQLite."""
    
    def __init__(self, db_path: str = "data/llm_costs.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(str(self.db_path))
        return self._local.conn
    
    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model TEXT NOT NULL,
                capability TEXT NOT NULL,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cost_usd REAL NOT NULL,
                cached INTEGER DEFAULT 0,
                request_id TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_costs_timestamp 
            ON llm_costs(timestamp)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_costs_model 
            ON llm_costs(model)
        """)
        conn.commit()
    
    async def record(
        self,
        model: str,
        capability: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        cached: bool = False,
        request_id: Optional[str] = None,
    ):
        """Record a usage entry."""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO llm_costs 
            (timestamp, model, capability, input_tokens, output_tokens, cost_usd, cached, request_id)
            VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?)
            """,
            (model, capability, input_tokens, output_tokens, cost_usd, 1 if cached else 0, request_id)
        )
        conn.commit()
    
    def get_monthly_cost(self) -> float:
        """Get total cost for current month."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT COALESCE(SUM(cost_usd), 0.0) FROM llm_costs
            WHERE timestamp >= date('now', 'start of month')
            """
        )
        return cursor.fetchone()[0]
    
    def get_cost_by_capability(self, days: int = 30) -> Dict[str, float]:
        """Get cost breakdown by capability."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT capability, SUM(cost_usd) FROM llm_costs
            WHERE timestamp >= datetime('now', ?)
            GROUP BY capability
            """,
            (f"-{days} days",)
        )
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def get_cost_by_model(self, days: int = 30) -> Dict[str, float]:
        """Get cost breakdown by model."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT model, SUM(cost_usd) FROM llm_costs
            WHERE timestamp >= datetime('now', ?)
            GROUP BY model
            """,
            (f"-{days} days",)
        )
        return {row[0]: row[1] for row in cursor.fetchall()}


# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimiter:
    """In-memory rate limiter for enrichment operations."""
    
    def __init__(self, max_per_window: int = 3, window_minutes: int = 5):
        self.max_per_window = max_per_window
        self.window_minutes = window_minutes
        self._requests: Dict[str, List[datetime]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def check(self, key: str) -> Tuple[bool, int]:
        """
        Check if request is allowed.
        
        Returns:
            Tuple of (is_allowed, seconds_until_retry)
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(minutes=self.window_minutes)
            
            # Clean old requests
            self._requests[key] = [
                ts for ts in self._requests[key] if ts > cutoff
            ]
            
            if len(self._requests[key]) >= self.max_per_window:
                # Calculate retry time
                oldest = min(self._requests[key])
                retry_after = int((oldest + timedelta(minutes=self.window_minutes) - now).total_seconds())
                return False, max(1, retry_after)
            
            return True, 0
    
    def record(self, key: str):
        """Record a request."""
        with self._lock:
            self._requests[key].append(datetime.now(timezone.utc))
    
    def count(self, key: str) -> int:
        """Get current count for key."""
        with self._lock:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(minutes=self.window_minutes)
            self._requests[key] = [
                ts for ts in self._requests[key] if ts > cutoff
            ]
            return len(self._requests[key])


# =============================================================================
# IDEMPOTENCY
# =============================================================================

class IdempotencyStore:
    """In-memory idempotency store for request deduplication."""
    
    def __init__(self, ttl_minutes: int = 60):
        self.ttl_minutes = ttl_minutes
        self._store: Dict[str, Tuple[Any, datetime]] = {}
        self._lock = threading.Lock()
    
    def get(self, request_id: str) -> Optional[Any]:
        """Get cached result for request ID."""
        with self._lock:
            if request_id in self._store:
                result, timestamp = self._store[request_id]
                if datetime.now(timezone.utc) - timestamp < timedelta(minutes=self.ttl_minutes):
                    logger.debug(f"Idempotency hit for {request_id}")
                    return result
                # Expired
                del self._store[request_id]
            return None
    
    def set(self, request_id: str, result: Any):
        """Store result for request ID."""
        with self._lock:
            self._store[request_id] = (result, datetime.now(timezone.utc))
    
    def cleanup(self):
        """Remove expired entries."""
        with self._lock:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.ttl_minutes)
            self._store = {
                k: v for k, v in self._store.items()
                if v[1] > cutoff
            }


# =============================================================================
# PROMPT LOADER
# =============================================================================

class PromptLoader:
    """Loads prompt templates from YAML configuration."""
    
    DEFAULT_PATH = Path("config/prompts/capabilities.yaml")
    
    def __init__(self, prompts_path: Optional[Path] = None):
        self.prompts_path = prompts_path or self.DEFAULT_PATH
        self._prompts: Dict[str, Dict[str, Any]] = {}
        self._load()
    
    def _load(self):
        """Load prompts from YAML file."""
        paths_to_try = [
            self.prompts_path,
            Path(__file__).parent.parent.parent.parent / "config" / "prompts" / "capabilities.yaml",
            Path("backend/config/prompts/capabilities.yaml"),
        ]
        
        for path in paths_to_try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._prompts = yaml.safe_load(f) or {}
                logger.info(f"Loaded prompts from {path}")
                return
        
        logger.warning("Prompts file not found, using built-in defaults")
        self._prompts = {}
    
    def get_system_prompt(self, capability: str) -> str:
        """Get system prompt for capability."""
        cap_prompts = self._prompts.get(capability, {})
        return cap_prompts.get("system", self._default_system_prompt(capability))
    
    def get_user_template(self, capability: str) -> str:
        """Get user prompt template for capability."""
        cap_prompts = self._prompts.get(capability, {})
        return cap_prompts.get("user_template", "{input}")
    
    def _default_system_prompt(self, capability: str) -> str:
        """Return default system prompts for capabilities."""
        defaults = {
            "vocab_normalize": """You are a numismatic vocabulary expert specializing in ancient coins.
Given raw text, return ONLY the canonical form for the specified vocabulary type.
Use anglicized names (Augustus not Octavian, Trajan not Traianus).
Return a JSON object: {"canonical_name": "...", "confidence": 0.0-1.0, "reasoning": ["..."]}""",
            
            "legend_expand": """You are a Roman numismatic expert specializing in Latin epigraphy.
Expand abbreviated Latin legends to their full form.
Common abbreviations: IMP=Imperator, CAES=Caesar, AVG=Augustus, P M=Pontifex Maximus, TR P=Tribunicia Potestate, COS=Consul, P P=Pater Patriae, S C=Senatus Consulto.
Return ONLY the expanded Latin text.""",
            
            "auction_parse": """You are an expert at parsing auction lot descriptions for ancient coins.
Extract structured data from the description text.
Return a JSON object with fields: issuer, denomination, metal, mint, year_start, year_end, weight_g, diameter_mm, obverse_legend, obverse_description, reverse_legend, reverse_description, references, grade.
Use null for fields that cannot be determined. Include a confidence score 0.0-1.0.""",
            
            "provenance_parse": """You are an expert at parsing coin provenance from auction descriptions.
Extract the chain of ownership/sales from the text.
Return a JSON object: {"provenance_chain": [{"source": "...", "source_type": "auction|collection|dealer", "year": ..., "sale": "...", "lot": "..."}], "earliest_known": ..., "confidence": 0.0-1.0}""",
            
            "image_identify": """You are an expert numismatist specializing in ancient coin identification.
Analyze the coin image(s) and identify: ruler/authority, denomination, mint, date range, obverse/reverse descriptions, and suggested catalog references.
Return a JSON object with these fields plus confidence 0.0-1.0.""",
            
            "reference_validate": """You are an expert in ancient coin catalog systems (RIC, RSC, RPC, Crawford, Sear, BMC).
Validate the given catalog reference and suggest alternatives if incorrect.
Return a JSON object: {"is_valid": true/false, "normalized": "...", "alternatives": [...], "notes": "...", "confidence": 0.0-1.0}""",
            
            "context_generate": """You are a historian specializing in ancient numismatics.
Generate an engaging historical narrative about this coin and its context.
Include information about the ruler, historical events, and significance of the coin type.
Write 2-3 paragraphs in an educational but accessible style.""",
        }
        return defaults.get(capability, "You are a helpful numismatic assistant.")


# =============================================================================
# MAIN LLM SERVICE
# =============================================================================

class LLMService(ILLMService):
    """
    Main LLM service implementation.
    
    Implements the ILLMService protocol with:
    - Multi-provider support via LiteLLM
    - Automatic model routing based on capability and profile
    - Response caching with TTL
    - Cost tracking and budget enforcement
    - Rate limiting per coin
    - Request idempotency
    """
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        cache_enabled: bool = True,
        cost_tracking: bool = True,
    ):
        self.config = ConfigLoader(config_path)
        self.prompt_loader = PromptLoader()
        
        # Initialize components
        if cache_enabled:
            cache_path = self.config.settings.get("cache_path", "data/llm_cache.sqlite")
            self.cache = LLMCache(cache_path)
        else:
            self.cache = None
        
        if cost_tracking:
            cost_path = self.config.settings.get("cost_log_path", "data/llm_costs.sqlite")
            self.cost_tracker = CostTracker(cost_path)
        else:
            self.cost_tracker = None
        
        # Rate limiter
        rate_cfg = self.config.rate_limit_config
        self.rate_limiter = RateLimiter(
            max_per_window=rate_cfg.get("enrichments_per_coin", 3),
            window_minutes=rate_cfg.get("window_minutes", 5),
        )
        
        # Idempotency
        self.idempotency = IdempotencyStore()
        
        # Image processing (for P1 vision capabilities)
        if IMAGE_PROCESSING_AVAILABLE:
            self.image_processor = ImageProcessor()
            if cache_enabled:
                vision_cache_path = self.config.settings.get(
                    "vision_cache_path", "data/llm_vision_cache.sqlite"
                )
                self.vision_cache = VisionCache(vision_cache_path)
            else:
                self.vision_cache = None
        else:
            self.image_processor = None
            self.vision_cache = None
            logger.warning("Image processing not available. Vision capabilities limited.")
        
        # Check LiteLLM availability
        if not LITELLM_AVAILABLE:
            logger.warning("LiteLLM not installed. LLM operations will fail.")
    
    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------
    
    @staticmethod
    def _strip_markdown_json(content: str) -> str:
        """
        Strip markdown code block formatting from JSON responses.
        
        Handles formats like:
        - ```json\n{...}\n```
        - ```\n{...}\n```
        - Direct JSON
        """
        content = content.strip()
        
        # Remove ```json or ``` at start
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        # Remove ``` at end
        if content.endswith("```"):
            content = content[:-3]
        
        return content.strip()
    
    # -------------------------------------------------------------------------
    # Core completion method
    # -------------------------------------------------------------------------
    
    async def complete(
        self,
        capability: LLMCapability,
        prompt: str,
        system: Optional[str] = None,
        context: Optional[dict] = None,
        image_b64: Optional[str] = None,
    ) -> LLMResult:
        """
        Generic completion for any capability.
        """
        cap_name = capability.value
        
        # Check capability availability
        if not self.is_capability_available(capability):
            raise LLMCapabilityNotAvailable(cap_name, self.config.active_profile)
        
        # Get system prompt
        if system is None:
            system = self.prompt_loader.get_system_prompt(cap_name)
        
        # Check cache
        cap_cfg = self.config.get_capability(cap_name)
        if self.cache and cap_cfg and cap_cfg.cacheable:
            cached = await self.cache.get(cap_name, prompt, context)
            if cached:
                return LLMResult(
                    content=cached["response"].get("content", ""),
                    confidence=cached["response"].get("confidence", 1.0),
                    cost_usd=0.0,
                    model_used=cached.get("model", "cached"),
                    cached=True,
                )
        
        # Check budget
        if self.cost_tracker:
            monthly_cost = self.cost_tracker.get_monthly_cost()
            if monthly_cost >= self.config.monthly_budget:
                raise LLMBudgetExceeded(
                    "Monthly budget exceeded",
                    monthly_cost,
                    self.config.monthly_budget
                )
        
        # Get model for capability
        primary_model, fallbacks = self.config.get_model_for_capability(cap_name)
        if not primary_model:
            raise LLMCapabilityNotAvailable(cap_name, self.config.active_profile)
        
        # Try primary then fallbacks
        models_to_try = [primary_model.name] + fallbacks
        providers_tried = []
        first_error = None
        last_error = None
        logger.info(
            "LLM %s: profile=%s, primary=%s, fallbacks=%s",
            cap_name, self.config.active_profile, primary_model.name, fallbacks,
        )
        
        for model_name in models_to_try:
            model_cfg = self.config.get_model(model_name)
            if not model_cfg:
                continue
            
            providers_tried.append(model_name)
            
            try:
                result = await self._call_model(
                    model_cfg=model_cfg,
                    capability=cap_name,
                    system=system,
                    prompt=prompt,
                    context=context,
                    image_b64=image_b64,
                    cap_cfg=cap_cfg,
                )
                
                # Cache successful result
                if self.cache and cap_cfg and cap_cfg.cacheable:
                    await self.cache.set(
                        capability=cap_name,
                        prompt=prompt,
                        response={"content": result.content, "confidence": result.confidence},
                        model=model_cfg.name,
                        cost_usd=result.cost_usd,
                        context=context,
                    )
                
                return result
                
            except Exception as e:
                logger.warning("Model %s failed: %s", model_name, e)
                if first_error is None:
                    first_error = e
                last_error = e
                continue
        
        err_msg = f"All providers failed: {last_error}"
        if first_error is not None and first_error is not last_error:
            err_msg = f"All providers failed (first: {first_error}; last: {last_error})"
        raise LLMProviderUnavailable(err_msg, providers_tried)
    
    async def _call_model(
        self,
        model_cfg: ModelConfig,
        capability: str,
        system: str,
        prompt: str,
        context: Optional[dict],
        image_b64: Optional[str],
        cap_cfg: Optional[CapabilityConfig],
    ) -> LLMResult:
        """Make actual LLM call."""
        if not LITELLM_AVAILABLE:
            raise LLMError("LiteLLM not installed")
        
        # Build messages
        messages = [
            {"role": "system", "content": system},
        ]
        
        # Handle vision
        if image_b64 and model_cfg.supports_vision:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                ],
            })
        else:
            messages.append({"role": "user", "content": prompt})
        
        # Build model string for LiteLLM
        model_str = self._get_litellm_model_string(model_cfg)
        
        # Get parameters
        params = {}
        if cap_cfg:
            params = dict(cap_cfg.parameters)
        
        # Make call (timeout: capability override > settings default)
        timeout_sec = params.get("timeout") or self.config.settings.get("default_timeout", 60)
        try:
            response = await acompletion(
                model=model_str,
                messages=messages,
                temperature=params.get("temperature", 0.3),
                max_tokens=params.get("max_tokens", model_cfg.max_tokens),
                timeout=timeout_sec,
            )
        except Exception as e:
            raise LLMError(f"LLM call failed: {e}")
        
        # Extract response
        content = response.choices[0].message.content
        
        # Calculate cost
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0
        cost = (
            (input_tokens / 1000) * model_cfg.cost_per_1k_input +
            (output_tokens / 1000) * model_cfg.cost_per_1k_output
        )
        
        # Track cost
        if self.cost_tracker:
            await self.cost_tracker.record(
                model=model_cfg.name,
                capability=capability,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
            )
        
        # Parse confidence if JSON response
        confidence = 0.8  # Default
        reasoning = []
        if cap_cfg and cap_cfg.requires_json:
            try:
                parsed = json.loads(content)
                confidence = parsed.get("confidence", 0.8)
                reasoning = parsed.get("reasoning", [])
            except json.JSONDecodeError:
                pass
        
        return LLMResult(
            content=content,
            confidence=confidence,
            cost_usd=cost,
            model_used=model_cfg.name,
            cached=False,
            reasoning=reasoning,
        )
    
    def _get_litellm_model_string(self, model_cfg: ModelConfig) -> str:
        """Build LiteLLM model string based on provider."""
        provider = model_cfg.provider
        model_id = model_cfg.model_id

        if provider == "anthropic":
            return model_id
        elif provider == "google":
            return f"gemini/{model_id}"
        elif provider == "openrouter":
            # Avoid double prefix: config may store "openrouter/foo" or "deepseek/bar"
            if model_id.startswith("openrouter/"):
                return model_id
            return f"openrouter/{model_id}"
        elif provider == "ollama":
            return f"ollama/{model_id}"
        else:
            return model_id
    
    # -------------------------------------------------------------------------
    # P0 Capability implementations
    # -------------------------------------------------------------------------
    
    async def normalize_vocab(
        self,
        raw_text: str,
        vocab_type: str,
        context: Optional[dict] = None,
        vocab_repo: Optional[Any] = None,  # IVocabRepository for fallback
    ) -> VocabNormalizationResult:
        """
        Normalize vocabulary term to canonical form.
        
        Includes graceful degradation: if LLM is unavailable, falls back
        to fuzzy string matching against the vocabulary database.
        
        Args:
            raw_text: Raw input text
            vocab_type: Type ("issuer", "mint", "denomination")
            context: Optional context dict
            vocab_repo: Optional vocab repository for fallback
        
        Returns:
            VocabNormalizationResult with canonical name
        """
        prompt = f"Vocab type: {vocab_type}\nRaw text: \"{raw_text}\""
        if context:
            prompt += f"\nContext: {json.dumps(context)}"
        
        try:
            result = await self.complete(
                capability=LLMCapability.VOCAB_NORMALIZE,
                prompt=prompt,
                context={"vocab_type": vocab_type, "raw_text": raw_text},
            )
            
            # Parse JSON response (strip markdown if present)
            parsed_confidence = result.confidence
            reasoning = result.reasoning
            try:
                cleaned = self._strip_markdown_json(result.content)
                parsed = json.loads(cleaned)
                canonical = parsed.get("canonical_name", "")
                reasoning = parsed.get("reasoning", result.reasoning)
                parsed_confidence = parsed.get("confidence", result.confidence)
            except json.JSONDecodeError:
                canonical = result.content.strip()
            
            return VocabNormalizationResult(
                content=result.content,
                confidence=parsed_confidence,
                cost_usd=result.cost_usd,
                model_used=result.model_used,
                cached=result.cached,
                reasoning=reasoning,
                raw_input=raw_text,
                canonical_name=canonical,
                vocab_type=vocab_type,
            )
        
        except LLMProviderUnavailable as e:
            logger.warning(f"LLM unavailable for vocab_normalize, using fallback: {e}")
            
            # Fallback to fuzzy search if vocab_repo provided
            if vocab_repo:
                return await self._vocab_normalize_fallback(
                    raw_text, vocab_type, vocab_repo
                )
            
            # Re-raise if no fallback available
            raise
    
    async def _vocab_normalize_fallback(
        self,
        raw_text: str,
        vocab_type: str,
        vocab_repo: Any,
    ) -> VocabNormalizationResult:
        """
        Fallback vocab normalization using fuzzy string matching.
        
        Used when LLM providers are unavailable.
        """
        from src.domain.llm import FuzzyMatch
        
        # Try fuzzy search
        matches: List[FuzzyMatch] = vocab_repo.fuzzy_search(
            query=raw_text,
            vocab_type=vocab_type,
            limit=3,
            min_score=0.5,
        )
        
        if matches and matches[0].score > 0.7:
            best = matches[0]
            # Discount confidence for non-LLM match
            confidence = best.score * 0.8
            
            return VocabNormalizationResult(
                content=json.dumps({
                    "canonical_name": best.canonical_name,
                    "confidence": confidence,
                    "reasoning": ["Fuzzy match fallback (LLM unavailable)"],
                }),
                confidence=confidence,
                cost_usd=0.0,
                model_used="fuzzy_match_fallback",
                cached=False,
                reasoning=["Fuzzy match fallback (LLM unavailable)"],
                raw_input=raw_text,
                canonical_name=best.canonical_name,
                vocab_type=vocab_type,
            )
        
        # No good match found
        return VocabNormalizationResult(
            content=json.dumps({
                "canonical_name": "",
                "confidence": 0.0,
                "reasoning": ["No match found (LLM unavailable, fuzzy search failed)"],
            }),
            confidence=0.0,
            cost_usd=0.0,
            model_used="fuzzy_match_fallback",
            cached=False,
            reasoning=["No match found (LLM unavailable, fuzzy search failed)"],
            raw_input=raw_text,
            canonical_name="",
            vocab_type=vocab_type,
        )
    
    async def expand_legend(
        self,
        abbreviation: str,
    ) -> LegendExpansionResult:
        """Expand abbreviated Latin legend."""
        prompt = f"Expand: {abbreviation}"
        
        result = await self.complete(
            capability=LLMCapability.LEGEND_EXPAND,
            prompt=prompt,
            context={"abbreviation": abbreviation},
        )
        
        expanded = result.content.strip()
        
        return LegendExpansionResult(
            content=result.content,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
            model_used=result.model_used,
            cached=result.cached,
            reasoning=result.reasoning,
            abbreviated=abbreviation,
            expanded=expanded,
        )
    
    async def parse_auction(
        self,
        description: str,
        hints: Optional[dict] = None,
    ) -> AuctionParseResult:
        """Parse auction lot description into structured data."""
        prompt = f"Parse this auction lot description:\n\n{description}"
        if hints:
            prompt += f"\n\nHints: {json.dumps(hints)}"
        
        result = await self.complete(
            capability=LLMCapability.AUCTION_PARSE,
            prompt=prompt,
            context={"description": description[:100]},  # Truncate for cache key
        )
        
        # Parse JSON response (strip markdown if present)
        try:
            cleaned = self._strip_markdown_json(result.content)
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise LLMParseError(
                f"Failed to parse auction response: {e}",
                result.content,
                "auction_parse"
            )
        
        return AuctionParseResult(
            content=result.content,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
            model_used=result.model_used,
            cached=result.cached,
            reasoning=result.reasoning,
            raw_text=description,
            issuer=parsed.get("issuer"),
            denomination=parsed.get("denomination"),
            metal=parsed.get("metal"),
            mint=parsed.get("mint"),
            year_start=parsed.get("year_start"),
            year_end=parsed.get("year_end"),
            weight_g=parsed.get("weight_g"),
            diameter_mm=parsed.get("diameter_mm"),
            obverse_legend=parsed.get("obverse_legend"),
            obverse_description=parsed.get("obverse_description"),
            reverse_legend=parsed.get("reverse_legend"),
            reverse_description=parsed.get("reverse_description"),
            references=parsed.get("references", []),
            grade=parsed.get("grade"),
        )
    
    async def parse_provenance(
        self,
        description: str,
    ) -> ProvenanceParseResult:
        """Extract provenance chain from description text."""
        prompt = f"Extract provenance from:\n\n{description}"
        
        result = await self.complete(
            capability=LLMCapability.PROVENANCE_PARSE,
            prompt=prompt,
            context={"description": description[:100]},
        )
        
        # Parse JSON response
        try:
            parsed = json.loads(self._strip_markdown_json(result.content))
        except json.JSONDecodeError as e:
            raise LLMParseError(
                f"Failed to parse provenance response: {e}",
                result.content,
                "provenance_parse"
            )
        
        # Build provenance chain
        chain = []
        for entry in parsed.get("provenance_chain", []):
            chain.append(ProvenanceEntry(
                source=entry.get("source", ""),
                source_type=entry.get("source_type", "unknown"),
                year=entry.get("year"),
                sale=entry.get("sale"),
                lot=entry.get("lot"),
            ))
        
        return ProvenanceParseResult(
            content=result.content,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
            model_used=result.model_used,
            cached=result.cached,
            reasoning=result.reasoning,
            raw_text=description,
            provenance_chain=chain,
            earliest_known=parsed.get("earliest_known"),
        )
    
    # -------------------------------------------------------------------------
    # P1 Capability implementations
    # -------------------------------------------------------------------------
    
    async def identify_coin(
        self,
        image_b64: str,
        hints: Optional[dict] = None,
    ) -> CoinIdentificationResult:
        """
        Identify coin from image.
        
        Uses image preprocessing to validate and resize images,
        and vision cache to avoid repeated API calls for similar images.
        """
        # Decode and preprocess image
        import base64
        image_bytes = base64.b64decode(image_b64)
        
        # Check vision cache first (uses perceptual hash)
        if self.vision_cache:
            cached = await self.vision_cache.get(image_bytes, "image_identify")
            if cached:
                response = cached["response"]
                return CoinIdentificationResult(
                    content=json.dumps(response),
                    confidence=response.get("confidence", 0.8),
                    cost_usd=0.0,
                    model_used=cached.get("model", "cached"),
                    cached=True,
                    ruler=response.get("ruler"),
                    denomination=response.get("denomination"),
                    mint=response.get("mint"),
                    date_range=response.get("date_range"),
                    obverse_description=response.get("obverse_description"),
                    reverse_description=response.get("reverse_description"),
                    suggested_references=response.get("suggested_references", []),
                )
        
        # Preprocess image if processor available
        if self.image_processor:
            try:
                preprocessed = self.image_processor.preprocess(image_bytes)
                image_b64 = base64.b64encode(preprocessed).decode("utf-8")
            except Exception as e:
                logger.warning(f"Image preprocessing failed: {e}")
                # Continue with original image
        
        prompt = "Identify this ancient coin. Provide: ruler, denomination, mint, date range, obverse/reverse descriptions, and suggested catalog references."
        if hints:
            prompt += f"\n\nHints: {json.dumps(hints)}"
        
        result = await self.complete(
            capability=LLMCapability.IMAGE_IDENTIFY,
            prompt=prompt,
            image_b64=image_b64,
        )
        
        # Parse JSON response
        try:
            parsed = json.loads(self._strip_markdown_json(result.content))
        except json.JSONDecodeError:
            parsed = {}
        
        # Cache result with vision cache
        if self.vision_cache and not result.cached:
            await self.vision_cache.set(
                image_bytes=image_bytes,
                capability="image_identify",
                response=parsed,
                model=result.model_used,
                cost_usd=result.cost_usd,
            )
        
        return CoinIdentificationResult(
            content=result.content,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
            model_used=result.model_used,
            cached=result.cached,
            reasoning=result.reasoning,
            ruler=parsed.get("ruler"),
            denomination=parsed.get("denomination"),
            mint=parsed.get("mint"),
            date_range=parsed.get("date_range"),
            obverse_description=parsed.get("obverse_description"),
            reverse_description=parsed.get("reverse_description"),
            suggested_references=parsed.get("suggested_references", []),
        )
    
    async def validate_reference(
        self,
        reference: str,
        coin_context: Optional[dict] = None,
    ) -> ReferenceValidationResult:
        """Validate and cross-reference catalog number."""
        prompt = f"Validate this catalog reference: {reference}"
        if coin_context:
            prompt += f"\n\nCoin context: {json.dumps(coin_context)}"
        
        result = await self.complete(
            capability=LLMCapability.REFERENCE_VALIDATE,
            prompt=prompt,
            context={"reference": reference},
        )
        
        # Parse JSON response
        try:
            parsed = json.loads(self._strip_markdown_json(result.content))
        except json.JSONDecodeError:
            parsed = {}
        
        return ReferenceValidationResult(
            content=result.content,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
            model_used=result.model_used,
            cached=result.cached,
            reasoning=result.reasoning,
            reference=reference,
            is_valid=parsed.get("is_valid", False),
            normalized=parsed.get("normalized", reference),
            alternatives=parsed.get("alternatives", []),
            notes=parsed.get("notes", ""),
        )
    
    # Section keys for parsing context response
    CONTEXT_SECTIONS = [
        "EPIGRAPHY_AND_TITLES",
        "ICONOGRAPHY_AND_SYMBOLISM", 
        "ARTISTIC_STYLE",
        "PROPAGANDA_AND_MESSAGING",
        "ECONOMIC_CONTEXT",
        "DIE_STUDIES_AND_VARIETIES",
        "ARCHAEOLOGICAL_CONTEXT",
        "TYPOLOGICAL_RELATIONSHIPS",
        "MILITARY_HISTORY",
        "HISTORICAL_CONTEXT",
        "NUMISMATIC_SIGNIFICANCE",
    ]
    
    # Known catalog reference patterns
    CATALOG_PATTERNS = [
        # RIC - Roman Imperial Coinage (most common)
        # Handles: RIC II 123, RIC IV.1 289c, RIC IVi 289c, RIC IV 289
        r'\bRIC\s+[IVX]+(?:\.\d+|i)?\s*,?\s*\d+[a-z]?\b',
        # RSC - Roman Silver Coins (Seaby)
        r'\bRSC\s+\d+[a-z]?\b',                                                # RSC 382
        # RRC - Roman Republican Coinage (Crawford)
        r'\bRRC\s+\d+(?:/\d+)?[a-z]?\b',                                       # RRC 494/23a
        r'\bCrawford\s+\d+(?:/\d+)?[a-z]?\b',                                  # Crawford 494/23
        # Sear (Roman Coins and Their Values)
        r'\bSear\s+\d+\b',                                                     # Sear 6846
        r'\bSear\s+RCV\s+\d+\b',                                               # Sear RCV 6846
        # Cohen (French catalog)
        r'\bCohen\s+\d+\b',                                                    # Cohen 382
        # BMC/BMCRE - British Museum Catalogue
        r'\bBMC(?:RE)?\s+(?:[IVXLC]+|\d+)?\s*,?\s*\d+\b',                     # BMC III 234, BMCRE 842
        # RPC - Roman Provincial Coinage (with comma/space variants)
        r'\bRPC\s+[IVXLC]+\s*,?\s*\d+\??\b',                                  # RPC III, 3129 or RPC III 3129?
        # SNG - Sylloge Nummorum Graecorum
        r'\bSNG\s+\w+\s+\d+\b',                                                # SNG Copenhagen 123
        # Calico (Spanish gold)
        r'\bCalic[oó]\s+\d+[a-z]?\b',                                         # Calico 123
        # Woytek (Trajanic coinage)
        r'\bWoytek\s+\d+[a-z]?\b',                                            # Woytek 123
        # Hill (Byzantine)
        r'\bHill\s+\d+\b',                                                     # Hill 123
        # DOC - Dumbarton Oaks Catalogue
        r'\bDOC\s+[IVXLC]+\s*,?\s*\d+\b',                                     # DOC I 123
        # MIB - Moneta Imperii Byzantini
        r'\bMIB\s+[IVXLC]+\s+\d+\b',                                          # MIB I 123
    ]
    
    def _parse_citations(self, content: str) -> List[str]:
        """
        Extract catalog citations from LLM response.
        
        Looks for standard numismatic reference patterns like:
        - RIC IVi 289c
        - RSC 382
        - Cohen 382
        - Sear 6846
        - Crawford 494/23
        - BMC III 234
        
        Returns deduplicated list of found citations.
        """
        citations = set()
        
        for pattern in self.CATALOG_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Normalize whitespace and clean up
                cleaned = " ".join(match.split())
                citations.add(cleaned)
        
        # Sort for consistent output
        return sorted(citations, key=lambda x: (x.split()[0], x))
    
    def _normalize_reference(self, ref: str) -> str:
        """Normalize a reference string for comparison."""
        # Lowercase, remove extra spaces, normalize Roman numerals
        normalized = " ".join(ref.upper().split())
        # Remove punctuation variations
        normalized = normalized.replace(".", " ").replace(",", " ").replace("-", " ")
        normalized = " ".join(normalized.split())
        return normalized
    
    def _compare_references(
        self, 
        llm_refs: List[str], 
        existing_refs: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Compare LLM-found references with existing database references.
        
        Returns:
            Tuple of (new_suggestions, matched_existing)
        """
        # Normalize existing refs for comparison
        existing_normalized = {
            self._normalize_reference(r): r for r in existing_refs
        }
        
        new_suggestions = []
        matched = []
        
        for llm_ref in llm_refs:
            llm_norm = self._normalize_reference(llm_ref)
            
            # Check if any existing ref matches
            found_match = False
            for exist_norm, exist_orig in existing_normalized.items():
                # Fuzzy match: check if core components match
                # e.g., "RIC IVI 289C" should match "RIC IV.1 289c"
                llm_parts = llm_norm.split()
                exist_parts = exist_norm.split()
                
                if len(llm_parts) >= 2 and len(exist_parts) >= 2:
                    # Compare catalog system
                    if llm_parts[0] == exist_parts[0]:
                        # Compare number (last element usually)
                        llm_num = llm_parts[-1].rstrip("ABCDEFGHIJ")
                        exist_num = exist_parts[-1].rstrip("ABCDEFGHIJ")
                        if llm_num == exist_num:
                            found_match = True
                            matched.append(exist_orig)
                            break
            
            if not found_match:
                new_suggestions.append(llm_ref)
        
        return new_suggestions, matched
    
    def _parse_rarity(self, content: str) -> Dict[str, Any]:
        """
        Extract rarity information from structured LLM response.
        
        Expects format in RARITY_ASSESSMENT section:
        ```
        RARITY_CODE: C
        RARITY_DESCRIPTION: Common
        SOURCE: RIC IV.1 rates as C
        SPECIMENS_KNOWN: Unknown
        ```
        
        Returns dict with parsed rarity data.
        """
        result = {
            "rarity_code": None,
            "rarity_description": None,
            "specimens_known": None,
            "source": None,
            "raw_section": None,
        }
        
        # Look for RARITY_ASSESSMENT section
        rarity_section_match = re.search(
            r'##\s*RARITY_ASSESSMENT\s*\n(.*?)(?=\n##|\[END|$)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        
        if not rarity_section_match:
            # Fallback: try to find structured fields anywhere
            pass
        else:
            section_text = rarity_section_match.group(1)
            result["raw_section"] = section_text.strip()
        
        # Strip markdown code block markers if present
        clean_content = re.sub(r'```\w*\n?', '', content)
        
        # Parse structured fields (can be anywhere in content)
        # RARITY_CODE: [value]
        code_match = re.search(
            r'RARITY_CODE:\s*(C|S|R[1-5]|RR|RRR|UNIQUE|UNKNOWN)\b',
            clean_content,
            re.IGNORECASE
        )
        if code_match:
            code = code_match.group(1).upper()
            if code != "UNKNOWN":
                result["rarity_code"] = code
        
        # RARITY_DESCRIPTION: [value]
        desc_match = re.search(
            r'RARITY_DESCRIPTION:\s*([^\n]+)',
            clean_content,
            re.IGNORECASE
        )
        if desc_match:
            desc = desc_match.group(1).strip()
            if desc.lower() != "unknown":
                result["rarity_description"] = desc
        
        # SOURCE: [value]
        source_match = re.search(
            r'SOURCE:\s*([^\n]+)',
            clean_content,
            re.IGNORECASE
        )
        if source_match:
            source = source_match.group(1).strip()
            if source.lower() not in ("unknown", "none", "n/a"):
                result["source"] = source
        
        # SPECIMENS_KNOWN: [value]
        specimens_match = re.search(
            r'SPECIMENS_KNOWN:\s*(\d+|[^\n]+)',
            clean_content,
            re.IGNORECASE
        )
        if specimens_match:
            specimens_str = specimens_match.group(1).strip()
            try:
                # Try to parse as number
                result["specimens_known"] = int(specimens_str.replace(',', '').split()[0])
            except (ValueError, IndexError):
                # Not a number, ignore
                pass
        
        # If no code but we have description, try to infer code
        if not result["rarity_code"] and result["rarity_description"]:
            desc_lower = result["rarity_description"].lower()
            code_map = {
                'common': 'C',
                'scarce': 'S',
                'rare': 'R1',
                'very rare': 'R3',
                'extremely rare': 'R4',
                'unique': 'R5',
            }
            for key, code in code_map.items():
                if key in desc_lower:
                    result["rarity_code"] = code
                    break
        
        return result
    
    def _parse_context_sections(self, content: str) -> Dict[str, str]:
        """
        Parse LLM response into named sections.
        
        Looks for ## SECTION_NAME headers and extracts content until next header.
        Returns dict mapping section keys to content.
        """
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split("\n"):
            # Check for section header (## SECTION_NAME)
            if line.startswith("## "):
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                
                # Extract section name
                header = line[3:].strip()
                # Normalize header to match our keys
                normalized = header.upper().replace(" ", "_").replace("&", "AND")
                if normalized in self.CONTEXT_SECTIONS:
                    current_section = normalized
                    current_content = []
                else:
                    current_section = None
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()
        
        return sections
    
    async def generate_context(
        self,
        coin_data: dict,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive multi-section numismatic analysis.
        
        Returns dict with:
            - sections: Dict mapping section names to content
            - raw_content: Full LLM response
            - confidence: Confidence score
            - cost_usd: API cost
            - model_used: Model that generated response
        """
        # Build structured prompt with clear sections
        prompt_parts = []
        
        # Identification header
        prompt_parts.append("=== COIN IDENTIFICATION ===")
        
        # Core identification
        if coin_data.get("issuer"):
            date_str = ""
            if coin_data.get("year_start"):
                y1 = coin_data["year_start"]
                y2 = coin_data.get("year_end", y1)
                if y1 < 0:
                    date_str = f" ({abs(y1)}-{abs(y2)} BC)" if y1 != y2 else f" ({abs(y1)} BC)"
                else:
                    date_str = f" (AD {y1}-{y2})" if y1 != y2 else f" (AD {y1})"
            prompt_parts.append(f"Issuer: {coin_data['issuer']}{date_str}")
        
        if coin_data.get("denomination"):
            denom = coin_data["denomination"]
            metal = coin_data.get("metal", "").upper()
            prompt_parts.append(f"Denomination: {metal} {denom}" if metal else f"Denomination: {denom}")
        
        if coin_data.get("mint"):
            prompt_parts.append(f"Mint: {coin_data['mint']}")
        
        if coin_data.get("category"):
            prompt_parts.append(f"Category: {coin_data['category']}")
        
        # References - clearly indicate what's known vs needed
        refs = coin_data.get("references", [])
        if isinstance(refs, list) and refs:
            prompt_parts.append(f"KNOWN REFERENCES (already cataloged): {'; '.join(refs)}")
            prompt_parts.append("NOTE: Verify and cite these references. If you find additional references (RIC, RSC, Cohen, Sear, BMC, Crawford, etc.), include them.")
        else:
            prompt_parts.append("KNOWN REFERENCES: None cataloged yet")
            prompt_parts.append("IMPORTANT: Please identify and cite all applicable catalog references (RIC, RSC, Cohen, Sear, BMC, Crawford, RPC, etc.)")
        
        # Obverse
        prompt_parts.append("\n=== OBVERSE ===")
        if coin_data.get("obverse_legend"):
            prompt_parts.append(f"Legend: {coin_data['obverse_legend']}")
        if coin_data.get("obverse_description"):
            prompt_parts.append(f"Description: {coin_data['obverse_description']}")
        
        # Reverse
        prompt_parts.append("\n=== REVERSE ===")
        if coin_data.get("reverse_legend"):
            prompt_parts.append(f"Legend: {coin_data['reverse_legend']}")
        if coin_data.get("reverse_description"):
            prompt_parts.append(f"Description: {coin_data['reverse_description']}")
        if coin_data.get("exergue"):
            prompt_parts.append(f"Exergue: {coin_data['exergue']}")
        
        # Physical
        prompt_parts.append("\n=== PHYSICAL ===")
        if coin_data.get("weight_g"):
            prompt_parts.append(f"Weight: {coin_data['weight_g']}g")
        if coin_data.get("diameter_mm"):
            prompt_parts.append(f"Diameter: {coin_data['diameter_mm']}mm")
        if coin_data.get("die_axis") is not None:
            prompt_parts.append(f"Die Axis: {coin_data['die_axis']}h")
        if coin_data.get("grade"):
            prompt_parts.append(f"Grade: {coin_data['grade']}")
        
        prompt = "\n".join(prompt_parts)
        
        result = await self.complete(
            capability=LLMCapability.CONTEXT_GENERATE,
            prompt=prompt,
        )
        
        # Parse sections from response
        sections = self._parse_context_sections(result.content)
        
        # Extract catalog citations from LLM response
        llm_citations = self._parse_citations(result.content)
        
        # Compare with existing references (if provided)
        existing_refs = coin_data.get("references", [])
        new_suggestions, matched_refs = self._compare_references(llm_citations, existing_refs)
        
        return {
            "sections": sections,
            "raw_content": result.content,
            "confidence": result.confidence,
            "cost_usd": result.cost_usd,
            "model_used": result.model_used,
            "cached": result.cached,
            "llm_citations": llm_citations,          # All citations found by LLM
            "suggested_references": new_suggestions,  # Citations NOT in existing DB refs
            "matched_references": matched_refs,       # Citations that matched existing refs
            "rarity_info": self._parse_rarity(result.content),  # Extracted rarity data
        }
    
    # -------------------------------------------------------------------------
    # P2 Capabilities (Advanced)
    # -------------------------------------------------------------------------
    
    async def assist_attribution(
        self,
        known_info: dict,
    ) -> "AttributionAssistResult":
        """
        Suggest attribution from partial coin information.
        
        Args:
            known_info: Dict with partial coin info (legend, weight, design)
        
        Returns:
            AttributionAssistResult with ranked suggestions
        """
        from src.domain.llm import AttributionAssistResult, AttributionSuggestion
        
        prompt = f"Suggest attribution based on:\n\n{json.dumps(known_info, indent=2)}"
        
        result = await self.complete(
            capability=LLMCapability.ATTRIBUTION_ASSIST,
            prompt=prompt,
            context=known_info,
        )
        
        # Parse JSON response
        try:
            parsed = json.loads(self._strip_markdown_json(result.content))
        except json.JSONDecodeError:
            parsed = {}
        
        # Parse suggestions
        suggestions = []
        for s in parsed.get("suggestions", []):
            suggestions.append(AttributionSuggestion(
                attribution=s.get("attribution", ""),
                reference=s.get("reference", ""),
                confidence=s.get("confidence", 0.5),
                reasoning=s.get("reasoning", []),
            ))
        
        return AttributionAssistResult(
            content=result.content,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
            model_used=result.model_used,
            cached=result.cached,
            reasoning=result.reasoning,
            suggestions=suggestions,
            questions_to_resolve=parsed.get("questions_to_resolve", []),
        )
    
    async def transcribe_legend(
        self,
        image_b64: str,
        hints: Optional[dict] = None,
    ) -> "LegendTranscribeResult":
        """
        OCR-like legend transcription from coin images.
        
        Uses vision model to read legend characters from images.
        Handles worn/uncertain portions with [...] notation.
        """
        from src.domain.llm import LegendTranscribeResult
        
        # Preprocess image if processor available
        if self.image_processor:
            try:
                image_bytes = self.image_processor.from_base64(image_b64)
                processed = self.image_processor.preprocess(image_bytes)
                image_b64 = self.image_processor.to_base64(processed, preprocess=False)
            except Exception as e:
                logger.warning(f"Image preprocessing failed: {e}")
        
        # Check vision cache
        if self.vision_cache:
            image_bytes = base64.b64decode(image_b64)
            cached = await self.vision_cache.get(
                image_bytes, 
                LLMCapability.LEGEND_TRANSCRIBE.value
            )
            if cached:
                parsed = cached["response"]
                return LegendTranscribeResult(
                    content=json.dumps(parsed),
                    confidence=parsed.get("confidence", 0.8),
                    cost_usd=0.0,
                    model_used=cached["model"],
                    cached=True,
                    reasoning=parsed.get("reasoning", []),
                    obverse_legend=parsed.get("obverse_legend"),
                    obverse_legend_expanded=parsed.get("obverse_legend_expanded"),
                    reverse_legend=parsed.get("reverse_legend"),
                    reverse_legend_expanded=parsed.get("reverse_legend_expanded"),
                    exergue=parsed.get("exergue"),
                    uncertain_portions=parsed.get("uncertain_portions", []),
                )
        
        hints_str = json.dumps(hints) if hints else "{}"
        prompt = f"Transcribe the legends from this coin image.\n\nHints: {hints_str}"
        
        result = await self.complete(
            capability=LLMCapability.LEGEND_TRANSCRIBE,
            prompt=prompt,
            image_b64=image_b64,
        )
        
        # Parse JSON response
        try:
            parsed = json.loads(self._strip_markdown_json(result.content))
        except json.JSONDecodeError:
            parsed = {}
        
        # Cache the result
        if self.vision_cache and not result.cached:
            image_bytes = base64.b64decode(image_b64)
            await self.vision_cache.set(
                image_bytes,
                LLMCapability.LEGEND_TRANSCRIBE.value,
                parsed,
                result.model_used,
                result.cost_usd,
            )
        
        return LegendTranscribeResult(
            content=result.content,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
            model_used=result.model_used,
            cached=result.cached,
            reasoning=result.reasoning,
            obverse_legend=parsed.get("obverse_legend"),
            obverse_legend_expanded=parsed.get("obverse_legend_expanded"),
            reverse_legend=parsed.get("reverse_legend"),
            reverse_legend_expanded=parsed.get("reverse_legend_expanded"),
            exergue=parsed.get("exergue"),
            uncertain_portions=parsed.get("uncertain_portions", []),
        )
    
    async def parse_catalog(
        self,
        reference: str,
    ) -> "CatalogParseResult":
        """
        Parse catalog reference string into components.
        
        Recognizes: RIC, RSC, RPC, Crawford, Sear, BMC, Cohen
        """
        from src.domain.llm import CatalogParseResult
        
        prompt = f"Parse this catalog reference: {reference}"
        
        result = await self.complete(
            capability=LLMCapability.CATALOG_PARSE,
            prompt=prompt,
            context={"reference": reference},
        )
        
        # Parse JSON response
        try:
            parsed = json.loads(self._strip_markdown_json(result.content))
        except json.JSONDecodeError:
            parsed = {"raw_reference": reference}
        
        return CatalogParseResult(
            content=result.content,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
            model_used=result.model_used,
            cached=result.cached,
            reasoning=result.reasoning,
            raw_reference=reference,
            catalog_system=parsed.get("catalog_system", ""),
            volume=parsed.get("volume"),
            number=parsed.get("number", ""),
            issuer=parsed.get("issuer"),
            mint=parsed.get("mint"),
            alternatives=parsed.get("alternatives", []),
        )
    
    async def observe_condition(
        self,
        image_b64: str,
        hints: Optional[dict] = None,
    ) -> "ConditionObservationsResult":
        """
        Describe wear patterns and condition (NOT grades).
        
        CRITICAL: Does NOT provide numeric grades (VF/EF/AU).
        Describes observable facts only.
        """
        from src.domain.llm import ConditionObservationsResult
        
        # Preprocess image if processor available
        if self.image_processor:
            try:
                image_bytes = self.image_processor.from_base64(image_b64)
                processed = self.image_processor.preprocess(image_bytes)
                image_b64 = self.image_processor.to_base64(processed, preprocess=False)
            except Exception as e:
                logger.warning(f"Image preprocessing failed: {e}")
        
        hints_str = json.dumps(hints) if hints else "{}"
        prompt = f"Describe the condition of this coin from the image.\nDo NOT provide grades - only observations.\n\nHints: {hints_str}"
        
        result = await self.complete(
            capability=LLMCapability.CONDITION_OBSERVATIONS,
            prompt=prompt,
            image_b64=image_b64,
        )
        
        # Parse JSON response
        try:
            parsed = json.loads(self._strip_markdown_json(result.content))
        except json.JSONDecodeError:
            parsed = {}
        
        # Post-processing: detect and warn about grade terminology
        output_text = json.dumps(parsed).upper()
        grade_terms = ["FINE", " VF ", " EF ", " AU ", " MS ", "VERY FINE", "EXTREMELY FINE", 
                       "ABOUT UNCIRCULATED", "MINT STATE", "F-VF", "VF-EF", "EF-AU"]
        for term in grade_terms:
            if term in output_text:
                logger.warning(f"Grade terminology detected in condition_observations output: {term}")
                # Add warning to parsed data
                if "concerns" not in parsed:
                    parsed["concerns"] = []
                parsed["concerns"].append(
                    "Warning: Output may contain grade terminology - please review"
                )
                break
        
        return ConditionObservationsResult(
            content=result.content,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
            model_used=result.model_used,
            cached=result.cached,
            reasoning=result.reasoning,
            wear_observations=parsed.get("wear_observations", ""),
            surface_notes=parsed.get("surface_notes", ""),
            strike_quality=parsed.get("strike_quality", ""),
            notable_features=parsed.get("notable_features", []),
            concerns=parsed.get("concerns", []),
            recommendation=parsed.get("recommendation", "Professional grading recommended for sale/insurance"),
        )
    
    # -------------------------------------------------------------------------
    # Admin methods
    # -------------------------------------------------------------------------
    
    def get_monthly_cost(self) -> float:
        """Get current month's total cost."""
        if self.cost_tracker:
            return self.cost_tracker.get_monthly_cost()
        return 0.0
    
    def get_active_profile(self) -> str:
        """Get current configuration profile."""
        return self.config.active_profile
    
    def is_capability_available(self, capability: LLMCapability) -> bool:
        """Check if a capability is available in current profile."""
        cap_cfg = self.config.get_capability(capability.value)
        if not cap_cfg:
            return False
        
        profile = self.config.active_profile
        profile_cfg = cap_cfg.profiles.get(profile, {})
        
        return bool(profile_cfg.get("primary"))
    
    def check_rate_limit(self, coin_id: int) -> Tuple[bool, int]:
        """
        Check rate limit for coin enrichment.
        
        Returns:
            Tuple of (is_allowed, seconds_until_retry)
        """
        return self.rate_limiter.check(f"coin:{coin_id}")
    
    def record_enrichment(self, coin_id: int):
        """Record an enrichment for rate limiting."""
        self.rate_limiter.record(f"coin:{coin_id}")
