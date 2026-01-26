"""Test script for NGC import endpoint."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.external.ngc_client import (
    get_ngc_client,
    InvalidCertificateError,
    CertificateNotFoundError,
    NGCTimeoutError,
    NGCRateLimitError,
)


async def test_ngc_lookup(cert_number: str):
    """Test NGC certificate lookup."""
    client = get_ngc_client()
    
    print(f"Testing NGC certificate lookup: {cert_number}")
    print("-" * 50)
    
    try:
        data = await client.lookup_certificate(cert_number)
        print(f"✅ Success!")
        print(f"   Cert Number: {data.cert_number}")
        print(f"   Grade: {data.grade}")
        print(f"   Strike: {data.strike_score}")
        print(f"   Surface: {data.surface_score}")
        print(f"   Designation: {data.designation}")
        print(f"   Description: {data.description}")
        print(f"   Images: {len(data.images)}")
        for idx, img in enumerate(data.images[:3]):  # Show first 3
            print(f"      [{idx+1}] {img.url[:80]}...")
        print(f"   Verification URL: {data.verification_url}")
        return True
    except InvalidCertificateError as e:
        print(f"❌ Invalid certificate format: {e}")
        return False
    except CertificateNotFoundError as e:
        print(f"❌ Certificate not found: {e}")
        return False
    except NGCTimeoutError as e:
        print(f"❌ Timeout: {e}")
        return False
    except NGCRateLimitError as e:
        print(f"❌ Rate limited: {e} (retry after {e.retry_after}s)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_ngc_import.py <cert_number>")
        print("Example: python test_ngc_import.py 4938475")
        sys.exit(1)
    
    cert_number = sys.argv[1]
    result = asyncio.run(test_ngc_lookup(cert_number))
    sys.exit(0 if result else 1)
