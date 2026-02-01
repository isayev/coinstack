from pathlib import Path
from dotenv import load_dotenv
import sys
import asyncio

# Fix for Windows + Playwright + FastAPI async subprocess issue
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load .env file from backend directory FIRST, before any other imports
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.infrastructure.web.routers import v2, audit_v2, scrape_v2, vocab, series, llm, provenance, stats, review, import_v2, catalog, catalog_v2, grading_history, rarity_assessment, concordance, external_links, llm_enrichment, census_snapshot, market, valuation, wishlist, collections, dies, die_links, die_pairings, die_varieties, attribution_hypotheses  # die_study (Legacy) removed in favor of Phase 1.5d
from src.infrastructure.persistence.database import init_db
from src.infrastructure.config import get_settings
from src.infrastructure.logging_config import configure_logging
from src.infrastructure.web.middleware import ObservabilityMiddleware

def create_app() -> FastAPI:
    # Note: Windows event loop policy already set at module level (lines 7-8)
    settings = get_settings()

    # Configure centralized logging with request ID tracking
    configure_logging(
        level=getattr(settings, 'LOG_LEVEL', 'INFO'),
        include_request_id=True,
    )

    app = FastAPI(title="CoinStack V2 API")

    # Add unified observability middleware (request ID, timing, slow request detection)
    app.add_middleware(
        ObservabilityMiddleware,
        slow_threshold_ms=getattr(settings, 'SLOW_REQUEST_THRESHOLD_MS', 1000.0)
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_db()
    
    # Mount static files for images
    # Use absolute path to ensure images are found regardless of CWD
    images_dir = Path(__file__).parent.parent.parent.parent / "data" / "coin_images"
    images_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")
    
    app.include_router(v2.router)
    app.include_router(audit_v2.router)
    app.include_router(scrape_v2.router)
    app.include_router(import_v2.router)       # Import API (/api/v2/import)
    app.include_router(vocab.router)          # V3 vocab API (/api/v2/vocab)
    app.include_router(vocab.legacy_router)   # Legacy vocab API (/api/vocab)
    app.include_router(series.router)
    app.include_router(llm.router)            # LLM capabilities API (/api/v2/llm)
    app.include_router(review.router)         # Review API (/api/v2/review)
    app.include_router(provenance.router, prefix="/api/v2")  # Provenance API
    # app.include_router(die_study.router, prefix="/api/v2")   # Die Study API (Legacy) - Replaced by Phase 1.5d
    app.include_router(dies.router)                          # Dies Catalog API (Phase 1.5d)
    app.include_router(die_links.router)                     # Die Links API (Phase 1.5d)
    app.include_router(die_pairings.router)                  # Die Pairings API (Phase 1.5d)
    app.include_router(die_varieties.router)                 # Die Varieties API (Phase 1.5d)
    app.include_router(attribution_hypotheses.router)        # Attribution Hypotheses API (Phase 2)
    app.include_router(stats.router)                         # Stats/Dashboard API
    app.include_router(catalog.router)                       # Catalog API (/api/catalog)
    app.include_router(catalog_v2.router)                    # Catalog parse/systems (/api/v2/catalog)
    app.include_router(grading_history.router)               # Grading History API (Schema V3 Phase 2)
    app.include_router(rarity_assessment.router)             # Rarity Assessment API (Schema V3 Phase 2)
    app.include_router(census_snapshot.router)               # Census Snapshot API (Schema V3 Phase 2)
    app.include_router(concordance.router)                   # Reference Concordance API (Schema V3 Phase 3)
    app.include_router(external_links.router)                # External Catalog Links API (Schema V3 Phase 3)
    app.include_router(llm_enrichment.router)                # LLM Enrichment API (Schema V3 Phase 4)
    app.include_router(market.router)                        # Market Prices API (Schema V3 Phase 5)
    app.include_router(valuation.router)                     # Coin Valuations API (Schema V3 Phase 5)
    app.include_router(wishlist.router)                      # Wishlist API (Schema V3 Phase 5)
    app.include_router(collections.router)                   # Collections API (Schema V3 Phase 6)

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint for monitoring."""
        return {"status": "healthy", "version": "2.0"}

    return app

app = create_app()