"""FastAPI application entry point."""
# Stats dashboard support added
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.database import engine, Base
# Import models to register them with Base before create_all
from app.models import (
    Coin, Mint, CoinReference, ReferenceType, ReferenceMatchAttempt,
    ProvenanceEvent, CoinImage, CoinTag, Countermark, AuctionData, PriceHistory,
    DiscrepancyRecord, EnrichmentRecord, AuditRun, ImageAuctionSource,
    ImportRecord, FieldHistory
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("coinstack.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CoinStack API",
    description="Personal coin collection management API",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for serving coin images
images_dir = Path("data/coin_images")
images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/api/images", StaticFiles(directory=str(images_dir)), name="images")


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Global exception handler."""
    import traceback
    traceback.print_exc()
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "An error occurred. Check logs for details."},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": exc.errors()},
    )


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "database": "connected"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "CoinStack API", "version": "0.1.0"}


# Import routers
from app.routers.coins import router as coins_router
from app.routers.import_export import router as import_export_router
from app.routers.stats import router as stats_router
from app.routers.settings import router as settings_router
from app.routers.catalog import router as catalog_router
from app.routers.legend import router as legend_router
from app.routers.auctions import router as auctions_router
from app.routers.scrape import router as scrape_router
from app.routers.audit import router as audit_router
from app.routers.campaign import router as campaign_router

app.include_router(coins_router, prefix=settings.API_PREFIX)
app.include_router(import_export_router, prefix=settings.API_PREFIX)
app.include_router(stats_router, prefix=settings.API_PREFIX)
app.include_router(settings_router, prefix=settings.API_PREFIX)
app.include_router(catalog_router, prefix=settings.API_PREFIX)
app.include_router(legend_router, prefix=settings.API_PREFIX)
app.include_router(auctions_router, prefix=settings.API_PREFIX)
app.include_router(scrape_router, prefix=settings.API_PREFIX)
app.include_router(audit_router, prefix=settings.API_PREFIX)
app.include_router(campaign_router, prefix=settings.API_PREFIX)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
