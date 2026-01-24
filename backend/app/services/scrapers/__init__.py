"""Auction scraper services for fetching lot data from various platforms."""

from .base import AuctionScraperBase, LotData, ScrapeResult
from .orchestrator import AuctionOrchestrator

__all__ = [
    "AuctionScraperBase",
    "LotData",
    "ScrapeResult",
    "AuctionOrchestrator",
]
