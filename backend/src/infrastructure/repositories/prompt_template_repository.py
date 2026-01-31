"""
Prompt Template Repository Implementation.

Handles persistence of LLM prompt templates with versioning and A/B testing support.
Implements IPromptTemplateRepository protocol.
"""

from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.domain.coin import PromptTemplate
from src.domain.repositories import IPromptTemplateRepository
from src.infrastructure.persistence.orm import LLMPromptTemplateModel


class SqlAlchemyPromptTemplateRepository(IPromptTemplateRepository):
    """
    Repository for managing LLM prompt templates.

    Provides versioning and A/B testing capabilities for prompts.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, template_id: int) -> Optional[PromptTemplate]:
        """Get a specific template by ID."""
        model = self.session.get(LLMPromptTemplateModel, template_id)
        return self._to_domain(model) if model else None

    def get_active(
        self,
        capability: str,
        variant_name: str = "default"
    ) -> Optional[PromptTemplate]:
        """Get the active template for a capability and variant."""
        model = self.session.query(LLMPromptTemplateModel).filter(
            LLMPromptTemplateModel.capability == capability,
            LLMPromptTemplateModel.variant_name == variant_name,
            LLMPromptTemplateModel.is_active.is_(True),
            LLMPromptTemplateModel.deprecated_at.is_(None)
        ).order_by(desc(LLMPromptTemplateModel.version)).first()

        return self._to_domain(model) if model else None

    def get_latest_version(self, capability: str) -> Optional[PromptTemplate]:
        """Get the highest version template for a capability."""
        model = self.session.query(LLMPromptTemplateModel).filter(
            LLMPromptTemplateModel.capability == capability
        ).order_by(desc(LLMPromptTemplateModel.version)).first()

        return self._to_domain(model) if model else None

    def list_by_capability(
        self,
        capability: str,
        include_deprecated: bool = False
    ) -> List[PromptTemplate]:
        """List all templates for a capability."""
        query = self.session.query(LLMPromptTemplateModel).filter(
            LLMPromptTemplateModel.capability == capability
        )

        if not include_deprecated:
            query = query.filter(LLMPromptTemplateModel.deprecated_at.is_(None))

        query = query.order_by(desc(LLMPromptTemplateModel.version))
        models = query.all()

        return [self._to_domain(m) for m in models]

    def list_active_variants(self, capability: str) -> List[PromptTemplate]:
        """List all active variants for A/B testing."""
        models = self.session.query(LLMPromptTemplateModel).filter(
            LLMPromptTemplateModel.capability == capability,
            LLMPromptTemplateModel.is_active.is_(True),
            LLMPromptTemplateModel.deprecated_at.is_(None)
        ).all()

        return [self._to_domain(m) for m in models]

    def create(self, template: PromptTemplate) -> PromptTemplate:
        """Create a new template. Returns template with ID assigned."""
        model = self._to_model(template)
        model.id = None  # Ensure new record

        self.session.add(model)
        self.session.flush()

        return self._to_domain(model)

    def update(
        self,
        template_id: int,
        template: PromptTemplate
    ) -> Optional[PromptTemplate]:
        """Update an existing template."""
        model = self.session.get(LLMPromptTemplateModel, template_id)
        if not model:
            return None

        # Update fields
        model.system_prompt = template.system_prompt
        model.user_template = template.user_template
        model.parameters = template.parameters
        model.requires_vision = template.requires_vision
        model.output_schema = template.output_schema
        model.variant_name = template.variant_name
        model.traffic_weight = Decimal(str(template.traffic_weight))
        model.is_active = template.is_active
        model.notes = template.notes

        self.session.flush()
        return self._to_domain(model)

    def deprecate(self, template_id: int) -> bool:
        """Mark a template as deprecated."""
        model = self.session.get(LLMPromptTemplateModel, template_id)
        if not model:
            return False

        model.deprecated_at = datetime.now(timezone.utc)
        model.is_active = False

        self.session.flush()
        return True

    def delete(self, template_id: int) -> bool:
        """Delete a template by ID."""
        model = self.session.get(LLMPromptTemplateModel, template_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: LLMPromptTemplateModel) -> PromptTemplate:
        """Convert ORM model to domain value object."""
        return PromptTemplate(
            id=model.id,
            capability=model.capability,
            version=model.version,
            system_prompt=model.system_prompt,
            user_template=model.user_template,
            parameters=model.parameters,
            requires_vision=model.requires_vision or False,
            output_schema=model.output_schema,
            variant_name=model.variant_name or "default",
            traffic_weight=float(model.traffic_weight) if model.traffic_weight else 1.0,
            is_active=model.is_active if model.is_active is not None else True,
            created_at=model.created_at,
            deprecated_at=model.deprecated_at,
            notes=model.notes,
        )

    def _to_model(self, template: PromptTemplate) -> LLMPromptTemplateModel:
        """Convert domain value object to ORM model."""
        return LLMPromptTemplateModel(
            id=template.id,
            capability=template.capability,
            version=template.version,
            system_prompt=template.system_prompt,
            user_template=template.user_template,
            parameters=template.parameters,
            requires_vision=template.requires_vision,
            output_schema=template.output_schema,
            variant_name=template.variant_name,
            traffic_weight=Decimal(str(template.traffic_weight)),
            is_active=template.is_active,
            created_at=template.created_at or datetime.now(timezone.utc),
            deprecated_at=template.deprecated_at,
            notes=template.notes,
        )
