import sys
import asyncio
import argparse
import logging
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.infrastructure.repositories.auction_data_repository import SqlAlchemyAuctionDataRepository
from src.application.commands.enrich_coin import EnrichCoinUseCase, EnrichCoinDTO
from src.infrastructure.web.routers.scrape_v2 import get_scraper_orchestrator
from src.infrastructure.persistence.orm import AuctionDataModel, CoinModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("enrichment_cli")

async def run_batch(batch_size=50):
    db = SessionLocal()
    try:
        # Find coins that need enrichment
        coins_with_url = db.query(CoinModel).filter(CoinModel.acquisition_url.isnot(None)).all()
        
        pending_coins = []
        for coin in coins_with_url:
            exists = db.query(AuctionDataModel).filter(AuctionDataModel.coin_id == coin.id).first()
            if not exists:
                pending_coins.append(coin)
                
        logger.info(f"Found {len(pending_coins)} coins pending enrichment.")
        
        to_process = pending_coins[:batch_size]
        logger.info(f"Processing batch of {len(to_process)}...")
        
        orchestrator = get_scraper_orchestrator()
        coin_repo = SqlAlchemyCoinRepository(db)
        auction_repo = SqlAlchemyAuctionDataRepository(db)
        use_case = EnrichCoinUseCase(coin_repo, auction_repo, orchestrator)
        
        success = 0
        failed = 0
        
        for coin in to_process:
            try:
                logger.info(f"Enriching Coin {coin.id} ({coin.acquisition_url})...")
                await use_case.execute(EnrichCoinDTO(coin_id=coin.id))
                success += 1
                logger.info("  Success")
            except Exception as e:
                logger.error(f"  Failed: {e}")
                failed += 1
                
        logger.info(f"Batch Complete. Success: {success}, Failed: {failed}")
        
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="CoinStack Enrichment CLI")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size")
    args = parser.parse_args()
    
    asyncio.run(run_batch(args.batch_size))

if __name__ == "__main__":
    main()
