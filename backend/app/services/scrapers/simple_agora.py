"""Agora Auctions scraper for agoraauctions.com."""

import re
import logging
from datetime import datetime
from bs4 import BeautifulSoup

from .base import AuctionScraperBase, LotData, ScrapeResult

logger = logging.getLogger(__name__)


class AgoraScraper(AuctionScraperBase):
    """
    Scraper for Agora Auctions (agoraauctions.com).
    
    Agora specializes in ancient and world coins.
    URL format: https://agoraauctions.com/listing/viewdetail/{lot_id}/0/archive
    """
    
    HOUSE = "Agora"
    BASE_URL = "https://agoraauctions.com"
    URL_PATTERNS = ["agoraauctions.com", "agora-auctions"]
    
    def parse_lot_id(self, url: str) -> str | None:
        """Extract lot ID from Agora URL."""
        # Main format: /listing/viewdetail/60751/0/archive
        match = re.search(r'/listing/viewdetail/(\d+)', url)
        if match:
            return match.group(1)
        
        # Alternative: /lot/12345
        match = re.search(r'/lot/(\d+)', url)
        if match:
            return match.group(1)
        
        # Alternative with auction ID
        match = re.search(r'/auction/(\d+)/lot/(\d+)', url)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        
        return None
    
    async def extract_lot(self, url: str) -> ScrapeResult:
        """Extract lot data from Agora auction page."""
        start_time = datetime.utcnow()
        
        html, status_code = await self._fetch_page(url)
        elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if not html:
            return ScrapeResult(
                status="error",
                url=url,
                house=self.HOUSE,
                error_message=f"Failed to fetch page (status: {status_code})",
                http_status=status_code,
                elapsed_ms=elapsed_ms,
            )
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            lot_id = self.parse_lot_id(url)
            
            # Extract title from h1 (format: "Lot 269. Trajan Decius...")
            title = None
            lot_number = None
            title_elem = soup.select_one('h1')
            if title_elem:
                title_text = self._clean_text(title_elem.get_text())
                # Remove "Lot X." prefix and extract lot number
                lot_match = re.match(r'Lot\s*(\d+)\.?\s*(.*)', title_text, re.I)
                if lot_match:
                    lot_number = lot_match.group(1)
                    title = lot_match.group(2).strip()
                else:
                    title = title_text
            
            # Extract description from h3 or paragraphs following the title
            description = None
            desc_elem = soup.select_one('h3')
            if desc_elem:
                # Get full description text, skip the first part if it's just the title again
                desc_text = self._clean_text(desc_elem.get_text())
                # The h3 often contains lot number + title + description
                # Format: "Lot 269. Trajan Decius... AR antoninianus (22.8 mm, 3.59 g, 12 h). [description]"
                if desc_text:
                    # Extract everything after the title repeat
                    description = desc_text
            
            # Get full page text for regex searching
            page_text = soup.get_text()
            
            # Extract hammer/final price from page text
            hammer_price = None
            final_match = re.search(r'Final Price[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)', page_text, re.I)
            if final_match:
                hammer_price = self._parse_price(final_match.group(1))
            
            # Extract estimates from page text
            estimate_low = None
            estimate_high = None
            
            # Single estimate format: "Estimate: $ 75.00"
            est_match = re.search(r'Estimate[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)', page_text, re.I)
            if est_match:
                estimate_low = self._parse_price(est_match.group(1))
                estimate_high = estimate_low
            
            # Range estimate format: "$50 - $100"
            range_match = re.search(r'Estimate[:\s]*\$?\s*([\d,]+)\s*[-–]\s*\$?\s*([\d,]+)', page_text, re.I)
            if range_match:
                estimate_low = self._parse_price(range_match.group(1))
                estimate_high = self._parse_price(range_match.group(2))
            
            # Currency (Agora uses USD)
            currency = "USD"
            
            # Extract auction date from "Bidding Ends:" section
            auction_date = None
            for elem in soup.find_all(string=re.compile(r'Bidding Ends', re.I)):
                parent = elem.parent
                if parent:
                    date_text = parent.find_next(string=True)
                    if date_text:
                        auction_date = self._parse_date(date_text.strip())
                    break
            
            # Extract photos - look for lot_images in src
            photos = []
            primary_photo = None
            
            for img in soup.select('img[src*="lot_images"]'):
                src = img.get('src')
                if src:
                    if src.startswith('/'):
                        src = self.BASE_URL + src
                    if 'loading' not in src.lower() and 'placeholder' not in src.lower():
                        if src not in photos:
                            photos.append(src)
            
            # Also check for links to lot_images (full-size versions)
            for a in soup.select('a[href*="lot_images"]'):
                href = a.get('href')
                if href:
                    if href.startswith('/'):
                        href = self.BASE_URL + href
                    if href not in photos:
                        photos.insert(0, href)  # Full-size first
            
            if photos:
                primary_photo = photos[0]
            
            # Extract physical properties from page text
            # Format: (22.8 mm, 3.59 g, 12 h)
            weight_g = None
            diameter_mm = None
            die_axis = None
            
            physical_match = re.search(r'\((\d+\.?\d*)\s*mm,?\s*(\d+\.?\d*)\s*g,?\s*(\d+)\s*h\)', page_text)
            if physical_match:
                diameter_mm = float(physical_match.group(1))
                weight_g = float(physical_match.group(2))
                die_axis = int(physical_match.group(3))
            else:
                # Try individual patterns
                diam_match = re.search(r'(\d+\.?\d*)\s*mm\b', page_text, re.I)
                if diam_match:
                    diameter_mm = float(diam_match.group(1))
                
                weight_match = re.search(r'(\d+\.?\d*)\s*(?:gm|g|grams?)\b', page_text, re.I)
                if weight_match:
                    weight_g = float(weight_match.group(1))
            
            # Extract catalog references (RIC, etc.) from page text
            references = []
            ref_patterns = [
                (r'RIC\s+(\d+[a-z]?)', 'RIC'),
                (r'RRC\s+(\d+/\d+)', 'RRC'),
                (r'RSC\s+(\d+[a-z]?)', 'RSC'),
                (r'Sear\s+(\d+)', 'Sear'),
                (r'BMC\s+(\d+)', 'BMC'),
            ]
            for pattern, catalog in ref_patterns:
                for match in re.finditer(pattern, page_text, re.I):
                    references.append(f"{catalog} {match.group(1)}")
            
            # Extract grading info from page text
            grade = None
            grade_service = None
            cert_number = None
            
            if 'NGC' in page_text.upper():
                grade_service = 'NGC'
                grade_match = re.search(r'NGC\s+([\w\s\d/*+-]+?)(?:\s+\d{7,})?(?:\s|,|$)', page_text, re.I)
                if grade_match:
                    grade = self._clean_text(grade_match.group(1))
            elif 'PCGS' in page_text.upper():
                grade_service = 'PCGS'
                grade_match = re.search(r'PCGS\s+([\w\s\d/*+-]+?)(?:\s+\d{7,})?(?:\s|,|$)', page_text, re.I)
                if grade_match:
                    grade = self._clean_text(grade_match.group(1))
            
            # Certification number
            cert_match = re.search(r'(\d{7,})', page_text)
            if cert_match and grade_service:
                cert_number = cert_match.group(1)
            
            lot_data = LotData(
                lot_id=lot_id or url,
                house=self.HOUSE,
                url=url,
                hammer_price=hammer_price,
                estimate_low=estimate_low,
                estimate_high=estimate_high,
                currency=currency,
                sold=bool(hammer_price),
                sale_name=None,
                lot_number=lot_number,
                auction_date=auction_date,
                title=title,
                description=description,
                grade=grade,
                grade_service=grade_service,
                certification_number=cert_number,
                weight_g=weight_g,
                diameter_mm=diameter_mm,
                die_axis=die_axis,
                photos=photos,
                primary_photo_url=primary_photo,
                catalog_refs=references if references else None,
                fetched_at=datetime.utcnow(),
            )
            
            status = "success" if (hammer_price or title) and photos else "partial"
            
            return ScrapeResult(
                status=status,
                lot_data=lot_data,
                url=url,
                house=self.HOUSE,
                http_status=status_code,
                elapsed_ms=elapsed_ms,
            )
            
        except Exception as e:
            logger.exception(f"Error parsing Agora page {url}")
            return ScrapeResult(
                status="error",
                url=url,
                house=self.HOUSE,
                error_message=str(e),
                http_status=status_code,
                elapsed_ms=elapsed_ms,
            )
