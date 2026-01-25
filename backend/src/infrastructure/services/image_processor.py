"""
Image Processor for CoinStack LLM Vision.

Handles image validation, preprocessing, and perceptual hashing for 
caching vision model results.

Features:
- Format validation (JPEG, PNG, WebP supported)
- Size limits (max 10MB, max 4096px dimension)
- Preprocessing (resize, convert to JPEG, strip EXIF)
- Perceptual hashing (phash) for similar image matching
- Multi-image concatenation for obverse/reverse pairs
"""

from __future__ import annotations

import base64
import hashlib
import io
import logging
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional, List, Tuple, Union

logger = logging.getLogger(__name__)

# Check for Pillow availability
try:
    from PIL import Image, ExifTags
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    Image = None  # type: ignore

# Check for imagehash availability
try:
    import imagehash
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False
    imagehash = None  # type: ignore


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass(frozen=True)
class ImageConfig:
    """Image processing configuration."""
    # Size limits
    max_size_mb: float = 10.0
    max_dimension_px: int = 4096
    resize_max_dimension: int = 2048
    
    # Formats
    accepted_formats: Tuple[str, ...] = ("jpeg", "jpg", "png", "webp")
    rejected_formats: Tuple[str, ...] = ("heic", "tiff", "bmp", "gif")
    output_format: str = "jpeg"
    output_quality: int = 85
    
    # Hash settings
    hash_size: int = 16  # Higher = more sensitive to differences
    
    # Multi-image
    max_images_per_request: int = 2


DEFAULT_CONFIG = ImageConfig()


# =============================================================================
# EXCEPTIONS
# =============================================================================

class ImageProcessingError(Exception):
    """Base exception for image processing errors."""
    pass


class InvalidImageFormat(ImageProcessingError):
    """Image format not supported."""
    def __init__(self, format: str, accepted: Tuple[str, ...]):
        super().__init__(f"Format '{format}' not supported. Accepted: {', '.join(accepted)}")
        self.format = format
        self.accepted = accepted


class ImageTooLarge(ImageProcessingError):
    """Image exceeds size limits."""
    def __init__(self, actual_mb: float, max_mb: float):
        super().__init__(f"Image too large: {actual_mb:.1f}MB (max: {max_mb}MB)")
        self.actual_mb = actual_mb
        self.max_mb = max_mb


class ImageDimensionsTooLarge(ImageProcessingError):
    """Image dimensions exceed limits."""
    def __init__(self, actual: Tuple[int, int], max_dim: int):
        super().__init__(f"Image too large: {actual[0]}x{actual[1]} (max dimension: {max_dim}px)")
        self.actual = actual
        self.max_dim = max_dim


class PillowNotAvailable(ImageProcessingError):
    """Pillow not installed."""
    def __init__(self):
        super().__init__("Pillow not installed. Run: pip install Pillow")


class ImageHashNotAvailable(ImageProcessingError):
    """imagehash not installed."""
    def __init__(self):
        super().__init__("imagehash not installed. Run: pip install imagehash")


# =============================================================================
# IMAGE PROCESSOR
# =============================================================================

