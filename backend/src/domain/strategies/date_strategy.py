from typing import List
from src.domain.coin import Coin
from src.domain.audit import IAuditStrategy, ExternalAuctionData, Discrepancy

class DateStrategy(IAuditStrategy):
    def audit(self, coin: Coin, auction_data: ExternalAuctionData) -> List[Discrepancy]:
        discrepancies = []
        
        # Check Start Year
        if auction_data.year_start is not None and coin.attribution.year_start is not None:
            if auction_data.year_start != coin.attribution.year_start:
                discrepancies.append(Discrepancy(
                    field="year_start",
                    current_value=str(coin.attribution.year_start),
                    auction_value=str(auction_data.year_start),
                    confidence=0.9,
                    source=auction_data.source
                ))

        # Check End Year
        if auction_data.year_end is not None and coin.attribution.year_end is not None:
            if auction_data.year_end != coin.attribution.year_end:
                discrepancies.append(Discrepancy(
                    field="year_end",
                    current_value=str(coin.attribution.year_end),
                    auction_value=str(auction_data.year_end),
                    confidence=0.9,
                    source=auction_data.source
                ))

        return discrepancies
