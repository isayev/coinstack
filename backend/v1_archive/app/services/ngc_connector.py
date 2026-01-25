"""NGC Ancients certificate lookup connector with caching and rate limiting."""
import re
import asyncio
import logging
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
import httpx
from bs4 import BeautifulSoup

from app.schemas.import_preview import (
    NGCCertificateData, 
    ImagePreview, 
    ImageSource, 
    ImageType,
    CoinPreviewData,
)

logger = logging.getLogger(__name__)


# ============================================================================
# EXCEPTIONS
# ============================================================================

class NGCError(Exception):
    """Base exception for NGC connector errors."""
    pass


class InvalidCertificateError(NGCError):
    """Invalid certificate number format."""
    pass


class CertificateNotFoundError(NGCError):
    """Certificate not found in NGC database."""
    pass


class NGCTimeoutError(NGCError):
    """NGC lookup timed out."""
    pass


class NGCRateLimitError(NGCError):
    """Rate limited by NGC."""
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


# ============================================================================
# SIMPLE RATE LIMITER
# ============================================================================

class AsyncRateLimiter:
    """Simple async rate limiter using token bucket."""
    
    def __init__(self, rate: int, per: int = 60):
        """
        Args:
            rate: Number of requests allowed
            per: Time period in seconds
        """
        self.rate = rate
        self.per = per
        self.tokens = rate
        self.last_update = datetime.utcnow()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a rate limit token, waiting if necessary."""
        async with self._lock:
            now = datetime.utcnow()
            time_passed = (now - self.last_update).total_seconds()
            
            # Replenish tokens
            self.tokens = min(self.rate, self.tokens + time_passed * (self.rate / self.per))
            self.last_update = now
            
            if self.tokens < 1:
                # Calculate wait time
                wait_time = (1 - self.tokens) * (self.per / self.rate)
                logger.info(f"Rate limiting: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


# ============================================================================
# SIMPLE CACHE
# ============================================================================

class SimpleCache:
    """Simple in-memory cache with TTL."""
    
    def __init__(self):
        self._cache: dict[str, tuple[any, datetime]] = {}
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache if not expired."""
        if key in self._cache:
            value, expires_at = self._cache[key]
            if datetime.utcnow() < expires_at:
                logger.debug(f"Cache hit for {key}")
                return value
            else:
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: str, ttl: int):
        """Set value in cache with TTL in seconds."""
        expires_at = datetime.utcnow().replace(
            second=0, microsecond=0
        )
        # Add TTL
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self._cache[key] = (value, expires_at)
        logger.debug(f"Cached {key} for {ttl}s")
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
    
    def cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.utcnow()
        expired = [k for k, (_, exp) in self._cache.items() if now >= exp]
        for key in expired:
            del self._cache[key]


# Global cache instance
_ngc_cache = SimpleCache()


# ============================================================================
# NGC CONNECTOR
# ============================================================================

