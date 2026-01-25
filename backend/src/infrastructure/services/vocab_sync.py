import httpx
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, Dict, Any
import logging

from src.infrastructure.persistence.models_vocab import IssuerModel

logger = logging.getLogger(__name__)

class VocabSyncService:
    NOMISMA_SPARQL = "http://nomisma.org/query/sparql"

    def __init__(self, session: Session, client: Optional[httpx.AsyncClient] = None):
        self.session = session
        self.client = client or httpx.AsyncClient(timeout=60.0)

    async def sync_nomisma_issuers(self) -> Dict[str, int]:
        query = """
        PREFIX nmo: <http://nomisma.org/ontology#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        
        SELECT ?uri ?label ?start ?end WHERE {
          ?uri a nmo:Person ;
               skos:prefLabel ?label .
          FILTER(lang(?label) = "en")
          OPTIONAL { ?uri nmo:hasStartDate ?start }
          OPTIONAL { ?uri nmo:hasEndDate ?end }
        }
        """
        return await self._sync_sparql(query, "issuer")

    async def sync_nomisma_mints(self) -> Dict[str, int]:
        query = """
        PREFIX nmo: <http://nomisma.org/ontology#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

        SELECT ?uri ?label ?start ?end WHERE {
          ?uri a nmo:Mint ;
               skos:prefLabel ?label .
          FILTER(lang(?label) = "en")
          OPTIONAL { ?uri nmo:hasStartDate ?start }
          OPTIONAL { ?uri nmo:hasEndDate ?end }
        }
        """
        return await self._sync_sparql(query, "mint")

    async def _sync_sparql(self, query: str, entity_type: str) -> Dict[str, int]:
        from src.infrastructure.persistence.models_vocab import MintModel
        try:
            response = await self.client.post(
                self.NOMISMA_SPARQL,
                data={"query": query},
                headers={"Accept": "application/sparql-results+json"}
            )
            response.raise_for_status()
            data = response.json()
            
            stats = {"added": 0, "updated": 0, "unchanged": 0}

            for binding in data["results"]["bindings"]:
                uri = binding["uri"]["value"]
                label = binding["label"]["value"]
                start = self._parse_year(binding.get("start", {}).get("value"))
                end = self._parse_year(binding.get("end", {}).get("value"))
                nomisma_id = uri.split("/")[-1]

                if entity_type == "issuer":
                    stmt = select(IssuerModel).where(IssuerModel.nomisma_id == nomisma_id)
                    model_class = IssuerModel
                else:
                    stmt = select(MintModel).where(MintModel.nomisma_id == nomisma_id)
                    model_class = MintModel

                existing = self.session.scalar(stmt)

                if existing:
                    if existing.canonical_name != label or \
                       (entity_type == "issuer" and (existing.reign_start != start or existing.reign_end != end)) or \
                       (entity_type == "mint" and (existing.active_from != start or existing.active_to != end)):
                        existing.canonical_name = label
                        if entity_type == "issuer":
                            existing.reign_start = start
                            existing.reign_end = end
                        else:
                            existing.active_from = start
                            existing.active_to = end
                        stats["updated"] += 1
                    else:
                        stats["unchanged"] += 1
                else:
                    if entity_type == "issuer":
                        new_item = IssuerModel(
                            canonical_name=label,
                            nomisma_id=nomisma_id,
                            reign_start=start,
                            reign_end=end,
                            issuer_type="unknown"
                        )
                    else:
                        new_item = MintModel(
                            canonical_name=label,
                            nomisma_id=nomisma_id,
                            active_from=start,
                            active_to=end
                        )
                    self.session.add(new_item)
                    stats["added"] += 1
            
            # Note: Do NOT commit here - transaction is managed by get_db() dependency
            # Use flush() to get IDs and make changes visible within the transaction
            self.session.flush()
            return stats

        except Exception as e:
            logger.error(f"Sync failed for {entity_type}: {e}")
            raise

    def _parse_year(self, value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        try:
            # Handle format like "-0027" or "0014" or "200"
            return int(value)
        except ValueError:
            return None
