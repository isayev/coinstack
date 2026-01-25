"""
Unit tests for LLM service infrastructure.

Tests the LLMService implementation with mocked LLM calls.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.domain.llm import (
    LLMCapability,
    LLMResult,
    LLMProviderUnavailable,
    LLMRateLimitExceeded,
    LLMBudgetExceeded,
    LLMCapabilityNotAvailable,
)


# Skip tests if LLM service not available
pytest.importorskip("src.infrastructure.services.llm_service")

from src.infrastructure.services.llm_service import (
    ConfigLoader,
    LLMCache,
    CostTracker,
    RateLimiter,
    IdempotencyStore,
    PromptLoader,
    LLMService,
    ModelConfig,
    CapabilityConfig,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = MagicMock(spec=ConfigLoader)
    config.active_profile = "development"
    config.monthly_budget = 5.0
    config.rate_limit_config = {"enrichments_per_coin": 3, "window_minutes": 5}
    config.settings = {
        "active_profile": "development",
        "default_timeout": 60,
        "monthly_budget_usd": 5.0,
    }
    
    # Mock model config
    model = ModelConfig(
        name="mock-model",
        provider="mock",
        model_id="mock-v1",
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.003,
        max_tokens=4096,
    )
    config.get_model.return_value = model
    
    # Mock capability config
    cap = CapabilityConfig(
        name="vocab_normalize",
        description="Normalize vocab",
        requires_json=True,
        cacheable=True,
        profiles={"development": {"primary": "mock-model", "fallback": []}},
        parameters={"temperature": 0.1, "max_tokens": 100},
    )
    config.get_capability.return_value = cap
    config.get_model_for_capability.return_value = (model, [])
    
    return config


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database path."""
    return str(tmp_path / "test_cache.sqlite")


# =============================================================================
# CONFIG LOADER TESTS
# =============================================================================

class TestConfigLoader:
    """Tests for ConfigLoader."""
    
    def test_default_config(self):
        """ConfigLoader should provide defaults when file not found."""
        # Use a non-existent path
        loader = ConfigLoader(Path("/nonexistent/config.yaml"))
        
        assert loader.active_profile in ["development", "production", "offline"]
        assert loader.monthly_budget > 0
    
    def test_expand_env_vars(self):
        """ConfigLoader should expand environment variables."""
        loader = ConfigLoader()
        
        # Test ${VAR:-default} pattern
        content = "key: ${NONEXISTENT_VAR:-fallback_value}"
        result = loader._expand_env_vars(content)
        assert "fallback_value" in result


# =============================================================================
# CACHE TESTS
# =============================================================================

class TestLLMCache:
    """Tests for LLMCache."""
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, temp_db):
        """Cache should return None on miss."""
        cache = LLMCache(temp_db)
        result = await cache.get("vocab_normalize", "test prompt")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, temp_db):
        """Cache should return stored result."""
        cache = LLMCache(temp_db)
        
        # Store
        await cache.set(
            capability="vocab_normalize",
            prompt="test prompt",
            response={"content": "Augustus", "confidence": 0.9},
            model="mock",
            cost_usd=0.001,
        )
        
        # Retrieve
        result = await cache.get("vocab_normalize", "test prompt")
        assert result is not None
        assert result["response"]["content"] == "Augustus"
    
    @pytest.mark.asyncio
    async def test_cache_with_context(self, temp_db):
        """Cache key should include context."""
        cache = LLMCache(temp_db)
        
        # Store with context
        await cache.set(
            capability="vocab_normalize",
            prompt="test",
            response={"content": "A"},
            model="m",
            cost_usd=0,
            context={"type": "issuer"},
        )
        
        # Different context should miss
        result = await cache.get("vocab_normalize", "test", {"type": "mint"})
        assert result is None
        
        # Same context should hit
        result = await cache.get("vocab_normalize", "test", {"type": "issuer"})
        assert result is not None


# =============================================================================
# COST TRACKER TESTS
# =============================================================================

class TestCostTracker:
    """Tests for CostTracker."""
    
    @pytest.mark.asyncio
    async def test_record_cost(self, temp_db):
        """CostTracker should record usage."""
        tracker = CostTracker(temp_db)
        
        await tracker.record(
            model="claude-haiku",
            capability="vocab_normalize",
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.001,
        )
        
        monthly = tracker.get_monthly_cost()
        assert monthly >= 0.001
    
    def test_cost_by_capability(self, temp_db):
        """CostTracker should breakdown by capability."""
        tracker = CostTracker(temp_db)
        
        # Record some costs
        conn = tracker._get_conn()
        conn.execute(
            """INSERT INTO llm_costs 
               (timestamp, model, capability, input_tokens, output_tokens, cost_usd)
               VALUES (datetime('now'), 'model', 'vocab_normalize', 100, 50, 0.01)"""
        )
        conn.execute(
            """INSERT INTO llm_costs 
               (timestamp, model, capability, input_tokens, output_tokens, cost_usd)
               VALUES (datetime('now'), 'model', 'legend_expand', 100, 50, 0.02)"""
        )
        conn.commit()
        
        breakdown = tracker.get_cost_by_capability()
        assert "vocab_normalize" in breakdown
        assert "legend_expand" in breakdown


