"""
Base LLM Client - The Core Engine.

Handles configuration, API calls, caching, cost tracking, and rate limiting.
De-coupled from specific capabilities.
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
from typing import Any, Dict, List, Optional, Tuple

import yaml

try:
    import litellm
    from litellm import acompletion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    acompletion = None

from src.domain.llm import (
    LLMCapability,
    LLMError,
    LLMProviderUnavailable,
    LLMRateLimitExceeded,
    LLMBudgetExceeded,
    LLMCapabilityNotAvailable,
)

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
        # Prefer path relative to project root
        root_dir = Path(os.getcwd())
        paths_to_try = [
            self.config_path,
            root_dir / "config/llm_config.yaml",
            root_dir / "backend/config/llm_config.yaml",
            Path(__file__).resolve().parent.parent.parent.parent.parent / "config" / "llm_config.yaml"
        ]
        
        for path in paths_to_try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    content = self._expand_env_vars(content)
                    self._config = yaml.safe_load(content)
                logger.info("Loaded LLM config from %s", path)
                break
        else:
            logger.warning("LLM config not found, using defaults")
            self._config = self._default_config()
        
        self._parse_models()
        self._parse_capabilities()
    
    def _expand_env_vars(self, content: str) -> str:
        def replace(match):
            var = match.group(1)
            if ":-" in var:
                var_name, default = var.split(":-", 1)
                return os.environ.get(var_name, default)
            return os.environ.get(var, "")
        return re.sub(r'\$\{([^}]+)\}', replace, content)
    
    def _default_config(self) -> Dict:
        return {
            "settings": {
                "active_profile": "development",
                "default_timeout": 60,
                "max_retries": 3,
                "track_costs": True,
                "monthly_budget_usd": 5.0,
                "cache_enabled": True,
                "rate_limit": {"enrichments_per_coin": 3, "window_minutes": 5},
            },
            "providers": {},
            "models": {},
            "capabilities": {},
        }
    
    def _parse_models(self):
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
    
    def get_model_for_capability(self, capability: str, profile: Optional[str] = None) -> Tuple[Optional[ModelConfig], List[str]]:
        profile = profile or self.active_profile
        cap_cfg = self._capabilities.get(capability)
        if not cap_cfg:
            return None, []
        profile_cfg = cap_cfg.profiles.get(profile, {})
        primary_name = profile_cfg.get("primary")
        fallback_names = profile_cfg.get("fallback", [])
        primary = self._models.get(primary_name) if primary_name else None
        return primary, fallback_names


# =============================================================================
# CACHE & COST & RATE LIMITS
# =============================================================================

class LLMCache:
    """SQLite-based LLM response cache."""
    def __init__(self, db_path: str = "data/llm_cache.sqlite"):
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
        conn.execute("CREATE TABLE IF NOT EXISTS llm_cache (cache_key TEXT PRIMARY KEY, response TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT NOT NULL, capability TEXT, model TEXT, cost_usd REAL DEFAULT 0.0)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON llm_cache(expires_at)")
        conn.commit()
    
    def _hash_key(self, capability: str, prompt: str, context: Optional[Dict] = None) -> str:
        key_data = {"capability": capability, "prompt": prompt, "context": context or {}}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]
    
    async def get(self, capability: str, prompt: str, context: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        cache_key = self._hash_key(capability, prompt, context)
        conn = self._get_conn()
        cursor = conn.execute("SELECT response, created_at, model, cost_usd FROM llm_cache WHERE cache_key = ? AND expires_at > datetime('now')", (cache_key,))
        row = cursor.fetchone()
        if row:
            return {"response": json.loads(row[0]), "created_at": row[1], "model": row[2], "cost_usd": row[3]}
        return None
    
    async def set(self, capability: str, prompt: str, response: Any, model: str, cost_usd: float, ttl_hours: int = 168, context: Optional[Dict] = None):
        cache_key = self._hash_key(capability, prompt, context)
        expires = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        conn = self._get_conn()
        conn.execute("INSERT OR REPLACE INTO llm_cache (cache_key, response, created_at, expires_at, capability, model, cost_usd) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (cache_key, json.dumps(response), datetime.now(timezone.utc).isoformat(), expires.isoformat(), capability, model, cost_usd))
        conn.commit()

class CostTracker:
    """Tracks LLM usage costs."""
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
        conn.execute("CREATE TABLE IF NOT EXISTS llm_costs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, model TEXT NOT NULL, capability TEXT NOT NULL, input_tokens INTEGER DEFAULT 0, output_tokens INTEGER DEFAULT 0, cost_usd REAL NOT NULL, cached INTEGER DEFAULT 0, request_id TEXT)")
        conn.commit()
    
    async def record(self, model: str, capability: str, input_tokens: int, output_tokens: int, cost_usd: float, cached: bool = False, request_id: Optional[str] = None):
        conn = self._get_conn()
        conn.execute("INSERT INTO llm_costs (timestamp, model, capability, input_tokens, output_tokens, cost_usd, cached, request_id) VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?)",
                     (model, capability, input_tokens, output_tokens, cost_usd, 1 if cached else 0, request_id))
        conn.commit()
    
    def get_monthly_cost(self) -> float:
        conn = self._get_conn()
        cursor = conn.execute("SELECT COALESCE(SUM(cost_usd), 0.0) FROM llm_costs WHERE timestamp >= date('now', 'start of month')")
        return cursor.fetchone()[0]

    def get_cost_by_capability(self, days: int = 30) -> Dict[str, float]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT capability, SUM(cost_usd) FROM llm_costs WHERE timestamp >= date('now', ?)", (f"-{days} days",))
        return {row[0]: row[1] for row in cursor.fetchall()}

    def get_cost_by_model(self, days: int = 30) -> Dict[str, float]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT model, SUM(cost_usd) FROM llm_costs WHERE timestamp >= date('now', ?)", (f"-{days} days",))
        return {row[0]: row[1] for row in cursor.fetchall()}

class RateLimiter:
    """In-memory rate limiter."""
    def __init__(self, max_per_window: int = 3, window_minutes: int = 5):
        self.max_per_window = max_per_window
        self.window_minutes = window_minutes
        self._requests: Dict[str, List[datetime]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def check_limit(self, key: str) -> bool:
        with self._lock:
            now = datetime.now()
            window_start = now - timedelta(minutes=self.window_minutes)
            self._requests[key] = [ts for ts in self._requests[key] if ts > window_start]
            if len(self._requests[key]) >= self.max_per_window:
                return False
            self._requests[key].append(now)
            return True

class PromptLoader:
    """Loads prompt templates."""
    DEFAULT_PATH = Path("config/prompts/capabilities.yaml")
    def __init__(self, prompts_path: Optional[Path] = None):
        self.prompts_path = prompts_path or self.DEFAULT_PATH
        self._prompts: Dict[str, Dict[str, Any]] = {}
        self._load()
    
    def _load(self):
        root_dir = Path(os.getcwd())
        paths_to_try = [self.prompts_path, root_dir / "config/prompts/capabilities.yaml", root_dir / "backend/config/prompts/capabilities.yaml"]
        for path in paths_to_try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._prompts = yaml.safe_load(f) or {}
                return
    
    def get_system_prompt(self, capability: str) -> str:
        return self._prompts.get(capability, {}).get("system", "You are a helpful assistant.")
    
    def get_user_template(self, capability: str) -> str:
        return self._prompts.get(capability, {}).get("user_template", "{input}")


# =============================================================================
# BASE CLIENT
# =============================================================================

class BaseLLMClient:
    """
    Core LLM Engine.
    Handles Model Routing, API Calls, Caching, Cost, and Rate Limiting.
    """
    def __init__(self, config_path: Optional[Path] = None):
        if not LITELLM_AVAILABLE:
            logger.warning("LiteLLM not installed. LLM features unavailable.")
        
        self.config = ConfigLoader(config_path)
        self.cache = LLMCache() if self.config.settings.get("cache_enabled", True) else None
        self.cost_tracker = CostTracker() if self.config.settings.get("track_costs", True) else None
        self.prompts = PromptLoader()
        
        rate_limit_cfg = self.config.rate_limit_config
        self.rate_limiter = RateLimiter(
            max_per_window=rate_limit_cfg.get("enrichments_per_coin", 3),
            window_minutes=rate_limit_cfg.get("window_minutes", 5)
        )

    def is_capability_available(self, capability: LLMCapability) -> bool:
        """Check if capability is configured and provider is available."""
        if not LITELLM_AVAILABLE:
            return False
        model, _ = self.config.get_model_for_capability(capability.value)
        return model is not None

    @staticmethod
    def _strip_markdown_json(content: str) -> str:
        """Strip Markdown code blocks from JSON string."""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()

    async def execute_prompt(
        self,
        capability: LLMCapability,
        user_input: str,
        system_override: Optional[str] = None,
        image_data: Optional[str] = None,
        context: Optional[Dict] = None,
        rate_limit_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute an LLM prompt with full infrastructure support.
        
        Args:
            capability: The LLM capability being used
            user_input: The main input text (will be formatted into user_template)
            system_override: Optional override for system prompt
            image_data: Base64 image data (if vision required)
            context: Additional context for caching/logging
            rate_limit_key: Key for rate limiting (e.g. coin_id)
            
        Returns:
            Dict containing 'content' (str/json), 'model', 'cost', 'cached', 'usage'
        """
        if not LITELLM_AVAILABLE:
            raise LLMProviderUnavailable("LiteLLM library not installed")

        # 1. Rate Limit Check
        if rate_limit_key and not self.rate_limiter.check_limit(rate_limit_key):
            raise LLMRateLimitExceeded(
                f"Rate limit exceeded for {rate_limit_key}",
                retry_after=self.rate_limiter.window_minutes * 60
            )

        # 2. Budget Check
        if self.cost_tracker and self.cost_tracker.get_monthly_cost() >= self.config.monthly_budget:
            raise LLMBudgetExceeded("Monthly LLM budget exceeded")

        # 3. Model Selection
        cap_name = capability.value
        cap_cfg = self.config.get_capability(cap_name)
        primary_model, fallbacks = self.config.get_model_for_capability(cap_name)
        if not primary_model:
            raise LLMCapabilityNotAvailable(f"No model configured for {cap_name}")

        # 4. Prompt Construction
        system_prompt = system_override or self.prompts.get_system_prompt(cap_name)
        user_template = self.prompts.get_user_template(cap_name)
        full_user_message = user_template.format(input=user_input)

        # 5. Cache Check
        cache_key_prompt = f"{system_prompt}\n{full_user_message}\nHasImage={bool(image_data)}"
        if self.cache:
            cached = await self.cache.get(cap_name, cache_key_prompt, context)
            if cached:
                return {
                    "content": cached["response"],
                    "model": cached["model"],
                    "cost": 0.0,
                    "cached": True,
                    "usage": {"input_tokens": 0, "output_tokens": 0}
                }

        # 6. Execute with Fallback
        models_to_try = [primary_model] + [self.config.get_model(name) for name in fallbacks if self.config.get_model(name)]
        last_error = None

        for model_cfg in models_to_try:
            try:
                logger.info(f"Invoking {model_cfg.model_id} for {cap_name}")
                messages = [{"role": "system", "content": system_prompt}]
                
                if image_data and model_cfg.supports_vision:
                    content_block = [
                        {"type": "text", "text": full_user_message},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]
                    messages.append({"role": "user", "content": content_block})
                else:
                    messages.append({"role": "user", "content": full_user_message})

                # Call API
                json_mode = cap_cfg.requires_json and model_cfg.supports_json_mode
                
                response = await acompletion(
                    model=model_cfg.model_id,
                    messages=messages,
                    response_format={"type": "json_object"} if json_mode else None,
                    max_tokens=model_cfg.max_tokens,
                    temperature=0.1, # Deterministic usually better for data extraction
                )
                
                content = response.choices[0].message.content
                usage = response.usage
                
                # Parse JSON if expected
                parsed_content = content
                if json_mode:
                    try:
                        cleaned_content = self._strip_markdown_json(content)
                        parsed_content = json.loads(cleaned_content)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse JSON from model response")
                        # If strict JSON was required, this might be a failure, but we return raw and let caller handle
                
                # Calculate Cost
                cost = litellm.completion_cost(completion_response=response)
                
                # Track Cost
                if self.cost_tracker:
                    await self.cost_tracker.record(
                        model=model_cfg.name,
                        capability=cap_name,
                        input_tokens=usage.prompt_tokens,
                        output_tokens=usage.completion_tokens,
                        cost_usd=cost,
                        cached=False
                    )
                
                # Cache Result
                if self.cache:
                    await self.cache.set(
                        capability=cap_name,
                        prompt=cache_key_prompt,
                        response=parsed_content,
                        model=model_cfg.name,
                        cost_usd=cost,
                        context=context
                    )
                
                return {
                    "content": parsed_content,
                    "model": model_cfg.name,
                    "cost": cost,
                    "cached": False,
                    "usage": {"input_tokens": usage.prompt_tokens, "output_tokens": usage.completion_tokens}
                }

            except Exception as e:
                logger.warning(f"Model {model_cfg.name} failed: {e}")
                last_error = e
                continue
        
        raise LLMError(f"All models failed for {cap_name}. Last error: {last_error}")
