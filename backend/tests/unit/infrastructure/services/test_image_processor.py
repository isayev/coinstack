"""
Unit tests for image processor.

Tests image validation, preprocessing, and perceptual hashing.
"""

import base64
import io
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Check if Pillow is available
pillow_available = True
try:
    from PIL import Image
except ImportError:
    pillow_available = False

# Import with graceful degradation
pytest.importorskip("src.infrastructure.services.image_processor")

from src.infrastructure.services.image_processor import (
    ImageConfig,
    ImageProcessor,
    ImageHasher,
    VisionCache,
    InvalidImageFormat,
    ImageTooLarge,
    ImageDimensionsTooLarge,
    PillowNotAvailable,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database path."""
    return str(tmp_path / "test_vision_cache.sqlite")


@pytest.fixture
def test_jpeg_bytes():
    """Create a minimal valid JPEG image."""
    if not pillow_available:
        pytest.skip("Pillow not available")
    
    img = Image.new("RGB", (100, 100), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def test_png_bytes():
    """Create a minimal valid PNG image."""
    if not pillow_available:
        pytest.skip("Pillow not available")
    
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def large_image_bytes():
    """Create a large image (3000x3000)."""
    if not pillow_available:
        pytest.skip("Pillow not available")
    
    img = Image.new("RGB", (3000, 3000), color="green")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=50)
    return buffer.getvalue()


@pytest.fixture
def processor():
    """Create image processor instance."""
    return ImageProcessor()


# =============================================================================
# IMAGE CONFIG TESTS
# =============================================================================

class TestImageConfig:
    """Tests for ImageConfig dataclass."""
    
    def test_default_config(self):
        """ImageConfig should have sensible defaults."""
        config = ImageConfig()
        
        assert config.max_size_mb == 10.0
        assert config.max_dimension_px == 4096
        assert config.resize_max_dimension == 2048
        assert "jpeg" in config.accepted_formats
        assert config.output_format == "jpeg"
    
    def test_frozen(self):
        """ImageConfig should be immutable."""
        config = ImageConfig()
        with pytest.raises(AttributeError):
            config.max_size_mb = 20.0  # type: ignore


# =============================================================================
# IMAGE PROCESSOR TESTS
# =============================================================================

@pytest.mark.skipif(not pillow_available, reason="Pillow not available")
class TestImageProcessor:
    """Tests for ImageProcessor."""
    
    def test_validate_valid_jpeg(self, processor, test_jpeg_bytes):
        """Processor should accept valid JPEG."""
        # Should not raise
        processor.validate(test_jpeg_bytes, "test.jpg")
    
    def test_validate_valid_png(self, processor, test_png_bytes):
        """Processor should accept valid PNG."""
        processor.validate(test_png_bytes, "test.png")
    
    def test_validate_too_large(self, processor):
        """Processor should reject files over size limit."""
        # Create bytes larger than 10MB
        large_bytes = b"x" * (11 * 1024 * 1024)
        
        with pytest.raises(ImageTooLarge) as exc:
            processor.validate(large_bytes, "test.jpg")
        
        assert exc.value.actual_mb > 10
    
    def test_validate_invalid_format(self, processor):
        """Processor should reject invalid formats."""
        with pytest.raises(InvalidImageFormat):
            processor.validate(b"not an image", "test.txt")
    
    def test_preprocess_resize(self, processor, large_image_bytes):
        """Processor should resize large images."""
        result = processor.preprocess(large_image_bytes)
        
        # Verify result is smaller
        assert len(result) < len(large_image_bytes)
        
        # Verify dimensions
        img = Image.open(io.BytesIO(result))
        assert max(img.size) <= processor.config.resize_max_dimension
    
    def test_preprocess_convert_to_jpeg(self, processor, test_png_bytes):
        """Processor should convert to JPEG."""
        result = processor.preprocess(test_png_bytes)
        
        # Verify it's JPEG
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"
    
    def test_to_base64(self, processor, test_jpeg_bytes):
        """Processor should encode to base64."""
        result = processor.to_base64(test_jpeg_bytes, preprocess=False)
        
        # Verify it's valid base64
        decoded = base64.b64decode(result)
        assert decoded == test_jpeg_bytes
    
    def test_from_base64(self, processor, test_jpeg_bytes):
        """Processor should decode from base64."""
        b64 = base64.b64encode(test_jpeg_bytes).decode()
        result = processor.from_base64(b64)
        
        assert result == test_jpeg_bytes
    
    def test_concatenate_horizontal(self, processor, test_jpeg_bytes):
        """Processor should concatenate images horizontally."""
        result = processor.concatenate_images(
            [test_jpeg_bytes, test_jpeg_bytes],
            direction="horizontal"
        )
        
        img = Image.open(io.BytesIO(result))
        # Combined should be wider
        assert img.width > 100
    
    def test_concatenate_vertical(self, processor, test_jpeg_bytes):
        """Processor should concatenate images vertically."""
        result = processor.concatenate_images(
            [test_jpeg_bytes, test_jpeg_bytes],
            direction="vertical"
        )
        
        img = Image.open(io.BytesIO(result))
        # Combined should be taller
        assert img.height > 100


# =============================================================================
# IMAGE HASHER TESTS
# =============================================================================

@pytest.mark.skipif(not pillow_available, reason="Pillow not available")
class TestImageHasher:
    """Tests for ImageHasher."""
    
    def test_compute_hash(self, test_jpeg_bytes):
        """Hasher should compute hash."""
        # Skip if imagehash not available
        try:
            hasher = ImageHasher()
            hash_str = hasher.compute_hash(test_jpeg_bytes)
        except Exception as e:
            if "imagehash" in str(e).lower():
                pytest.skip("imagehash not available")
            raise
        
        assert isinstance(hash_str, str)
        assert len(hash_str) > 0
    
    def test_same_image_same_hash(self, test_jpeg_bytes):
        """Same image should produce same hash."""
        try:
            hasher = ImageHasher()
            hash1 = hasher.compute_hash(test_jpeg_bytes)
            hash2 = hasher.compute_hash(test_jpeg_bytes)
        except Exception as e:
            if "imagehash" in str(e).lower():
                pytest.skip("imagehash not available")
            raise
        
        assert hash1 == hash2
    
    def test_different_images_different_hash(self):
        """Different images should produce different hashes."""
        try:
            import imagehash
        except ImportError:
            pytest.skip("imagehash not available")
        
        hasher = ImageHasher()
        
        # Create distinctly different images (not just solid colors)
        # Image 1: Gradient
        img1 = Image.new("RGB", (100, 100))
        for x in range(100):
            for y in range(100):
                img1.putpixel((x, y), (x * 2, y * 2, 128))
        buffer1 = io.BytesIO()
        img1.save(buffer1, format="JPEG")
        bytes1 = buffer1.getvalue()
        
        # Image 2: Opposite gradient
        img2 = Image.new("RGB", (100, 100))
        for x in range(100):
            for y in range(100):
                img2.putpixel((x, y), (255 - x * 2, 255 - y * 2, 64))
        buffer2 = io.BytesIO()
        img2.save(buffer2, format="JPEG")
        bytes2 = buffer2.getvalue()
        
        hash1 = hasher.compute_hash(bytes1)
        hash2 = hasher.compute_hash(bytes2)
        
        # Different patterns should produce different hashes
        assert hash1 != hash2
    
    def test_is_similar_identical(self, test_jpeg_bytes):
        """Identical images should be similar."""
        try:
            hasher = ImageHasher()
            hash1 = hasher.compute_hash(test_jpeg_bytes)
        except Exception as e:
            if "imagehash" in str(e).lower():
                pytest.skip("imagehash not available")
            raise
        
        assert hasher.is_similar(hash1, hash1, threshold=10)
    
    def test_resized_image_similar_hash(self, test_jpeg_bytes):
        """Resized image should have similar hash (within threshold)."""
        try:
            import imagehash
        except ImportError:
            pytest.skip("imagehash not available")
        
        hasher = ImageHasher()
        
        # Original hash
        hash1 = hasher.compute_hash(test_jpeg_bytes)
        
        # Resize the image
        img = Image.open(io.BytesIO(test_jpeg_bytes))
        resized = img.resize((50, 50))
        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG")
        resized_bytes = buffer.getvalue()
        
        hash2 = hasher.compute_hash(resized_bytes)
        
        # Should be similar (within threshold)
        distance = hasher.hamming_distance(hash1, hash2)
        assert distance < 20  # Reasonably similar


# =============================================================================
# VISION CACHE TESTS
# =============================================================================

@pytest.mark.skipif(not pillow_available, reason="Pillow not available")
class TestVisionCache:
    """Tests for VisionCache."""
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, temp_db, test_jpeg_bytes):
        """Cache should return None on miss."""
        try:
            import imagehash
        except ImportError:
            pytest.skip("imagehash not available")
        
        cache = VisionCache(temp_db)
        result = await cache.get(test_jpeg_bytes, "image_identify")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, temp_db, test_jpeg_bytes):
        """Cache should return stored result."""
        try:
            import imagehash
        except ImportError:
            pytest.skip("imagehash not available")
        
        cache = VisionCache(temp_db)
        
        # Store result
        response = {
            "ruler": "Trajan",
            "denomination": "Denarius",
            "confidence": 0.85
        }
        await cache.set(
            test_jpeg_bytes,
            "image_identify",
            response,
            "gemini-pro",
            0.01
        )
        
        # Retrieve
        result = await cache.get(test_jpeg_bytes, "image_identify")
        
        assert result is not None
        assert result["response"]["ruler"] == "Trajan"
        assert result["model"] == "gemini-pro"
    
    @pytest.mark.asyncio
    async def test_different_capability_miss(self, temp_db, test_jpeg_bytes):
        """Different capability should miss cache."""
        try:
            import imagehash
        except ImportError:
            pytest.skip("imagehash not available")
        
        cache = VisionCache(temp_db)
        
        # Store for one capability
        await cache.set(
            test_jpeg_bytes,
            "image_identify",
            {"test": "data"},
            "model",
            0.0
        )
        
        # Different capability should miss
        result = await cache.get(test_jpeg_bytes, "legend_transcribe")
        assert result is None
    
    def test_get_stats(self, temp_db, test_jpeg_bytes):
        """Cache should return stats."""
        try:
            import imagehash
        except ImportError:
            pytest.skip("imagehash not available")
        
        cache = VisionCache(temp_db)
        stats = cache.get_stats()
        
        assert "total_entries" in stats
        assert "by_capability" in stats