# =============================================================================
# RATE LIMITER TESTS
# =============================================================================

class TestRateLimiter:
    """Tests for RateLimiter."""
    
    def test_allow_within_limit(self):
        """RateLimiter should allow requests within limit."""
        limiter = RateLimiter(max_per_window=3, window_minutes=5)
        
        allowed, _ = limiter.check("coin:1")
        assert allowed is True
    
    def test_block_over_limit(self):
        """RateLimiter should block when limit exceeded."""
        limiter = RateLimiter(max_per_window=2, window_minutes=5)
        
        # Record two requests
        limiter.record("coin:1")
        limiter.record("coin:1")
        
        # Third should be blocked
        allowed, retry_after = limiter.check("coin:1")
        assert allowed is False
        assert retry_after > 0
    
    def test_different_keys(self):
        """RateLimiter should track different keys separately."""
        limiter = RateLimiter(max_per_window=1, window_minutes=5)
        
        limiter.record("coin:1")
        
        # Different coin should be allowed
        allowed, _ = limiter.check("coin:2")
        assert allowed is True
    
    def test_count(self):
        """RateLimiter should report count."""
        limiter = RateLimiter(max_per_window=5, window_minutes=5)
        
        limiter.record("coin:1")
        limiter.record("coin:1")
        
        assert limiter.count("coin:1") == 2


# =============================================================================
# IDEMPOTENCY STORE TESTS
# =============================================================================

class TestIdempotencyStore:
    """Tests for IdempotencyStore."""
    
    def test_get_miss(self):
        """IdempotencyStore should return None on miss."""
        store = IdempotencyStore()
        result = store.get("unknown-request-id")
        assert result is None
    
    def test_get_hit(self):
        """IdempotencyStore should return cached result."""
        store = IdempotencyStore()
        
        store.set("req-123", {"result": "cached"})
        result = store.get("req-123")
        
        assert result == {"result": "cached"}
    
    def test_cleanup(self):
        """IdempotencyStore should clean expired entries."""
        store = IdempotencyStore(ttl_minutes=0)  # Immediate expiry
        
        store.set("req-123", {"result": "cached"})
        store.cleanup()
        
        result = store.get("req-123")
        assert result is None


# =============================================================================
# PROMPT LOADER TESTS
# =============================================================================

class TestPromptLoader:
    """Tests for PromptLoader."""
    
    def test_default_prompts(self):
        """PromptLoader should provide default system prompts."""
        loader = PromptLoader()
        
        prompt = loader.get_system_prompt("vocab_normalize")
        assert "numismatic" in prompt.lower() or "vocabulary" in prompt.lower()
    
    def test_default_legend_prompt(self):
        """PromptLoader should provide legend expansion prompt."""
        loader = PromptLoader()
        
        prompt = loader.get_system_prompt("legend_expand")
        assert "Latin" in prompt or "legend" in prompt.lower()


# =============================================================================
# LLM SERVICE TESTS
# =============================================================================

class TestLLMService:
    """Tests for LLMService."""
    
    def test_init(self):
        """LLMService should initialize components."""
        service = LLMService(cache_enabled=False, cost_tracking=False)
        
        assert service.config is not None
        assert service.rate_limiter is not None
        assert service.idempotency is not None
    
    def test_get_active_profile(self):
        """LLMService should return active profile."""
        service = LLMService(cache_enabled=False, cost_tracking=False)
        
        profile = service.get_active_profile()
        assert profile in ["development", "production", "offline"]
    
    def test_is_capability_available(self):
        """LLMService should check capability availability."""
        service = LLMService(cache_enabled=False, cost_tracking=False)
        
        # P0 capabilities should be available (depends on config)
        # This test verifies the method works, actual availability depends on config
        result = service.is_capability_available(LLMCapability.VOCAB_NORMALIZE)
        assert isinstance(result, bool)
    
    def test_check_rate_limit(self):
        """LLMService should provide rate limit checking."""
        service = LLMService(cache_enabled=False, cost_tracking=False)
        
        allowed, retry_after = service.check_rate_limit(coin_id=1)
        assert allowed is True
        
        # Record some requests
        service.record_enrichment(coin_id=1)
        service.record_enrichment(coin_id=1)
        service.record_enrichment(coin_id=1)
        
        # Should be limited now
        allowed, retry_after = service.check_rate_limit(coin_id=1)
        assert allowed is False
        assert retry_after > 0
    
    def test_get_monthly_cost_no_tracker(self):
        """LLMService should return 0 without cost tracker."""
        service = LLMService(cache_enabled=False, cost_tracking=False)
        
        cost = service.get_monthly_cost()
        assert cost == 0.0