class NGCConnector:
    """
    Hardened NGC Ancients certificate lookup connector.
    
    Features:
    - Rate limiting (5 requests/minute by default)
    - 30-day caching of successful lookups
    - Certificate format validation
    - Robust error handling with specific exception types
    - Image extraction (PhotoVision)
    """
    
    # Rate limit: 5 requests per minute
    RATE_LIMIT = 5
    RATE_PERIOD = 60  # seconds
    
    # Cache TTL: 30 days (NGC data doesn't change)
    CACHE_TTL = 86400 * 30
    
    # Certificate validation pattern (7-10 digits)
    CERT_PATTERN = re.compile(r'^\d{7,10}$')
    
    # NGC URLs
    BASE_URL = "https://www.ngccoin.com/certlookup/{cert}/NGCAncients"
    VERIFY_URL = "https://www.ngccoin.com/certlookup/{cert}/"
    
    # Request timeout
    TIMEOUT = 30.0
    
    # User agent
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    def __init__(
        self,
        cache: Optional[SimpleCache] = None,
        rate_limit: int = RATE_LIMIT,
        timeout: float = TIMEOUT,
    ):
        """
        Initialize NGC connector.
        
        Args:
            cache: Cache instance (uses global cache if None)
            rate_limit: Max requests per minute
            timeout: Request timeout in seconds
        """
        self.cache = cache or _ngc_cache
        self.rate_limiter = AsyncRateLimiter(rate_limit, self.RATE_PERIOD)
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": self.USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                }
            )
        return self._client
    
    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def lookup_certificate(self, cert_number: str) -> NGCCertificateData:
        """
        Lookup NGC certificate and extract coin data.
        
        Args:
            cert_number: NGC certification number
            
        Returns:
            NGCCertificateData with grade, scores, and images
            
        Raises:
            InvalidCertificateError: Invalid certificate format
            CertificateNotFoundError: Certificate not found
            NGCTimeoutError: Request timed out
            NGCRateLimitError: Rate limited (includes retry_after)
        """
        # 1. Validate certificate format
        cert_number = cert_number.strip()
        if not self.CERT_PATTERN.match(cert_number):
            raise InvalidCertificateError(
                f"Invalid NGC cert format: {cert_number}. Must be 7-10 digits."
            )
        
        # 2. Check cache
        cache_key = f"ngc:{cert_number}"
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"NGC cache hit for cert {cert_number}")
            return NGCCertificateData.model_validate_json(cached)
        
        # 3. Rate limit
        await self.rate_limiter.acquire()
        
        # 4. Fetch certificate page
        url = self.BASE_URL.format(cert=cert_number)
        client = await self._get_client()
        
        try:
            async with asyncio.timeout(self.timeout):
                response = await client.get(url)
        except asyncio.TimeoutError:
            raise NGCTimeoutError(f"NGC lookup timed out for cert {cert_number}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching NGC cert {cert_number}: {e}")
            raise NGCError(f"HTTP error: {e}")
        
        # 5. Handle response status
        if response.status_code == 404:
            raise CertificateNotFoundError(f"NGC cert {cert_number} not found")
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise NGCRateLimitError(
                f"Rate limited by NGC",
                retry_after=retry_after
            )
        
        if response.status_code != 200:
            raise NGCError(f"NGC returned status {response.status_code}")
        
        # 6. Check if certificate was found (NGC returns 200 even for not found)
        if "not found" in response.text.lower() or "no results" in response.text.lower():
            raise CertificateNotFoundError(f"NGC cert {cert_number} not found")
        
        # 7. Parse response
        data = self._parse_certificate_page(response.text, cert_number)
        
        # 8. Cache successful lookup
        await self.cache.set(cache_key, data.model_dump_json(), self.CACHE_TTL)
        logger.info(f"NGC lookup successful for cert {cert_number}, cached for 30 days")
        
        return data
    
    def _parse_certificate_page(self, html: str, cert_number: str) -> NGCCertificateData:
        """
        Parse NGC certificate page HTML.
        
        Extracts:
        - Grade (MS, AU, XF, VF, etc.)
        - Strike/Surface scores (4/5, 5/5)
        - Designation (Choice, Fine Style)
        - Description
        - PhotoVision images
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Initialize data
        grade = None
        strike_score = None
        surface_score = None
        numeric_grade = None
        designation = None
        description = None
        coin_type = None
        images: list[ImagePreview] = []
        
        # --- Parse Grade ---
        # Look for grade in various elements
        grade_patterns = [
            (r'(MS|AU|XF|VF|F|VG|G|AG|FR|PO|PR|PF)\s*(\d{1,2})?', 'grade'),
            (r'(Choice|Gem)\s+(MS|AU|XF|VF)', 'designation_grade'),
        ]
        
        # Try to find grade section
        grade_elem = soup.select_one('.cert-grade, .grade, [class*="grade"]')
        if grade_elem:
            grade_text = grade_elem.get_text(strip=True)
            match = re.search(r'(MS|AU|XF|VF|Fine|VG|Good|AG|Fair|Poor)\s*(\d+)?', grade_text, re.I)
            if match:
                grade = match.group(1).upper()
                if match.group(2):
                    numeric_grade = int(match.group(2))
        
        # Look for strike/surface scores
        score_elem = soup.select_one('.cert-scores, [class*="strike"], [class*="surface"]')
        if score_elem:
            score_text = score_elem.get_text(strip=True)
            
            strike_match = re.search(r'Strike[:\s]*(\d/\d)', score_text, re.I)
            if strike_match:
                strike_score = strike_match.group(1)
            
            surface_match = re.search(r'Surface[:\s]*(\d/\d)', score_text, re.I)
            if surface_match:
                surface_score = surface_match.group(1)
        
        # Alternative: Look for scores in any text
        if not strike_score or not surface_score:
            full_text = soup.get_text()
            if not strike_score:
                match = re.search(r'Strike[:\s]*(\d/\d)', full_text, re.I)
                if match:
                    strike_score = match.group(1)
            if not surface_score:
                match = re.search(r'Surface[:\s]*(\d/\d)', full_text, re.I)
                if match:
                    surface_score = match.group(1)
        
        # Look for designation
        designation_elem = soup.select_one('.cert-designation, [class*="designation"]')
        if designation_elem:
            designation = designation_elem.get_text(strip=True)
        else:
            # Check for common designations in text
            full_text = soup.get_text()
            for des in ['Fine Style', 'Choice', 'Gem', 'Superb Gem', 'NGC Ancients']:
                if des.lower() in full_text.lower():
                    designation = des
                    break
        
        # Parse description/coin type
        desc_elem = soup.select_one('.cert-description, .coin-description, [class*="description"]')
        if desc_elem:
            description = desc_elem.get_text(strip=True)
        
        type_elem = soup.select_one('.cert-type, .coin-type, [class*="cointype"]')
        if type_elem:
            coin_type = type_elem.get_text(strip=True)
        
        # --- Parse Images ---
        # Look for PhotoVision images
        img_patterns = [
            'img[src*="photovision"]',
            'img[src*="ngc"]',
            '.cert-images img',
            '.coin-images img',
            '[class*="photo"] img',
        ]
        
        for pattern in img_patterns:
            for img in soup.select(pattern):
                src = img.get('src') or img.get('data-src')
                if src and 'placeholder' not in src.lower():
                    # Determine image type from context
                    img_type = ImageType.COMBINED
                    parent_text = img.parent.get_text().lower() if img.parent else ""
                    alt_text = (img.get('alt') or '').lower()
                    
                    if 'obverse' in parent_text or 'obverse' in alt_text:
                        img_type = ImageType.OBVERSE
                    elif 'reverse' in parent_text or 'reverse' in alt_text:
                        img_type = ImageType.REVERSE
                    elif 'slab' in parent_text or 'holder' in parent_text:
                        img_type = ImageType.SLAB_FRONT
                    
                    # Make URL absolute
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.ngccoin.com' + src
                    
                    images.append(ImagePreview(
                        url=src,
                        source=ImageSource.NGC_PHOTOVISION,
                        image_type=img_type,
                    ))
        
        # Deduplicate images by URL
        seen_urls = set()
        unique_images = []
        for img in images:
            if img.url not in seen_urls:
                seen_urls.add(img.url)
                unique_images.append(img)
        
        return NGCCertificateData(
            cert_number=cert_number,
            grade=grade,
            strike_score=strike_score,
            surface_score=surface_score,
            numeric_grade=numeric_grade,
            designation=designation,
            description=description or coin_type,
            coin_type=coin_type,
            images=unique_images,
            verified=True,
            verification_url=self.BASE_URL.format(cert=cert_number),
        )
    
    def map_to_preview(self, cert_data: NGCCertificateData) -> CoinPreviewData:
        """
        Map NGC certificate data to CoinPreviewData for preview/edit.
        
        Note: NGC data is limited - mainly grading info and images.
        Other fields need to be filled from auction data or manually.
        """
        # Parse strike/surface scores to integers
        strike_quality = None
        surface_quality = None
        
        if cert_data.strike_score:
            match = re.match(r'(\d)/\d', cert_data.strike_score)
            if match:
                strike_quality = int(match.group(1))
        
        if cert_data.surface_score:
            match = re.match(r'(\d)/\d', cert_data.surface_score)
            if match:
                surface_quality = int(match.group(1))
        
        # Build grade string
        grade_parts = []
        if cert_data.designation:
            grade_parts.append(cert_data.designation)
        if cert_data.grade:
            grade_parts.append(cert_data.grade)
            if cert_data.numeric_grade:
                grade_parts[-1] = f"{cert_data.grade} {cert_data.numeric_grade}"
        if cert_data.strike_score and cert_data.surface_score:
            grade_parts.append(f"{cert_data.strike_score}, {cert_data.surface_score}")
        
        grade = " ".join(grade_parts) if grade_parts else None
        
        return CoinPreviewData(
            # Grading (NGC authoritative)
            grade_service="ngc",
            grade=grade,
            strike_quality=strike_quality,
            surface_quality=surface_quality,
            certification_number=cert_data.cert_number,
            
            # Description (may contain coin details)
            description=cert_data.description,
            title=cert_data.coin_type or cert_data.description,
            
            # Images
            images=cert_data.images,
            
            # Holder type
            holder_type="ngc_slab",
        )


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

# Global connector instance (reuses rate limiter and cache)
_ngc_connector: Optional[NGCConnector] = None


def get_ngc_connector() -> NGCConnector:
    """Get NGC connector instance (singleton for rate limiting)."""
    global _ngc_connector
    if _ngc_connector is None:
        _ngc_connector = NGCConnector()
    return _ngc_connector


async def cleanup_ngc_connector():
    """Cleanup NGC connector (call on shutdown)."""
    global _ngc_connector
    if _ngc_connector:
        await _ngc_connector.close()
        _ngc_connector = None
