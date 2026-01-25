"""
Agora Parser

Extracts structured coin data from Agora Auctions pages.
"""

import re
from typing import Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from .models import AgoraCoinData, AgoraPhysicalData

logger = logging.getLogger(__name__)

class AgoraParser:
    """Parser for Agora Auctions"""
    
    BASE_URL = "https://agoraauctions.com"
    
    def parse(self, html: str, url: str) -> AgoraCoinData:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract ID
        lot_id = self._extract_lot_id(url)
        
        # Title & Lot Number
        title = ""
        lot_number = None
        title_elem = soup.select_one('h1')
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            lot_match = re.match(r'Lot\s*(\d+)\.?\s*(.*)', title_text, re.I)
            if lot_match:
                lot_number = lot_match.group(1)
                title = lot_match.group(2).strip()
            else:
                title = title_text
        
        # Description
        description = None
        desc_elem = soup.select('h3')
        # Usually it's in an h3, but sometimes there are multiple.
        # We look for the one that seems to contain description text
        for elem in desc_elem:
            text = elem.get_text(strip=True)
            if len(text) > 50 and text != title:
                description = text
                break
        
        page_text = soup.get_text()
        
        # Pricing
        hammer_price = None
        final_match = re.search(r'Final Price[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)', page_text, re.I)
        if final_match:
            hammer_price = self._parse_price(final_match.group(1))
            
        estimate_low = None
        estimate_high = None
        
        est_match = re.search(r'Estimate[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)', page_text, re.I)
        if est_match:
            estimate_low = self._parse_price(est_match.group(1))
            estimate_high = estimate_low
            
        range_match = re.search(r'Estimate[:\s]*\$?\s*([\d,]+)\s*[-–]\s*\$?\s*([\d,]+)', page_text, re.I)
        if range_match:
            estimate_low = self._parse_price(range_match.group(1))
            estimate_high = self._parse_price(range_match.group(2))
            
        # Auction Date
        auction_date = None
        for elem in soup.find_all(string=re.compile(r'Bidding Ends', re.I)):
            parent = elem.parent
            if parent:
                date_text = parent.find_next(string=True)
                if date_text:
                    try:
                         # Attempt to parse date, format may vary so careful
                         # Often: "Tue, 12 Oct 2023 12:00:00 EST"
                         date_str = date_text.strip()
                         # TODO: Implement actual date parsing logic
                         pass
                    except Exception as e:
                        logger.warning(f"Failed to parse auction date '{date_text}': {type(e).__name__}: {str(e)}")
                    break
        
        # Images
        photos = []
        for img in soup.select('img[src*="lot_images"]'):
            src = img.get('src')
            if src:
                if src.startswith('/'):
                    src = self.BASE_URL + src
                if 'loading' not in src.lower() and 'placeholder' not in src.lower():
                    if src not in photos:
                        photos.append(src)
        
        primary_photo = photos[0] if photos else None
        
        # Physical
        physical = self._parse_physical(page_text)
        
        # References
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
        
        # Grading
        grade = None
        grade_service = None
        cert_number = None
        
        if 'NGC' in page_text.upper():
            grade_service = 'NGC'
            grade_match = re.search(r'NGC\s+([\w\s\d/*+-]+?)(?:\s+\d{7,})?(?:\s|,|$)', page_text, re.I)
            if grade_match:
                grade = grade_match.group(1).strip()
        elif 'PCGS' in page_text.upper():
            grade_service = 'PCGS'
            grade_match = re.search(r'PCGS\s+([\w\s\d/*+-]+?)(?:\s+\d{7,})?(?:\s|,|$)', page_text, re.I)
            if grade_match:
                grade = grade_match.group(1).strip()
                
        cert_match = re.search(r'(\d{7,})', page_text)
        if cert_match and grade_service:
            cert_number = cert_match.group(1)
            
        return AgoraCoinData(
            agora_lot_id=str(lot_id) if lot_id else "unknown",
            url=url,
            title=title,
            description=description,
            lot_number=lot_number,
            auction_date=auction_date,
            estimate_low=estimate_low,
            estimate_high=estimate_high,
            hammer_price=hammer_price,
            physical=physical,
            grade=grade,
            grade_service=grade_service,
            certification_number=cert_number,
            references=references,
            photos=photos,
            primary_photo_url=primary_photo
        )

    def _extract_lot_id(self, url: str) -> Optional[str]:
        match = re.search(r'/listing/viewdetail/(\d+)', url)
        if match: return match.group(1)
        match = re.search(r'/lot/(\d+)', url)
        if match: return match.group(1)
        return None

    def _parse_price(self, price_str: str) -> Optional[float]:
        try:
            return float(price_str.replace(',', '').replace('$', ''))
        except (ValueError, AttributeError) as e:
            logger.debug(f"Failed to parse price '{price_str}': {type(e).__name__}")
            return None

    def _parse_physical(self, text: str) -> AgoraPhysicalData:
        diameter = None
        weight = None
        die_axis = None
        
        physical_match = re.search(r'\((\d+\.?\d*)\s*mm,?\s*(\d+\.?\d*)\s*g,?\s*(\d+)\s*h\)', text)
        if physical_match:
            diameter = float(physical_match.group(1))
            weight = float(physical_match.group(2))
            die_axis = int(physical_match.group(3))
        else:
            diam_match = re.search(r'(\d+\.?\d*)\s*mm\b', text, re.I)
            if diam_match: diameter = float(diam_match.group(1))
            
            weight_match = re.search(r'(\d+\.?\d*)\s*(?:gm|g|grams?)\b', text, re.I)
            if weight_match: weight = float(weight_match.group(1))
            
        return AgoraPhysicalData(
            diameter_mm=diameter,
            weight_g=weight,
            die_axis=die_axis
        )