class ImageProcessor:
    """
    Processes images for LLM vision models.
    
    Handles validation, resizing, format conversion, and EXIF stripping
    before sending images to vision models.
    """
    
    def __init__(self, config: Optional[ImageConfig] = None):
        self.config = config or DEFAULT_CONFIG
        
        if not PILLOW_AVAILABLE:
            logger.warning("Pillow not installed. Image processing will fail.")
    
    def validate(self, image_bytes: bytes, filename: Optional[str] = None) -> None:
        """
        Validate image format and size.
        
        Args:
            image_bytes: Raw image bytes
            filename: Optional filename for format detection
        
        Raises:
            InvalidImageFormat: If format not supported
            ImageTooLarge: If exceeds size limit
            ImageDimensionsTooLarge: If dimensions too large
        """
        if not PILLOW_AVAILABLE:
            raise PillowNotAvailable()
        
        # Check file size
        size_mb = len(image_bytes) / (1024 * 1024)
        if size_mb > self.config.max_size_mb:
            raise ImageTooLarge(size_mb, self.config.max_size_mb)
        
        # Check format
        try:
            img = Image.open(io.BytesIO(image_bytes))
            format_lower = (img.format or "").lower()
        except Exception as e:
            raise InvalidImageFormat(
                filename or "unknown", 
                self.config.accepted_formats
            ) from e
        
        # Validate format
        if format_lower not in self.config.accepted_formats:
            # Check if it's explicitly rejected
            if format_lower in self.config.rejected_formats:
                raise InvalidImageFormat(format_lower, self.config.accepted_formats)
            # Also check filename extension if provided
            if filename:
                ext = filename.lower().split(".")[-1]
                if ext not in self.config.accepted_formats:
                    raise InvalidImageFormat(ext, self.config.accepted_formats)
        
        # Check dimensions
        if max(img.size) > self.config.max_dimension_px:
            raise ImageDimensionsTooLarge(img.size, self.config.max_dimension_px)
    
    def preprocess(
        self,
        image_bytes: bytes,
        filename: Optional[str] = None,
        strip_exif: bool = True,
    ) -> bytes:
        """
        Preprocess image for LLM consumption.
        
        Operations:
        1. Validate format and size
        2. Resize if larger than max dimension
        3. Convert to JPEG
        4. Strip EXIF data (privacy)
        
        Args:
            image_bytes: Raw image bytes
            filename: Optional filename for format detection
            strip_exif: Whether to strip EXIF metadata
        
        Returns:
            Preprocessed image bytes (JPEG)
        """
        if not PILLOW_AVAILABLE:
            raise PillowNotAvailable()
        
        # Validate first
        self.validate(image_bytes, filename)
        
        # Load image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Handle EXIF orientation
        try:
            exif = img._getexif()
            if exif:
                for orientation_tag in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation_tag] == 'Orientation':
                        break
                orientation = exif.get(orientation_tag)
                if orientation:
                    rotations = {
                        3: 180,
                        6: 270,
                        8: 90,
                    }
                    if orientation in rotations:
                        img = img.rotate(rotations[orientation], expand=True)
        except (AttributeError, KeyError, TypeError):
            pass
        
        # Resize if needed
        if max(img.size) > self.config.resize_max_dimension:
            img.thumbnail(
                (self.config.resize_max_dimension, self.config.resize_max_dimension),
                Image.Resampling.LANCZOS
            )
            logger.debug(f"Resized image to {img.size}")
        
        # Convert to RGB (remove alpha channel if present)
        if img.mode in ("RGBA", "P", "LA", "L"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA" or img.mode == "LA":
                background.paste(img, mask=img.split()[-1])  # Use alpha as mask
            else:
                background.paste(img)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
        
        # Save to JPEG
        output = io.BytesIO()
        img.save(
            output,
            format="JPEG",
            quality=self.config.output_quality,
            optimize=True,
        )
        
        return output.getvalue()
    
    def to_base64(self, image_bytes: bytes, preprocess: bool = True) -> str:
        """
        Convert image to base64 string for LLM API.
        
        Args:
            image_bytes: Raw or preprocessed image bytes
            preprocess: Whether to preprocess first
        
        Returns:
            Base64-encoded string
        """
        if preprocess:
            image_bytes = self.preprocess(image_bytes)
        return base64.b64encode(image_bytes).decode("utf-8")
    
    def from_base64(self, b64_string: str) -> bytes:
        """
        Decode base64 image string.
        
        Args:
            b64_string: Base64-encoded image
        
        Returns:
            Raw image bytes
        """
        return base64.b64decode(b64_string)
    
    def concatenate_images(
        self,
        images: List[bytes],
        direction: str = "horizontal",
        spacing: int = 10,
    ) -> bytes:
        """
        Concatenate multiple images side-by-side.
        
        Used for sending obverse + reverse together to vision model.
        
        Args:
            images: List of image bytes
            direction: "horizontal" or "vertical"
            spacing: Pixels between images
        
        Returns:
            Combined image bytes (JPEG)
        """
        if not PILLOW_AVAILABLE:
            raise PillowNotAvailable()
        
        if len(images) > self.config.max_images_per_request:
            raise ValueError(
                f"Max {self.config.max_images_per_request} images per request"
            )
        
        # Load and preprocess all images
        pil_images = []
        for img_bytes in images:
            preprocessed = self.preprocess(img_bytes)
            pil_images.append(Image.open(io.BytesIO(preprocessed)))
        
        if direction == "horizontal":
            # Calculate dimensions
            total_width = sum(img.width for img in pil_images) + spacing * (len(pil_images) - 1)
            max_height = max(img.height for img in pil_images)
            
            # Create combined image
            combined = Image.new("RGB", (total_width, max_height), (255, 255, 255))
            x_offset = 0
            for img in pil_images:
                # Center vertically
                y_offset = (max_height - img.height) // 2
                combined.paste(img, (x_offset, y_offset))
                x_offset += img.width + spacing
        else:
            # Vertical concatenation
            max_width = max(img.width for img in pil_images)
            total_height = sum(img.height for img in pil_images) + spacing * (len(pil_images) - 1)
            
            combined = Image.new("RGB", (max_width, total_height), (255, 255, 255))
            y_offset = 0
            for img in pil_images:
                # Center horizontally
                x_offset = (max_width - img.width) // 2
                combined.paste(img, (x_offset, y_offset))
                y_offset += img.height + spacing
        
        # Save combined
        output = io.BytesIO()
        combined.save(output, format="JPEG", quality=self.config.output_quality)
        return output.getvalue()


# =============================================================================
# PERCEPTUAL HASHING
# =============================================================================

class ImageHasher:
    """
    Computes perceptual hashes for images.
    
    Uses pHash (perceptual hash) algorithm which is robust to:
    - Resizing
    - Minor color changes
    - JPEG compression
    - Slight crops
    
    But sensitive to:
    - Different subjects (different coins)
    - Major rotations
    - Significant modifications
    """
    
    def __init__(self, hash_size: int = 16):
        """
        Initialize hasher.
        
        Args:
            hash_size: Hash size (higher = more sensitive to differences)
                       16 is a good balance for coin images
        """
        if not IMAGEHASH_AVAILABLE:
            logger.warning("imagehash not installed. Perceptual hashing disabled.")
        if not PILLOW_AVAILABLE:
            logger.warning("Pillow not installed. Image hashing will fail.")
        
        self.hash_size = hash_size
    
    def compute_hash(self, image_bytes: bytes) -> str:
        """
        Compute perceptual hash of image.
        
        Args:
            image_bytes: Raw image bytes
        
        Returns:
            Hex string representation of hash
        """
        if not IMAGEHASH_AVAILABLE:
            raise ImageHashNotAvailable()
        if not PILLOW_AVAILABLE:
            raise PillowNotAvailable()
        
        img = Image.open(io.BytesIO(image_bytes))
        phash = imagehash.phash(img, hash_size=self.hash_size)
        return str(phash)
    
    def compute_hash_from_b64(self, b64_string: str) -> str:
        """
        Compute hash from base64-encoded image.
        
        Args:
            b64_string: Base64-encoded image
        
        Returns:
            Hex string hash
        """
        image_bytes = base64.b64decode(b64_string)
        return self.compute_hash(image_bytes)
    
    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """
        Compute Hamming distance between two hashes.
        
        Lower distance = more similar images.
        
        Args:
            hash1: First hash string
            hash2: Second hash string
        
        Returns:
            Hamming distance (0 = identical)
        """
        if not IMAGEHASH_AVAILABLE:
            raise ImageHashNotAvailable()
        
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        return h1 - h2
    
    def is_similar(
        self,
        hash1: str,
        hash2: str,
        threshold: int = 10
    ) -> bool:
        """
        Check if two images are perceptually similar.
        
        Args:
            hash1: First hash
            hash2: Second hash
            threshold: Max Hamming distance to consider similar
                      (10 is good for coin images)
        
        Returns:
            True if similar within threshold
        """
        distance = self.hamming_distance(hash1, hash2)
        return distance <= threshold


# =============================================================================
# VISION CACHE
# =============================================================================

class VisionCache:
    """
    SQLite-based cache for vision model results using perceptual hashing.
    
    Caches results by image hash so that similar images (resized,
    recompressed) return cached results.
    """
    
    def __init__(
        self,
        db_path: str = "data/llm_vision_cache.sqlite",
        hash_size: int = 16,
        ttl_days: int = 30,
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.hasher = ImageHasher(hash_size=hash_size)
        self.ttl_days = ttl_days
        self._local = threading.local()
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(str(self.db_path))
        return self._local.conn
    
    def _init_db(self):
        """Initialize cache database."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vision_cache (
                image_hash TEXT PRIMARY KEY,
                capability TEXT NOT NULL,
                response TEXT NOT NULL,
                model TEXT,
                cost_usd REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_vision_cache_expires
            ON vision_cache(expires_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_vision_cache_capability
            ON vision_cache(capability)
        """)
        conn.commit()
    
    async def get(
        self,
        image_bytes: bytes,
        capability: str,
    ) -> Optional[dict]:
        """
        Get cached result for image.
        
        Args:
            image_bytes: Image bytes (will be hashed)
            capability: LLM capability name
        
        Returns:
            Cached result dict or None if miss
        """
        if not IMAGEHASH_AVAILABLE:
            return None  # No caching without imagehash
        
        try:
            img_hash = self.hasher.compute_hash(image_bytes)
        except Exception as e:
            logger.warning(f"Failed to compute image hash: {e}")
            return None
        
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT response, model, cost_usd, created_at
            FROM vision_cache
            WHERE image_hash = ? AND capability = ? AND expires_at > datetime('now')
            """,
            (img_hash, capability)
        )
        row = cursor.fetchone()
        
        if row:
            import json
            logger.debug(f"Vision cache hit for {capability}")
            return {
                "response": json.loads(row[0]),
                "model": row[1],
                "cost_usd": row[2],
                "created_at": row[3],
            }
        
        return None
    
    async def set(
        self,
        image_bytes: bytes,
        capability: str,
        response: Any,
        model: str,
        cost_usd: float,
    ):
        """
        Cache result for image.
        
        Args:
            image_bytes: Image bytes (will be hashed)
            capability: LLM capability name
            response: Result to cache
            model: Model that produced result
            cost_usd: Cost of the call
        """
        if not IMAGEHASH_AVAILABLE:
            return  # No caching without imagehash
        
        try:
            img_hash = self.hasher.compute_hash(image_bytes)
        except Exception as e:
            logger.warning(f"Failed to compute image hash for caching: {e}")
            return
        
        import json
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=self.ttl_days)
        
        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO vision_cache
            (image_hash, capability, response, model, cost_usd, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                img_hash,
                capability,
                json.dumps(response),
                model,
                cost_usd,
                now.isoformat(),
                expires.isoformat(),
            )
        )
        conn.commit()
    
    def clear_expired(self):
        """Remove expired entries."""
        conn = self._get_conn()
        conn.execute("DELETE FROM vision_cache WHERE expires_at < datetime('now')")
        conn.commit()
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        conn = self._get_conn()
        
        total = conn.execute("SELECT COUNT(*) FROM vision_cache").fetchone()[0]
        by_capability = {}
        for row in conn.execute(
            "SELECT capability, COUNT(*) FROM vision_cache GROUP BY capability"
        ).fetchall():
            by_capability[row[0]] = row[1]
        
        return {
            "total_entries": total,
            "by_capability": by_capability,
        }