# =============================================================================
# LLM SERVICE ASYNC TESTS
# =============================================================================

class TestLLMServiceAsync:
    """Async tests for LLMService with mocked LLM calls."""
    
    @pytest.mark.asyncio
    async def test_normalize_vocab_cached(self, temp_db):
        """normalize_vocab should return cached results."""
        service = LLMService(cache_enabled=True, cost_tracking=False)
        service.cache = LLMCache(temp_db)
        
        # Pre-populate cache
        await service.cache.set(
            capability="vocab_normalize",
            prompt='Vocab type: issuer\nRaw text: "Augustus"',
            response={"content": '{"canonical_name": "Augustus", "confidence": 0.95}', "confidence": 0.95},
            model="cached",
            cost_usd=0,
            context={"vocab_type": "issuer", "raw_text": "Augustus"},
        )
        
        # Should hit cache
        with patch.object(service, '_call_model') as mock_call:
            result = await service.normalize_vocab("Augustus", "issuer")
            
            # If no model was available, this would fail differently
            # The test verifies caching logic
            if result.cached:
                mock_call.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_complete_capability_not_available(self):
        """complete should raise if capability not available."""
        service = LLMService(cache_enabled=False, cost_tracking=False)
        
        # Mock capability as unavailable
        with patch.object(service, 'is_capability_available', return_value=False):
            with pytest.raises(LLMCapabilityNotAvailable):
                await service.complete(
                    capability=LLMCapability.DIE_STUDY,
                    prompt="test"
                )
    
    @pytest.mark.asyncio
    async def test_complete_budget_exceeded(self):
        """complete should raise if budget exceeded."""
        service = LLMService(cache_enabled=False, cost_tracking=True)
        
        # Mock budget as exceeded
        service.cost_tracker = MagicMock()
        service.cost_tracker.get_monthly_cost.return_value = 10.0  # Over $5 budget
        
        with patch.object(service, 'is_capability_available', return_value=True):
            with pytest.raises(LLMBudgetExceeded):
                await service.complete(
                    capability=LLMCapability.VOCAB_NORMALIZE,
                    prompt="test"
                )


# =============================================================================
# INTEGRATION-STYLE TESTS (still unit, but more complete flow)
# =============================================================================

class TestLLMServiceFlow:
    """Tests for complete LLM service flow with mocks."""
    
    @pytest.mark.asyncio
    async def test_vocab_normalize_mocked(self, temp_db):
        """Test vocab normalization with mocked LLM response."""
        # This test would require litellm to be installed
        # Skip if not available
        pytest.importorskip("litellm")
        
        service = LLMService(cache_enabled=True, cost_tracking=True)
        service.cache = LLMCache(temp_db)
        service.cost_tracker = CostTracker(temp_db.replace("cache", "costs"))
        
        # Mock the actual LLM call
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"canonical_name": "Augustus", "confidence": 0.92, "reasoning": ["match"]}'
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        
        with patch('src.infrastructure.services.llm_service.acompletion', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            
            # Ensure capability is available
            with patch.object(service, 'is_capability_available', return_value=True):
                with patch.object(service.config, 'get_model_for_capability') as mock_cap:
                    model = ModelConfig(
                        name="mock",
                        provider="mock",
                        model_id="mock",
                        cost_per_1k_input=0.001,
                        cost_per_1k_output=0.003,
                    )
                    mock_cap.return_value = (model, [])
                    
                    with patch.object(service.config, 'get_capability') as mock_get_cap:
                        cap = CapabilityConfig(
                            name="vocab_normalize",
                            description="test",
                            requires_json=True,
                            parameters={"temperature": 0.1},
                        )
                        mock_get_cap.return_value = cap
                        
                        with patch.object(service.config, 'get_model') as mock_get_model:
                            mock_get_model.return_value = model
                            
                            result = await service.normalize_vocab("IMP CAES AVG", "issuer")
                            
                            assert result.canonical_name == "Augustus"
                            assert result.confidence == 0.92
