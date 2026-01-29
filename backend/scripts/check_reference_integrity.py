"""
Reference integrity check for catalog references.

Reports:
- Coins with non-empty llm_suggested_references but no (or zero) coin_references links.
- Optionally: reference_types with no coin_references (orphans).

Run from backend directory: uv run python scripts/check_reference_integrity.py [--json] [--orphans]
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure backend src is on path when run as script
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.infrastructure.persistence.database import SessionLocal
from src.application.services.reference_integrity import run_integrity_check


def main() -> None:
    parser = argparse.ArgumentParser(description="Check catalog reference integrity.")
    parser.add_argument("--json", action="store_true", help="Output full report as JSON.")
    parser.add_argument("--orphans", action="store_true", help="Include orphan reference_types (no coin links).")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        report = run_integrity_check(session, include_orphans=args.orphans)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(report["summary"])
            print(f"  Coins with pending suggestions: {report['coins_with_pending_suggestions']}")
            print(f"  Coins pending with zero applied refs: {report['coins_pending_with_zero_applied_refs']}")
            if report.get("orphan_reference_types_count") is not None:
                print(f"  Orphan reference_types: {report['orphan_reference_types_count']}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
