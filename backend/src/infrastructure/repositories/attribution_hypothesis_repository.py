"""Concrete repository implementation for attribution hypotheses."""

from typing import Optional
from decimal import Decimal
import sqlalchemy as sa
from sqlalchemy.orm import Session, selectinload
from src.domain.coin import AttributionHypothesis, AttributionCertainty
from src.domain.repositories_attribution import IAttributionHypothesisRepository
from src.infrastructure.persistence.orm import AttributionHypothesisModel


class SqlAlchemyAttributionHypothesisRepository(IAttributionHypothesisRepository):
    """SQLAlchemy implementation of attribution hypothesis repository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, hypothesis_id: int) -> Optional[AttributionHypothesis]:
        """Get attribution hypothesis by ID with eager loading."""
        model = (
            self.session.query(AttributionHypothesisModel)
            .options(selectinload(AttributionHypothesisModel.coin))
            .filter(AttributionHypothesisModel.id == hypothesis_id)
            .first()
        )
        return self._to_domain(model) if model else None

    def get_by_coin_id(self, coin_id: int) -> list[AttributionHypothesis]:
        """Get all attribution hypotheses for a coin (ordered by rank)."""
        models = (
            self.session.query(AttributionHypothesisModel)
            .options(selectinload(AttributionHypothesisModel.coin))
            .filter(AttributionHypothesisModel.coin_id == coin_id)
            .order_by(AttributionHypothesisModel.hypothesis_rank)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_primary(self, coin_id: int) -> Optional[AttributionHypothesis]:
        """Get the primary attribution hypothesis (rank=1) for a coin."""
        model = (
            self.session.query(AttributionHypothesisModel)
            .options(selectinload(AttributionHypothesisModel.coin))
            .filter(
                AttributionHypothesisModel.coin_id == coin_id,
                AttributionHypothesisModel.hypothesis_rank == 1
            )
            .first()
        )
        return self._to_domain(model) if model else None

    def create(self, hypothesis: AttributionHypothesis) -> AttributionHypothesis:
        """Create new attribution hypothesis."""
        model = self._to_model(hypothesis)
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)

    def update(self, hypothesis_id: int, hypothesis: AttributionHypothesis) -> Optional[AttributionHypothesis]:
        """Update existing attribution hypothesis."""
        model = self.session.query(AttributionHypothesisModel).filter(
            AttributionHypothesisModel.id == hypothesis_id
        ).first()

        if not model:
            return None

        # Update fields
        model.issuer = hypothesis.issuer if hypothesis.issuer is not None else model.issuer
        model.issuer_confidence = hypothesis.issuer_confidence.value if hypothesis.issuer_confidence else model.issuer_confidence

        model.mint = hypothesis.mint if hypothesis.mint is not None else model.mint
        model.mint_confidence = hypothesis.mint_confidence.value if hypothesis.mint_confidence else model.mint_confidence

        model.year_start = hypothesis.year_start if hypothesis.year_start is not None else model.year_start
        model.year_end = hypothesis.year_end if hypothesis.year_end is not None else model.year_end
        model.date_confidence = hypothesis.date_confidence.value if hypothesis.date_confidence else model.date_confidence

        model.denomination = hypothesis.denomination if hypothesis.denomination is not None else model.denomination
        model.denomination_confidence = hypothesis.denomination_confidence.value if hypothesis.denomination_confidence else model.denomination_confidence

        model.overall_certainty = hypothesis.overall_certainty.value if hypothesis.overall_certainty else model.overall_certainty
        model.confidence_score = hypothesis.confidence_score if hypothesis.confidence_score is not None else model.confidence_score

        model.attribution_notes = hypothesis.attribution_notes if hypothesis.attribution_notes is not None else model.attribution_notes
        model.reference_support = hypothesis.reference_support if hypothesis.reference_support is not None else model.reference_support
        model.source = hypothesis.source if hypothesis.source is not None else model.source

        self.session.flush()
        return self._to_domain(model)

    def delete(self, hypothesis_id: int) -> bool:
        """Delete attribution hypothesis."""
        model = self.session.query(AttributionHypothesisModel).filter(
            AttributionHypothesisModel.id == hypothesis_id
        ).first()

        if not model:
            return False

        self.session.delete(model)
        self.session.flush()
        return True

    def set_primary(self, hypothesis_id: int) -> AttributionHypothesis:
        """Promote hypothesis to rank 1, shift others down atomically.

        CRITICAL FIX from code review: Detailed reordering algorithm with atomic SQL updates.
        """
        hypothesis = self.session.query(AttributionHypothesisModel).get(hypothesis_id)
        if not hypothesis:
            raise ValueError(f"Hypothesis {hypothesis_id} not found")

        coin_id = hypothesis.coin_id
        old_rank = hypothesis.hypothesis_rank

        # If already rank 1, no-op
        if old_rank == 1:
            return self._to_domain(hypothesis)

        # Atomic reordering using SQL UPDATE
        # Step 1: Set current rank 1 to temp value (-1)
        self.session.execute(
            sa.update(AttributionHypothesisModel)
            .where(
                AttributionHypothesisModel.coin_id == coin_id,
                AttributionHypothesisModel.hypothesis_rank == 1
            )
            .values(hypothesis_rank=-1)
        )

        # Step 2: Shift ranks 2 to old_rank down by 1
        self.session.execute(
            sa.update(AttributionHypothesisModel)
            .where(
                AttributionHypothesisModel.coin_id == coin_id,
                AttributionHypothesisModel.hypothesis_rank.between(2, old_rank)
            )
            .values(hypothesis_rank=AttributionHypothesisModel.hypothesis_rank - 1)
        )

        # Step 3: Set promoted hypothesis to rank 1
        hypothesis.hypothesis_rank = 1

        # Step 4: Set temp rank to max
        max_rank = self.session.query(
            sa.func.max(AttributionHypothesisModel.hypothesis_rank)
        ).filter(AttributionHypothesisModel.coin_id == coin_id).scalar() or 1

        self.session.execute(
            sa.update(AttributionHypothesisModel)
            .where(
                AttributionHypothesisModel.coin_id == coin_id,
                AttributionHypothesisModel.hypothesis_rank == -1
            )
            .values(hypothesis_rank=max_rank + 1)
        )

        self.session.flush()
        return self._to_domain(hypothesis)

    def reorder(self, coin_id: int, hypothesis_ids: list[int]) -> list[AttributionHypothesis]:
        """Reorder hypotheses for a coin (hypothesis_ids in desired rank order)."""
        # Get all hypotheses for this coin
        hypotheses = self.session.query(AttributionHypothesisModel).filter(
            AttributionHypothesisModel.coin_id == coin_id
        ).all()

        # Create ID to hypothesis map
        hypothesis_map = {h.id: h for h in hypotheses}

        # Validate all provided IDs exist and belong to this coin
        for hypothesis_id in hypothesis_ids:
            if hypothesis_id not in hypothesis_map:
                raise ValueError(f"Hypothesis {hypothesis_id} not found for coin {coin_id}")

        # Update ranks atomically
        # First, set all to temp negative values to avoid unique constraint violations
        for i, hypothesis_id in enumerate(hypothesis_ids):
            hypothesis_map[hypothesis_id].hypothesis_rank = -(i + 1)

        self.session.flush()

        # Then set to actual positive ranks
        for i, hypothesis_id in enumerate(hypothesis_ids):
            hypothesis_map[hypothesis_id].hypothesis_rank = i + 1

        self.session.flush()

        # Return reordered list
        return [self._to_domain(hypothesis_map[hid]) for hid in hypothesis_ids]

    def _to_domain(self, model: AttributionHypothesisModel) -> AttributionHypothesis:
        """Convert ORM model to domain entity."""
        return AttributionHypothesis(
            id=model.id,
            coin_id=model.coin_id,
            hypothesis_rank=model.hypothesis_rank,
            issuer=model.issuer,
            issuer_confidence=AttributionCertainty(model.issuer_confidence) if model.issuer_confidence else None,
            mint=model.mint,
            mint_confidence=AttributionCertainty(model.mint_confidence) if model.mint_confidence else None,
            year_start=model.year_start,
            year_end=model.year_end,
            date_confidence=AttributionCertainty(model.date_confidence) if model.date_confidence else None,
            denomination=model.denomination,
            denomination_confidence=AttributionCertainty(model.denomination_confidence) if model.denomination_confidence else None,
            overall_certainty=AttributionCertainty(model.overall_certainty) if model.overall_certainty else None,
            confidence_score=model.confidence_score,
            attribution_notes=model.attribution_notes,
            reference_support=model.reference_support,
            source=model.source
        )

    def _to_model(self, hypothesis: AttributionHypothesis) -> AttributionHypothesisModel:
        """Convert domain entity to ORM model."""
        return AttributionHypothesisModel(
            id=hypothesis.id,
            coin_id=hypothesis.coin_id,
            hypothesis_rank=hypothesis.hypothesis_rank,
            issuer=hypothesis.issuer,
            issuer_confidence=hypothesis.issuer_confidence.value if hypothesis.issuer_confidence else None,
            mint=hypothesis.mint,
            mint_confidence=hypothesis.mint_confidence.value if hypothesis.mint_confidence else None,
            year_start=hypothesis.year_start,
            year_end=hypothesis.year_end,
            date_confidence=hypothesis.date_confidence.value if hypothesis.date_confidence else None,
            denomination=hypothesis.denomination,
            denomination_confidence=hypothesis.denomination_confidence.value if hypothesis.denomination_confidence else None,
            overall_certainty=hypothesis.overall_certainty.value if hypothesis.overall_certainty else None,
            confidence_score=hypothesis.confidence_score,
            attribution_notes=hypothesis.attribution_notes,
            reference_support=hypothesis.reference_support,
            source=hypothesis.source
        )
