"""
Auction image handler with perceptual hash deduplication.

Downloads images from auction sources, deduplicates using perceptual hashing,
and tracks image provenance across multiple auction appearances.
"""

import os
import hashlib
import logging
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.models.image import CoinImage, ImageType
from app.models.image_source import ImageAuctionSource
from app.models.auction_data import AuctionData
from app.config import get_settings

logger = logging.getLogger(__name__)

# Try to import imagehash, gracefully degrade if not available
try:
    import imagehash
    from PIL import Image
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False
    logger.warning("imagehash/Pillow not installed - image deduplication disabled")


class AuctionImageHandler:
    """
    Handles downloading and deduplicating images from auction sources.
    
    Features:
    - Downloads images from auction URLs
    - Calculates perceptual hash for deduplication
    - Tracks multiple auction sources per image
    - Classifies images as obverse/reverse/other
    """
    
    TIMEOUT = 30.0
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Maximum hamming distance for perceptual hash to consider images identical
    PHASH_THRESHOLD = 5
    
    def __init__(self, db: Session):
        self.db = db
        settings = get_settings()
        self.upload_dir = Path(settings.UPLOAD_DIR)
    
    async def download_auction_images(
        self,
        coin_id: int,
        auction_data_id: int,
    ) -> list[CoinImage]:
        """
        Download all images from an auction record.
        
        Handles deduplication - if an image already exists (by perceptual hash),
        just links it to this auction source instead of downloading again.
        
        Args:
            coin_id: ID of coin to link images to
            auction_data_id: ID of auction data record
            
        Returns:
            List of CoinImage records (created or existing)
        """
        auction = self.db.query(AuctionData).filter(
            AuctionData.id == auction_data_id
        ).first()
        
        if not auction:
            raise ValueError(f"Auction data {auction_data_id} not found")
        
        image_urls = self._extract_image_urls(auction)
        if not image_urls:
            logger.info(f"No images found for auction {auction_data_id}")
            return []
        
        downloaded = []
        
        for idx, url in enumerate(image_urls):
            try:
                image = await self._process_image(
                    coin_id=coin_id,
                    auction=auction,
                    url=url,
                    index=idx,
                    total=len(image_urls),
                )
                if image:
                    downloaded.append(image)
            except Exception as e:
                logger.error(f"Failed to process image {url}: {e}")
                continue
        
        return downloaded
    
    async def _process_image(
        self,
        coin_id: int,
        auction: AuctionData,
        url: str,
        index: int,
        total: int,
    ) -> CoinImage | None:
        """
        Process a single image URL.
        
        Downloads, hashes, checks for duplicates, and saves if new.
        """
        # Download to temp file
        temp_path = await self._download_to_temp(url)
        if not temp_path:
            return None
        
        try:
            # Calculate perceptual hash
            phash = self._calculate_phash(temp_path) if IMAGEHASH_AVAILABLE else None
            
            # Check for existing image with similar hash
            if phash:
                existing = await self._find_by_phash(coin_id, phash)
                if existing:
                    # Just add auction source to existing image
                    await self._add_auction_source(
                        existing.id,
                        auction.id,
                        url,
                        auction.auction_house,
                    )
                    logger.info(f"Image already exists (phash match): {existing.id}")
                    return existing
            
            # New image - get dimensions and save
            width, height = self._get_image_dimensions(temp_path)
            mime_type = self._detect_mime_type(temp_path)
            
            # Generate final path
            final_path = self._generate_path(coin_id, auction.id, url, index)
            final_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move temp file to final location
            shutil.move(temp_path, str(final_path))
            temp_path = None  # Don't delete in finally
            
            # Determine image type
            image_type = self._classify_image(index, total)
            
            # Check if this should be primary
            is_primary = await self._should_be_primary(coin_id, image_type)
            
            # Create database record
            image = CoinImage(
                coin_id=coin_id,
                image_type=image_type,
                file_path=str(final_path.relative_to(self.upload_dir.parent)),
                file_name=final_path.name,
                mime_type=mime_type,
                size_bytes=final_path.stat().st_size,
                width=width,
                height=height,
                is_primary=is_primary,
                perceptual_hash=phash,
                source_url=url,
                source_auction_id=auction.id,
                source_house=auction.auction_house,
                downloaded_at=datetime.utcnow(),
            )
            
            self.db.add(image)
            self.db.commit()
            self.db.refresh(image)
            
            # Add auction source record
            await self._add_auction_source(
                image.id,
                auction.id,
                url,
                auction.auction_house,
            )
            
            logger.info(f"Downloaded new image: {image.id} from {url}")
            return image
            
        finally:
            # Clean up temp file if still exists
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
    
    def _extract_image_urls(self, auction: AuctionData) -> list[str]:
        """Extract image URLs from auction record."""
        urls = []
        
        # Primary photo URL
        if auction.primary_photo_url:
            urls.append(auction.primary_photo_url)
        
        # Photos array (JSON)
        if auction.photos:
            if isinstance(auction.photos, list):
                for photo in auction.photos:
                    if isinstance(photo, str) and photo not in urls:
                        urls.append(photo)
                    elif isinstance(photo, dict) and photo.get("url"):
                        if photo["url"] not in urls:
                            urls.append(photo["url"])
        
        return urls
    
    async def _download_to_temp(self, url: str) -> str | None:
        """Download image to temporary file."""
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "image/*",
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get("content-type", "")
                if not content_type.startswith("image/"):
                    logger.warning(f"Not an image: {url} (content-type: {content_type})")
                    return None
                
                # Save to temp file
                suffix = self._get_extension_from_url(url) or ".jpg"
                fd, temp_path = tempfile.mkstemp(suffix=suffix)
                
                with os.fdopen(fd, 'wb') as f:
                    f.write(response.content)
                
                return temp_path
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout downloading {url}")
            return None
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error downloading {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None
    
    def _calculate_phash(self, path: str) -> str | None:
        """Calculate perceptual hash for image."""
        if not IMAGEHASH_AVAILABLE:
            return None
        
        try:
            img = Image.open(path)
            phash = imagehash.phash(img)
            return str(phash)
        except Exception as e:
            logger.warning(f"Failed to calculate phash: {e}")
            return None
    
    async def _find_by_phash(self, coin_id: int, phash: str) -> CoinImage | None:
        """Find existing image with similar perceptual hash."""
        if not IMAGEHASH_AVAILABLE or not phash:
            return None
        
        # Get all images for this coin with perceptual hashes
        images = self.db.query(CoinImage).filter(
            CoinImage.coin_id == coin_id,
            CoinImage.perceptual_hash.isnot(None),
        ).all()
        
        try:
            new_hash = imagehash.hex_to_hash(phash)
            
            for img in images:
                if img.perceptual_hash:
                    existing_hash = imagehash.hex_to_hash(img.perceptual_hash)
                    distance = new_hash - existing_hash
                    if distance <= self.PHASH_THRESHOLD:
                        return img
        except Exception as e:
            logger.warning(f"Error comparing phashes: {e}")
        
        return None
    
    async def _add_auction_source(
        self,
        image_id: int,
        auction_data_id: int,
        source_url: str,
        source_house: str | None,
    ):
        """Add auction source record for an image."""
        # Check if already linked
        existing = self.db.query(ImageAuctionSource).filter(
            ImageAuctionSource.image_id == image_id,
            ImageAuctionSource.auction_data_id == auction_data_id,
        ).first()
        
        if existing:
            return
        
        source = ImageAuctionSource(
            image_id=image_id,
            auction_data_id=auction_data_id,
            source_url=source_url,
            source_house=source_house,
            fetched_at=datetime.utcnow(),
        )
        
        self.db.add(source)
        self.db.commit()
    
    def _get_image_dimensions(self, path: str) -> tuple[int, int]:
        """Get image width and height."""
        if IMAGEHASH_AVAILABLE:
            try:
                with Image.open(path) as img:
                    return img.size
            except Exception:
                pass
        return (0, 0)
    
    def _detect_mime_type(self, path: str) -> str:
        """Detect MIME type from file."""
        # Simple detection based on magic bytes
        with open(path, 'rb') as f:
            header = f.read(16)
        
        if header.startswith(b'\xff\xd8\xff'):
            return "image/jpeg"
        elif header.startswith(b'\x89PNG\r\n\x1a\n'):
            return "image/png"
        elif header.startswith(b'GIF8'):
            return "image/gif"
        elif header.startswith(b'RIFF') and header[8:12] == b'WEBP':
            return "image/webp"
        
        return "image/jpeg"  # Default
    
    def _get_extension_from_url(self, url: str) -> str:
        """Get file extension from URL."""
        path = url.split('?')[0].split('#')[0]
        
        if path.lower().endswith('.png'):
            return '.png'
        elif path.lower().endswith('.gif'):
            return '.gif'
        elif path.lower().endswith('.webp'):
            return '.webp'
        
        return '.jpg'
    
    def _generate_path(
        self,
        coin_id: int,
        auction_id: int,
        url: str,
        index: int,
    ) -> Path:
        """Generate unique file path for image."""
        # Create hash of URL for unique filename
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        extension = self._get_extension_from_url(url)
        
        filename = f"auction_{auction_id}_{index}_{url_hash}{extension}"
        
        # Organize by coin ID
        return self.upload_dir / "coins" / str(coin_id) / filename
    
    def _classify_image(self, index: int, total: int) -> ImageType:
        """Classify image type based on position in listing."""
        if total >= 2:
            if index == 0:
                return ImageType.OBVERSE
            elif index == 1:
                return ImageType.REVERSE
        
        return ImageType.OTHER
    
    async def _should_be_primary(self, coin_id: int, image_type: ImageType) -> bool:
        """Check if this image should be marked as primary."""
        # Primary if it's an obverse and no primary exists
        if image_type == ImageType.OBVERSE:
            existing_primary = self.db.query(CoinImage).filter(
                CoinImage.coin_id == coin_id,
                CoinImage.is_primary == True,
            ).first()
            
            return existing_primary is None
        
        return False
    
    # =========================================================================
    # Bulk Operations
    # =========================================================================
    
    async def download_all_auction_images(
        self,
        coin_id: int,
    ) -> dict:
        """
        Download images from all auction records linked to a coin.
        
        Returns:
            Summary of download results
        """
        auctions = self.db.query(AuctionData).filter(
            AuctionData.coin_id == coin_id
        ).all()
        
        total_downloaded = 0
        total_skipped = 0
        errors = 0
        
        for auction in auctions:
            try:
                images = await self.download_auction_images(coin_id, auction.id)
                total_downloaded += len([i for i in images if i.downloaded_at])
                total_skipped += len([i for i in images if not i.downloaded_at])
            except Exception as e:
                logger.error(f"Error downloading images from auction {auction.id}: {e}")
                errors += 1
        
        return {
            "coin_id": coin_id,
            "auctions_processed": len(auctions),
            "images_downloaded": total_downloaded,
            "duplicates_skipped": total_skipped,
            "errors": errors,
        }
