from typing import List
from src.domain.coin import Coin
from src.domain.audit import IAuditStrategy, ExternalAuctionData, Discrepancy

class GradeStrategy(IAuditStrategy):
    def audit(self, coin: Coin, auction_data: ExternalAuctionData) -> List[Discrepancy]:
        discrepancies = []
        
        # Skip if external data is missing
        if not auction_data.grade:
            return []

        # Simple string match for now. 
        # In future, we could normalize "Ch XF" == "Choice XF"
        if coin.grading.grade != auction_data.grade:
            discrepancies.append(Discrepancy(
                field="grade",
                current_value=coin.grading.grade,
                auction_value=auction_data.grade,
                confidence=1.0,
                source=auction_data.source
            ))
            
        return discrepancies
