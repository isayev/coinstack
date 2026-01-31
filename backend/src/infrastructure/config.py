"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = "sqlite:///./coinstack_v2.db"
    DATABASE_ECHO: bool = False
    
    # API
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000", 
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]
    UPLOAD_DIR: str = "./uploads"
    
    # LLM
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "claude-sonnet-4-20250514"
    LLM_RATE_LIMIT_PER_MINUTE: int = 10
    
    # Scraper settings
    SCRAPER_TIMEOUT: float = 30.0  # HTTP request timeout in seconds
    SCRAPER_RATE_LIMIT: float = 2.0  # Default seconds between requests
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Per-source rate limits (seconds between requests)
    # Different auction houses have different rate limit tolerance
    SCRAPER_RATE_LIMITS: dict[str, float] = {
        "heritage": 2.0,  # Heritage Auctions - moderate rate
        "cng": 3.0,       # CNG (Classical Numismatic Group) - conservative rate
        "ebay": 5.0,      # eBay - very conservative (anti-bot detection)
        "biddr": 2.0,     # Biddr - moderate rate
        "agora": 2.0,     # Agora Auctions - moderate rate
        "default": 2.0    # Fallback for unknown sources
    }

    # Catalog scrapers (no-API catalogs like RPC Online)
    CATALOG_SCRAPER_RPC_ENABLED: bool = False  # Set True to fetch type data from RPC HTML
    CATALOG_SCRAPER_RPC_RATE_LIMIT_SEC: float = 10.0  # Seconds between RPC requests
    CATALOG_SCRAPER_USER_AGENT: str = "CoinStack/1.0 (Numismatic collection manager; catalog lookup)"
    
    # Logging
    LOG_LEVEL: str = "INFO"

    # Observability
    SLOW_QUERY_THRESHOLD_SECONDS: float = 0.1
    SLOW_REQUEST_THRESHOLD_MS: float = 1000.0
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # Ignore extra env vars if any
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
