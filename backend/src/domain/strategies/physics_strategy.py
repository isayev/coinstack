from typing import List
from decimal import Decimal
from src.domain.coin import Coin
from src.domain.audit import IAuditStrategy, ExternalAuctionData, Discrepancy

class PhysicsStrategy(IAuditStrategy):
    def __init__(self, weight_tolerance: Decimal = Decimal("0.05"), diameter_tolerance: Decimal = Decimal("0.5")):
        self.weight_tolerance = weight_tolerance
        self.diameter_tolerance = diameter_tolerance

    def audit(self, coin: Coin, auction_data: ExternalAuctionData) -> List[Discrepancy]:
        discrepancies = []
        
        # Check Weight
        if auction_data.weight_g is not None and coin.dimensions.weight_g is not None:
            diff = abs(coin.dimensions.weight_g - auction_data.weight_g)
            if diff > self.weight_tolerance:
                discrepancies.append(Discrepancy(
                    field="weight_g",
                    current_value=str(coin.dimensions.weight_g),
                    auction_value=str(auction_data.weight_g),
                    confidence=1.0,
                    source=auction_data.source
                ))

        # Check Diameter
        if auction_data.diameter_mm is not None and coin.dimensions.diameter_mm is not None:
            diff = abs(coin.dimensions.diameter_mm - auction_data.diameter_mm)
            if diff > self.diameter_tolerance:
                discrepancies.append(Discrepancy(
                    field="diameter_mm",
                    current_value=str(coin.dimensions.diameter_mm),
                    auction_value=str(auction_data.diameter_mm),
                    confidence=1.0,
                    source=auction_data.source
                ))

        # Check Die Axis
        if auction_data.die_axis is not None and coin.dimensions.die_axis is not None:
            if auction_data.die_axis != coin.dimensions.die_axis:
                discrepancies.append(Discrepancy(
                    field="die_axis",
                    current_value=str(coin.dimensions.die_axis),
                    auction_value=str(auction_data.die_axis),
                    confidence=1.0,
                    source=auction_data.source
                ))

        return discrepancies
