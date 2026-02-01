# Router modules
from . import v2
from . import audit_v2
from . import scrape_v2
from . import import_v2
from . import vocab
from . import series
from . import llm
from . import provenance
# from . import die_study  # Legacy - disabled in favor of Phase 1.5d die_links/die_varieties
from . import dies
from . import die_links
from . import die_pairings
from . import die_varieties
from . import attribution_hypotheses
from . import stats
from . import review
from . import catalog
from . import catalog_v2

__all__ = [
    "v2",
    "audit_v2",
    "scrape_v2",
    "import_v2",
    "vocab",
    "series",
    "llm",
    "provenance",
    # "die_study",  # Legacy - disabled in favor of Phase 1.5d
    "dies",
    "die_links",
    "die_pairings",
    "die_varieties",
    "attribution_hypotheses",
    "stats",
    "review",
    "catalog",
    "catalog_v2",
]
