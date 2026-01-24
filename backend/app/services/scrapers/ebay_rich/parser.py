"""
eBay Parser

Extracts structured coin data from eBay listing pages.
Handles various eBay page formats and extracts item specifics.
"""

import re
import json
from typing import Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from .models import (
    EbayCoinData, EbayPhysicalData, EbayCatalogReference,
    EbayImage, EbayListingInfo, EbaySellerInfo, EbayGradingInfo,
    EbayListingType, EbayCondition
)

logger = logging.getLogger(__name__)


class EbayParser:
    """
    Parser for eBay listing pages.
    
    Extracts data from:
    - Page HTML/DOM
    - JSON-LD structured data
    - Item specifics section
    """
    
    # Reference patterns
    REFERENCE_PATTERNS = [
        (re.compile(r'RIC\s+([IVX]+(?:\.\d)?)\s+(\d+[a-z]?)', re.I), 'RIC'),
        (re.compile(r'(?:Crawford|Cr\.?)\s*(\d+/\d+[a-z]?)', re.I), 'Crawford'),
        (re.compile(r'RSC\s+(\d+[a-z]?)', re.I), 'RSC'),
        (re.compile(r'RPC\s+([IVX]+)\s+(\d+)', re.I), 'RPC'),
        (re.compile(r'Sear\s+(\d+)', re.I), 'Sear'),
        (re.compile(r'SNG\s+(\w+)\s+(\d+)', re.I), 'SNG'),
        (re.compile(r'BMC\s+(\d+)', re.I), 'BMC'),
        (re.compile(r'Cohen\s+(\d+)', re.I), 'Cohen'),
        (re.compile(r'Sydenham\s+(\d+)', re.I), 'Sydenham'),
    ]
    
    # Grade patterns for slabbed coins
    SLAB_PATTERNS = [
        (r'\bNGC\s+([A-Z]{1,2}[\s-]?\d{1,2}(?:\s*[/*+-]\s*\d{1,2})?)\b', 'NGC'),
        (r'\bPCGS\s+([A-Z]{1,2}[\s-]?\d{1,2}(?:\s*[/*+-]\s*\d{1,2})?)\b', 'PCGS'),
        (r'\bANACS\s+([A-Z]{1,2}[\s-]?\d{1,2})\b', 'ANACS'),
        (r'\bICG\s+([A-Z]{1,2}[\s-]?\d{1,2})\b', 'ICG'),
    ]
    
    # Cert number patterns
    CERT_PATTERNS = [
        r'(?:cert(?:ification)?|#)\s*[:#]?\s*(\d{6,})',
        r'(\d{7,})',  # NGC/PCGS cert numbers are 7+ digits
    ]
    
    def __init__(self):
        self.soup: Optional[BeautifulSoup] = None
        self.json_ld: Optional[dict] = None
    
    def parse(self, html: str, url: str) -> EbayCoinData:
        """
        Parse eBay listing HTML into structured data.
        """
        self.soup = BeautifulSoup(html, 'html.parser')
        
        # Check for error pages first (item removed/expired)
        error_status = self._check_error_page()
        if error_status:
            logger.warning(f"eBay error page detected: {error_status}")
            item_id = self._extract_item_id(url)
            # Return minimal data with error indicator
            return EbayCoinData(
                ebay_item_id=item_id,
                url=url,
                title=f"[REMOVED] {error_status}",
                description=error_status,
                listing=EbayListingInfo(
                    item_id=item_id,
                    is_ended=True,
                ),
                seller=EbaySellerInfo(),
                images=[],
            )
        
        self._extract_json_ld()
        
        item_id = self._extract_item_id(url)
        title = self._extract_title()
        description = self._extract_description()
        item_specifics = self._extract_item_specifics()
        
        # Parse coin details from title and description
        combined_text = f"{title} {description} {' '.join(str(v) for v in item_specifics.values())}"
        coin_details = self._parse_coin_details(combined_text, item_specifics)
        physical = self._parse_physical(combined_text, item_specifics)
        references = self._extract_references(combined_text)
        grading = self._extract_grading(combined_text, item_specifics)
        
        # Listing info
        listing = self._parse_listing_info(url)
        
        # Seller info
        seller = self._parse_seller_info()
        
        # Images
        images = self._extract_images()
        
        return EbayCoinData(
            ebay_item_id=item_id,
            url=url,
            title=title,
            ruler=coin_details.get('ruler'),
            reign_dates=coin_details.get('reign_dates'),
            era=coin_details.get('era'),
            denomination=coin_details.get('denomination'),
            metal=coin_details.get('metal'),
            mint=coin_details.get('mint'),
            mint_date=coin_details.get('mint_date'),
            physical=physical,
            description=description,
            item_specifics=item_specifics,
            references=references,
            grading=grading,
            condition=coin_details.get('condition'),
            listing=listing,
            seller=seller,
            images=images,
        )
    
    def _check_error_page(self) -> Optional[str]:
        """
        Check if this is an error page (item removed, expired, etc.)
        
        Returns:
            Error message if error page detected, None otherwise
        """
        # Check for "We looked everywhere" error page
        error_h1 = self.soup.select_one('.error-header-v2__title, .error-header__title')
        if error_h1:
            text = error_h1.get_text(strip=True)
            if 'looked everywhere' in text.lower() or 'missing' in text.lower():
                return "Item removed or not found"
        
        # Check for error page title
        title_tag = self.soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True).lower()
            if 'error page' in title_text:
                return "Error page - item may be removed"
        
        # Check for "This listing has ended"
        ended_notice = self.soup.select_one('.ux-notice--attention, [data-testid="ux-call-out"]')
        if ended_notice:
            text = ended_notice.get_text(strip=True).lower()
            if 'ended' in text or 'no longer available' in text:
                return f"Listing ended: {text[:100]}"
        
        # Check for specific error containers
        error_content = self.soup.select_one('.error-page-v2__content, .error-content')
        if error_content:
            return "Item page not available"
        
        # Check for CAPTCHA/robot check
        if 'robot' in (self.soup.get_text() or '').lower()[:5000]:
            # Only flag if it's a blocking captcha, not just mention in page
            captcha_form = self.soup.select_one('#captcha, .captcha, [data-testid="captcha"]')
            if captcha_form:
                return "CAPTCHA/robot check required"
        
        return None
    
    def _extract_json_ld(self):
        """Extract JSON-LD structured data"""
        scripts = self.soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    self.json_ld = data
                    break
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            self.json_ld = item
                            break
            except (json.JSONDecodeError, TypeError):
                continue
    
    def _extract_item_id(self, url: str) -> str:
        """Extract eBay item ID from URL"""
        # Standard format: /itm/123456789 or /itm/title/123456789
        match = re.search(r'/itm/(?:[^/]+/)?(\d+)', url)
        if match:
            return match.group(1)
        
        # Query param format
        match = re.search(r'[?&]item=(\d+)', url)
        if match:
            return match.group(1)
        
        return ""
    
    def _extract_title(self) -> str:
        """Extract listing title"""
        # Try JSON-LD first
        if self.json_ld and self.json_ld.get('name'):
            return self.json_ld['name']
        
        # Try various title selectors
        selectors = [
            'h1.x-item-title__mainTitle',
            'h1[itemprop="name"]',
            '#itemTitle',
            'h1.product-title',
            '.x-item-title span',
        ]
        
        for sel in selectors:
            el = self.soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                # Remove "Details about" prefix
                text = re.sub(r'^Details about\s+', '', text)
                return text
        
        return ""
    
    def _extract_description(self) -> str:
        """Extract item description"""
        # Try JSON-LD
        if self.json_ld and self.json_ld.get('description'):
            return self.json_ld['description']
        
        # Description is often in an iframe, but we can try common selectors
        selectors = [
            '#desc_div',
            '.item-description',
            '[itemprop="description"]',
            '#viTabs_0_is',
        ]
        
        for sel in selectors:
            el = self.soup.select_one(sel)
            if el:
                return el.get_text(separator='\n', strip=True)[:5000]
        
        return ""
    
    def _extract_item_specifics(self) -> dict:
        """Extract eBay item specifics table"""
        specifics = {}
        
        # New format
        for row in self.soup.select('.ux-labels-values__labels-content'):
            label_el = row.select_one('.ux-labels-values__labels')
            value_el = row.select_one('.ux-labels-values__values')
            if label_el and value_el:
                label = label_el.get_text(strip=True).rstrip(':')
                value = value_el.get_text(strip=True)
                specifics[label] = value
        
        # Old format
        for row in self.soup.select('.itemAttr tr, .ux-layout-section--itemSpecifics tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).rstrip(':')
                value = cells[1].get_text(strip=True)
                if label and value:
                    specifics[label] = value
        
        # Also check labeled spans
        for container in self.soup.select('[data-testid="ux-labels-values"]'):
            label_el = container.select_one('.ux-textspans--BOLD')
            value_el = container.select_one('.ux-textspans:not(.ux-textspans--BOLD)')
            if label_el and value_el:
                label = label_el.get_text(strip=True).rstrip(':')
                value = value_el.get_text(strip=True)
                specifics[label] = value
        
        return specifics
    
    def _parse_coin_details(self, text: str, specifics: dict) -> dict:
        """Parse coin details from text and item specifics"""
        result = {}
        
        # Check item specifics first (more reliable structure)
        ruler_keys = ['Ruler', 'Emperor', 'King', 'Historical Period']
        for key in ruler_keys:
            if key in specifics:
                result['ruler'] = specifics[key]
                break
        
        # Era/Period
        era_keys = ['Era', 'Period', 'Historical Period', 'Civilization']
        for key in era_keys:
            if key in specifics:
                result['era'] = specifics[key]
                break
        
        # Metal
        metal_keys = ['Composition', 'Metal', 'Coin Type']
        for key in metal_keys:
            if key in specifics:
                result['metal'] = specifics[key]
                break
        
        # Denomination
        denom_keys = ['Denomination', 'Type']
        for key in denom_keys:
            if key in specifics:
                result['denomination'] = specifics[key]
                break
        
        # Mint
        if 'Mint Location' in specifics:
            result['mint'] = specifics['Mint Location']
        
        # Year/Date
        year_keys = ['Year', 'Date', 'Strike Year']
        for key in year_keys:
            if key in specifics:
                result['mint_date'] = specifics[key]
                break
        
        # Parse from text if not in specifics
        if 'ruler' not in result:
            # Common emperor names
            emperor_match = re.search(
                r'\b(Augustus|Tiberius|Caligula|Claudius|Nero|Vespasian|Titus|'
                r'Domitian|Nerva|Trajan|Hadrian|Antoninus Pius|Marcus Aurelius|'
                r'Commodus|Septimius Severus|Caracalla|Elagabalus|Severus Alexander|'
                r'Maximinus|Gordian|Philip|Decius|Gallienus|Aurelian|Diocletian|'
                r'Constantine|Julian|Theodosius)\b',
                text, re.I
            )
            if emperor_match:
                result['ruler'] = emperor_match.group(1)
        
        # Reign dates
        if 'reign_dates' not in result:
            dates_match = re.search(r'\b(AD|BC)\s*(\d+)\s*[-–]\s*(?:AD|BC)?\s*(\d+)\b', text)
            if dates_match:
                result['reign_dates'] = f"{dates_match.group(1)} {dates_match.group(2)}-{dates_match.group(3)}"
        
        # Era from text
        if 'era' not in result:
            if 'roman republic' in text.lower():
                result['era'] = 'Roman Republic'
            elif 'roman imperial' in text.lower() or 'roman empire' in text.lower():
                result['era'] = 'Roman Imperial'
            elif 'greek' in text.lower():
                result['era'] = 'Greek'
            elif 'byzantine' in text.lower():
                result['era'] = 'Byzantine'
        
        # Metal from text
        if 'metal' not in result:
            metal_patterns = {
                r'\b(gold|AV|aureus)\b': 'Gold',
                r'\b(silver|AR|denarius|drachm)\b': 'Silver',
                r'\b(bronze|AE|copper)\b': 'Bronze',
                r'\bbillon\b': 'Billon',
            }
            for pattern, metal in metal_patterns.items():
                if re.search(pattern, text, re.I):
                    result['metal'] = metal
                    break
        
        # Denomination from text
        if 'denomination' not in result:
            denom_match = re.search(
                r'\b(Denarius|Aureus|Sestertius|Dupondius|As|Antoninianus|'
                r'Solidus|Tremissis|Follis|Drachm|Tetradrachm|Stater|Obol)\b',
                text, re.I
            )
            if denom_match:
                result['denomination'] = denom_match.group(1)
        
        # Condition from item specifics
        condition_map = {
            'New': EbayCondition.NEW,
            'Like New': EbayCondition.LIKE_NEW,
            'Very Good': EbayCondition.VERY_GOOD,
            'Good': EbayCondition.GOOD,
            'Acceptable': EbayCondition.ACCEPTABLE,
            'Used': EbayCondition.USED,
        }
        if 'Condition' in specifics:
            cond_text = specifics['Condition']
            for key, val in condition_map.items():
                if key.lower() in cond_text.lower():
                    result['condition'] = val
                    break
        
        return result
    
    def _parse_physical(self, text: str, specifics: dict) -> EbayPhysicalData:
        """Parse physical measurements"""
        diameter_mm = None
        weight_g = None
        
        # Check item specifics
        if 'Diameter' in specifics:
            diam_text = specifics['Diameter']
            mm_match = re.search(r'([\d.]+)\s*mm', diam_text, re.I)
            if mm_match:
                diameter_mm = float(mm_match.group(1))
        
        if 'Weight' in specifics:
            weight_text = specifics['Weight']
            g_match = re.search(r'([\d.]+)\s*g(?:rams?)?', weight_text, re.I)
            if g_match:
                weight_g = float(g_match.group(1))
        
        # Parse from text
        if not diameter_mm:
            diam_match = re.search(r'(\d+(?:\.\d+)?)\s*mm', text, re.I)
            if diam_match:
                diameter_mm = float(diam_match.group(1))
        
        if not weight_g:
            # Handle various formats: 3.74g, 3.74 grams, 3.74 gm
            weight_match = re.search(r'(\d+(?:\.\d+)?)\s*g(?:rams?|m)?(?:\b|$)', text, re.I)
            if weight_match:
                weight_g = float(weight_match.group(1))
        
        return EbayPhysicalData(
            diameter_mm=diameter_mm,
            weight_g=weight_g
        )
    
    def _extract_references(self, text: str) -> list[EbayCatalogReference]:
        """Extract catalog references"""
        references = []
        
        for pattern, catalog in self.REFERENCE_PATTERNS:
            for match in pattern.finditer(text):
                raw = match.group(0)
                groups = match.groups()
                
                if catalog in ('RIC', 'RPC', 'SNG') and len(groups) >= 2:
                    ref = EbayCatalogReference(
                        catalog=catalog,
                        volume=groups[0],
                        number=groups[1],
                        raw_text=raw,
                        needs_verification=True
                    )
                else:
                    ref = EbayCatalogReference(
                        catalog=catalog,
                        number=groups[0] if groups else "",
                        raw_text=raw,
                        needs_verification=True
                    )
                
                if not any(r.raw_text == ref.raw_text for r in references):
                    references.append(ref)
        
        return references
    
    def _extract_grading(self, text: str, specifics: dict) -> EbayGradingInfo:
        """Extract grading information"""
        grading = EbayGradingInfo()
        
        # Check item specifics for certification
        cert_keys = ['Certification', 'Grading', 'Certification Number']
        for key in cert_keys:
            if key in specifics:
                cert_text = specifics[key]
                if 'NGC' in cert_text.upper():
                    grading.grading_service = 'NGC'
                    grading.is_slabbed = True
                elif 'PCGS' in cert_text.upper():
                    grading.grading_service = 'PCGS'
                    grading.is_slabbed = True
                elif 'ANACS' in cert_text.upper():
                    grading.grading_service = 'ANACS'
                    grading.is_slabbed = True
        
        # Extract grade from title/text
        for pattern, service in self.SLAB_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                grading.is_slabbed = True
                grading.grading_service = service
                grading.grade = match.group(1).strip()
                break
        
        # Certification number
        if 'Certification Number' in specifics:
            grading.cert_number = specifics['Certification Number']
        else:
            for pattern in self.CERT_PATTERNS:
                match = re.search(pattern, text, re.I)
                if match:
                    cert = match.group(1)
                    if len(cert) >= 7:  # Valid cert numbers are 7+ digits
                        grading.cert_number = cert
                        break
        
        # Raw grade from item specifics
        if 'Grade' in specifics and not grading.is_slabbed:
            grading.raw_grade = specifics['Grade']
        
        return grading
    
    def _parse_listing_info(self, url: str) -> EbayListingInfo:
        """Extract listing information"""
        info = EbayListingInfo()
        info.item_id = self._extract_item_id(url)
        
        # Price from JSON-LD
        if self.json_ld:
            offers = self.json_ld.get('offers', {})
            if isinstance(offers, dict):
                if offers.get('price'):
                    info.current_price = float(offers['price'])
                if offers.get('priceCurrency'):
                    info.currency = offers['priceCurrency']
        
        # Current price/bid
        price_selectors = [
            '.x-price-primary span',
            '[itemprop="price"]',
            '.vi-price .notranslate',
            '#prcIsum',
        ]
        for sel in price_selectors:
            el = self.soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                price_match = re.search(r'[\$€£]?([\d,]+\.?\d*)', text)
                if price_match:
                    info.current_price = float(price_match.group(1).replace(',', ''))
                # Currency
                if '$' in text or 'USD' in text:
                    info.currency = 'USD'
                elif '€' in text or 'EUR' in text:
                    info.currency = 'EUR'
                elif '£' in text or 'GBP' in text:
                    info.currency = 'GBP'
                break
        
        # Sold price
        sold_el = self.soup.select_one('.vi-price-np, .x-price-approx__price--soldPrice')
        if sold_el:
            text = sold_el.get_text(strip=True)
            price_match = re.search(r'[\$€£]?([\d,]+\.?\d*)', text)
            if price_match:
                info.sold_price = float(price_match.group(1).replace(',', ''))
                info.is_sold = True
        
        # Check for "Sold" status
        if self.soup.select_one('.vi-status .SOLD, .x-item-status--sold'):
            info.is_sold = True
            info.is_ended = True
        
        # Bid count
        bid_el = self.soup.select_one('#qty-test, .vi-qtyS-hot-red')
        if bid_el:
            match = re.search(r'(\d+)\s*bids?', bid_el.get_text(), re.I)
            if match:
                info.bid_count = int(match.group(1))
        
        # Listing type
        if info.bid_count and info.bid_count > 0:
            info.listing_type = EbayListingType.AUCTION
        elif self.soup.select_one('[data-testid="x-bin-price"]'):
            info.listing_type = EbayListingType.BUY_IT_NOW
        else:
            info.listing_type = EbayListingType.FIXED_PRICE
        
        # Shipping
        shipping_el = self.soup.select_one('#fshippingCost, .ux-labels-values--shipping .ux-textspans')
        if shipping_el:
            text = shipping_el.get_text(strip=True)
            if 'free' in text.lower():
                info.free_shipping = True
                info.shipping_cost = 0
            else:
                price_match = re.search(r'[\$€£]?([\d,]+\.?\d*)', text)
                if price_match:
                    info.shipping_cost = float(price_match.group(1).replace(',', ''))
        
        return info
    
    def _parse_seller_info(self) -> EbaySellerInfo:
        """Extract seller information"""
        seller = EbaySellerInfo()
        
        # Seller name
        seller_selectors = [
            '.x-sellercard-atf__info__about-seller a',
            '.si-inner .si-pd a',
            '[data-testid="str-seller-name"] a',
            '.x-seller-card a',
        ]
        for sel in seller_selectors:
            el = self.soup.select_one(sel)
            if el:
                seller.username = el.get_text(strip=True)
                break
        
        # Feedback score
        feedback_selectors = [
            '.x-sellercard-atf__data-item--feedback span',
            '.si-inner .si-fb a',
            '[data-testid="str-seller-feedback"]',
        ]
        for sel in feedback_selectors:
            el = self.soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                # Score
                score_match = re.search(r'([\d,]+)\s*(?:feedback|reviews)?', text, re.I)
                if score_match:
                    seller.feedback_score = int(score_match.group(1).replace(',', ''))
                # Percentage
                pct_match = re.search(r'([\d.]+)%', text)
                if pct_match:
                    seller.feedback_percent = float(pct_match.group(1))
                break
        
        # Top rated
        if self.soup.select_one('.x-sellercard-atf__badge--top-rated, .top-rated-img'):
            seller.is_top_rated = True
        
        # Seller location
        loc_el = self.soup.select_one('.ux-labels-values--itemLocation .ux-textspans, #itemLocation')
        if loc_el:
            seller.location = loc_el.get_text(strip=True)
        
        return seller
    
    def _extract_images(self) -> list[EbayImage]:
        """Extract image URLs"""
        images = []
        seen_urls = set()
        
        # JSON-LD images
        if self.json_ld and 'image' in self.json_ld:
            img_data = self.json_ld['image']
            if isinstance(img_data, str):
                img_data = [img_data]
            for url in img_data:
                if url not in seen_urls:
                    # Upgrade to high-res
                    large_url = self._upgrade_image_url(url)
                    images.append(EbayImage(url=large_url, url_large=large_url, index=len(images)))
                    seen_urls.add(url)
        
        # Image gallery
        img_selectors = [
            '.ux-image-carousel-item img',
            '.pic-gallery img',
            '#icImg',
            '.ux-image-magnify__container img',
            'img.img-responsive',
        ]
        
        for sel in img_selectors:
            for img in self.soup.select(sel):
                src = img.get('src') or img.get('data-zoom-src') or img.get('data-src')
                if src and src not in seen_urls:
                    if 'ebayimg.com' in src and 'placeholder' not in src:
                        large_url = self._upgrade_image_url(src)
                        images.append(EbayImage(
                            url=large_url,
                            url_large=large_url,
                            index=len(images)
                        ))
                        seen_urls.add(src)
        
        return images
    
    def _upgrade_image_url(self, url: str) -> str:
        """Upgrade eBay image URL to highest resolution"""
        # eBay image sizing: s-l64, s-l140, s-l225, s-l300, s-l400, s-l500, s-l1600
        # Replace any size with largest
        url = re.sub(r's-l\d+', 's-l1600', url)
        url = re.sub(r'\$_\d+\.', '$_57.', url)  # Alternative format
        return url
