from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from src.infrastructure.web.routers import v2, audit_v2, scrape_v2, vocab, series
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
    # We mount both standard locations to cover V1 and V2 paths
    images_dir = Path("data/coin_images")
    images_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/api/images", StaticFiles(directory=str(images_dir)), name="images")
    
    app.include_router(v2.router)
    app.include_router(audit_v2.router)
    app.include_router(scrape_v2.router)
    app.include_router(vocab.router)
    app.include_router(series.router)
    
    return app

app = create_app()