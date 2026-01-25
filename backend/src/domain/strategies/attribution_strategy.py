from typing import List
from src.domain.coin import Coin
from src.domain.audit import IAuditStrategy, ExternalAuctionData, Discrepancy

class AttributionStrategy(IAuditStrategy):
    def audit(self, coin: Coin, auction_data: ExternalAuctionData) -> List[Discrepancy]:
        discrepancies = []
        
        # Check Issuer
        if auction_data.issuer and coin.attribution.issuer:
            # Simple check, could use fuzzy logic later
            if auction_data.issuer.lower() != coin.attribution.issuer.lower():
                discrepancies.append(Discrepancy(
                    field="issuer",
                    current_value=coin.attribution.issuer,
                    auction_value=auction_data.issuer,
                    confidence=0.9,
                    source=auction_data.source
                ))

        # Check Mint
        if auction_data.mint and coin.attribution.mint:
            if auction_data.mint.lower() != coin.attribution.mint.lower():
                discrepancies.append(Discrepancy(
                    field="mint",
                    current_value=coin.attribution.mint,
                    auction_value=auction_data.mint,
                    confidence=0.8,
                    source=auction_data.source
                ))

        return discrepancies
