from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from src.infrastructure.web.routers import v2, audit_v2, scrape_v2, vocab, series, llm, provenance, die_study, stats
from src.infrastructure.persistence.database import init_db
from src.infrastructure.config import get_settings

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="CoinStack V2 API")
    
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
    app.include_router(vocab.router)          # V3 vocab API (/api/v2/vocab)
    app.include_router(vocab.legacy_router)   # Legacy vocab API (/api/vocab)
    app.include_router(series.router)
    app.include_router(llm.router)            # LLM capabilities API (/api/v2/llm)
    app.include_router(provenance.router, prefix="/api/v2")  # Provenance API
    app.include_router(die_study.router, prefix="/api/v2")   # Die Study API
    app.include_router(stats.router)                         # Stats/Dashboard API
    
    return app

app = create_app()