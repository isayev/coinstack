"""
CNG Parser

Extracts structured coin data from CNG auction HTML pages.
Leverages JSON-LD schema.org data embedded in pages for cleaner extraction.
"""

import re
import json
from typing import Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from .models import (
    CNGCoinData, PhysicalData, CatalogReference, Provenance, 
    ProvenanceEntry, CNGImage, AuctionInfo, CNGAuctionType, CNGMetal
)

logger = logging.getLogger(__name__)


class CNGParser:
    """
    Parser for CNG auction lot pages.
    
    CNG uses the Auction Mobility platform which embeds JSON-LD 
    structured data - we parse that first, then supplement with
    HTML parsing for additional fields.
    """
    
    # Reference patterns for catalog number extraction
    REFERENCE_PATTERNS = [
        # RIC with volume: "RIC III 676 (Aurelius)" or "RIC II.1 783"
        re.compile(r'RIC\s+(?P<vol>[IVX]+(?:\.\d)?)\s+(?P<num>\d+[a-z]?)(?:\s*\((?P<suffix>[^)]+)\))?', re.I),
        # Crawford: "Crawford 44/5" or "Cr. 44/5"
        re.compile(r'(?:Crawford|Cr\.?)\s*(?P<num>\d+/\d+[a-z]?)', re.I),
        # RSC: "RSC 162"
        re.compile(r'RSC\s+(?P<num>\d+[a-z]?)', re.I),
        # RPC: "RPC I 1234"
        re.compile(r'RPC\s+(?P<vol>[IVX]+)\s+(?P<num>\d+)', re.I),
        # Sear: "Sear 1234"
        re.compile(r'Sear\s+(?P<num>\d+)', re.I),
        # MIR: "MIR 18, 10-4a"
        re.compile(r'MIR\s+(?P<vol>\d+),?\s*(?P<num>[\d\-]+[a-z]?)', re.I),
        # BMC: "BMC 123"
        re.compile(r'BMC\s+(?P<num>\d+)', re.I),
        # SNG: "SNG Copenhagen 123"
        re.compile(r'SNG\s+(?P<collection>\w+)\s+(?P<num>\d+)', re.I),
    ]
    
    def __init__(self):
        self.soup: Optional[BeautifulSoup] = None
        self.json_ld: Optional[dict] = None
    
    def parse(self, html: str, url: str) -> CNGCoinData:
        """
        Parse CNG lot page HTML into structured data.
        
        Args:
            html: Raw HTML content
            url: Page URL (for lot ID extraction)
            
        Returns:
            CNGCoinData with all extracted fields
        """
        self.soup = BeautifulSoup(html, 'html.parser')
        self.json_ld = self._extract_json_ld()
        
        # Extract lot ID from URL
        lot_id = self._extract_lot_id(url)
        
        # Start with JSON-LD data
        title = self._get_title()
        description = self._get_description()
        images = self._get_images()
        price_data = self._get_price_data()
        
        # Parse title for structured fields
        title_data = self._parse_title(title)
        
        # Parse description for detailed fields
        desc_data = self._parse_description(description)
        
        # Get auction info
        auction = self._get_auction_info(price_data)
        
        # Build coin data
        return CNGCoinData(
            cng_lot_id=lot_id,
            url=url,
            title=title,
            ruler=title_data.get('ruler'),
            ruler_title=title_data.get('ruler_title'),
            reign_dates=title_data.get('reign_dates'),
            denomination=title_data.get('denomination'),
            metal=title_data.get('metal'),
            mint=title_data.get('mint'),
            struck_dates=title_data.get('struck_dates'),
            struck_under=title_data.get('struck_under'),
            physical=title_data.get('physical', PhysicalData()),
            obverse_description=desc_data.get('obverse'),
            reverse_description=desc_data.get('reverse'),
            references=desc_data.get('references', []),
            grade=title_data.get('grade') or desc_data.get('grade'),
            condition_notes=desc_data.get('condition_notes'),
            provenance=desc_data.get('provenance', Provenance()),
            categories=self._get_categories(),
            auction=auction,
            images=images,
            raw_description=description,
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # JSON-LD EXTRACTION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _extract_json_ld(self) -> Optional[dict]:
        """Extract JSON-LD Product schema from page"""
        # Method 1: Look for script tags with JSON-LD
        for script in self.soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    return data
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            return item
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Method 2: Look for Product schema in page text
        page_text = self.soup.get_text()
        product_match = re.search(
            r'\{"@context":"http[s]?://schema\.org/?[^}]*"@type":"Product"[^}]*\}',
            page_text.replace('\\/', '/')
        )
        
        if product_match:
            try:
                json_str = self._extract_full_json(page_text, product_match.start())
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON-LD: {e}")
        
        return None
    
    def _extract_full_json(self, text: str, start: int) -> str:
        """Extract complete JSON object from position"""
        depth = 0
        end = start
        
        for i, char in enumerate(text[start:], start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        
        return text[start:end]
    
    def _get_title(self) -> str:
        """Get coin title from JSON-LD or page"""
        if self.json_ld and 'name' in self.json_ld:
            return self.json_ld['name']
        
        # Fallback to page title element
        title_elem = self.soup.find('h1') or self.soup.find('title')
        if title_elem:
            return title_elem.text.split('|')[0].strip()
        
        return ""
    
    def _get_description(self) -> str:
        """Get full description from JSON-LD"""
        if self.json_ld and 'description' in self.json_ld:
            # Description has HTML - convert to plain text while preserving structure
            desc_html = self.json_ld['description']
            desc_soup = BeautifulSoup(desc_html, 'html.parser')
            return desc_soup.get_text(separator='\n').strip()
        
        # Fallback to page content
        desc_elem = self.soup.find(class_='description') or self.soup.find(id='description')
        if desc_elem:
            return desc_elem.get_text(separator='\n').strip()
        
        # Try to find lot description in Angular app
        lot_desc = self.soup.find(class_=re.compile(r'lot.*desc|desc.*lot', re.I))
        if lot_desc:
            return lot_desc.get_text(separator='\n').strip()
        
        return ""
    
    def _get_images(self) -> list[CNGImage]:
        """Extract image URLs from JSON-LD and page"""
        images = []
        
        # From JSON-LD
        if self.json_ld and 'image' in self.json_ld:
            img_list = self.json_ld['image']
            if isinstance(img_list, str):
                img_list = [img_list]
            
            for i, url in enumerate(img_list):
                # Get full resolution by removing size constraints
                full_url = re.sub(r'\?.*$', '', url)
                img_type = "obverse" if i == 0 else "reverse" if i == 1 else "other"
                images.append(CNGImage(
                    url=url,
                    url_full_res=full_url,
                    index=i,
                    image_type=img_type
                ))
        
        # Also look for images in page
        for img in self.soup.find_all('img', src=re.compile(r'auctionmobility.*\.jpg')):
            url = img.get('src', '')
            # Upgrade to high resolution
            full_url = re.sub(r'\?width=\d+.*$', '', url)
            high_res_url = url.replace('width=440', 'width=1600').replace('height=440', 'height=1600')
            
            if url and not any(i.url == url or i.url_full_res == full_url for i in images):
                images.append(CNGImage(
                    url=high_res_url,
                    url_full_res=full_url,
                    index=len(images),
                    image_type="other"
                ))
        
        # Also look for data-zoom-image or high-res links
        for link in self.soup.find_all('a', href=re.compile(r'\.jpg')):
            url = link.get('href', '')
            if 'auctionmobility' in url and not any(i.url_full_res == url for i in images):
                images.append(CNGImage(
                    url=url,
                    url_full_res=url,
                    index=len(images),
                    image_type="other"
                ))
        
        return images
    
    def _get_price_data(self) -> dict:
        """Extract price info from JSON-LD"""
        if self.json_ld and 'offers' in self.json_ld:
            offers = self.json_ld['offers']
            price = offers.get('price')
            if price:
                try:
                    price = int(float(price))
                except (ValueError, TypeError):
                    price = None
            return {
                'price': price,
                'currency': offers.get('priceCurrency', 'USD'),
                'is_sold': 'SoldOut' in offers.get('availability', ''),
            }
        return {}
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TITLE PARSING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _parse_title(self, title: str) -> dict:
        """
        Parse CNG title format into structured fields.
        
        Example: "Faustina Junior. Augusta, AD 147-175. AR Denarius (17mm, 3.20 g, 12h). 
                  Rome mint. Struck under Marcus Aurelius and Lucius Verus, circa AD 161. VF."
        """
        result = {}
        
        # First extract physical data from parentheses (before splitting by period)
        phys_match = re.search(r'\((\d+(?:\.\d+)?\s*mm[^)]+)\)', title)
        if phys_match:
            result['physical'] = self._parse_physical(phys_match.group(1))
        
        # Protect decimal numbers from period splitting
        protected_title = re.sub(r'(\d)\.(\d)', r'\1<DOT>\2', title)
        parts = [p.strip().replace('<DOT>', '.') for p in protected_title.split('.') if p.strip()]
        
        if len(parts) >= 1:
            result['ruler'] = parts[0]
        
        if len(parts) >= 2:
            # Parse "Augusta, AD 147-175" or "As Caesar, AD 69-79"
            title_part = parts[1]
            dates_match = re.search(r'(AD|BC)\s*\d+(?:\s*-\s*\d+)?', title_part)
            if dates_match:
                result['reign_dates'] = dates_match.group()
                result['ruler_title'] = title_part[:dates_match.start()].strip(' ,')
        
        if len(parts) >= 3:
            # Parse "AR Denarius (17mm, 3.20 g, 12h)"
            denom_part = parts[2]
            
            # Extract metal
            metal_match = re.match(r'^(AV|AR|Æ|AE|BI|EL|PB)\s+', denom_part)
            if metal_match:
                result['metal'] = self._parse_metal(metal_match.group(1))
                denom_part = denom_part[metal_match.end():]
            
            # Extract denomination - remove parenthetical physical data
            phys_match = re.search(r'\([^)]*\d+\s*mm[^)]*\)', denom_part)
            if phys_match:
                result['denomination'] = denom_part[:phys_match.start()].strip()
                # Physical already extracted above from full title
            else:
                # Also handle truncated physical data like "(17mm, 3"
                trunc_match = re.search(r'\(\d+', denom_part)
                if trunc_match:
                    result['denomination'] = denom_part[:trunc_match.start()].strip()
                else:
                    result['denomination'] = denom_part.strip()
        
        if len(parts) >= 4:
            # Parse mint: "Rome mint"
            mint_part = parts[3]
            if 'mint' in mint_part.lower():
                result['mint'] = mint_part.replace('mint', '').strip()
        
        if len(parts) >= 5:
            # Parse struck info: "Struck under Marcus Aurelius and Lucius Verus, circa AD 161"
            struck_part = parts[4]
            
            under_match = re.search(r'Struck under\s+([^,]+)', struck_part, re.I)
            if under_match:
                result['struck_under'] = under_match.group(1).strip()
            
            date_match = re.search(r'(?:circa\s+)?(AD|BC)\s*\d+(?:\s*-\s*\d+)?', struck_part)
            if date_match:
                result['struck_dates'] = date_match.group().strip()
        
        # Last part is usually grade
        if len(parts) >= 6:
            grade_part = parts[-1].strip()
            if grade_part in ['VF', 'EF', 'VG', 'Fine', 'Good', 'Fair', 'Near VF', 'Choice VF',
                             'Superb EF', 'Choice EF', 'Near EF', 'Good VF', 'Near Fine', 'Good Fine']:
                result['grade'] = grade_part
        
        return result
    
    def _parse_physical(self, phys_str: str) -> PhysicalData:
        """Parse physical measurements from string like '17mm, 3.20 g, 12h'"""
        diameter = None
        weight = None
        die_axis = None
        
        # Diameter
        dm = re.search(r'([\d.]+)\s*mm', phys_str)
        if dm:
            diameter = float(dm.group(1))
        
        # Weight
        wm = re.search(r'([\d.]+)\s*g', phys_str)
        if wm:
            weight = float(wm.group(1))
        
        # Die axis
        am = re.search(r'(\d+)\s*h', phys_str)
        if am:
            die_axis = int(am.group(1))
        
        return PhysicalData(
            diameter_mm=diameter,
            weight_g=weight,
            die_axis_hours=die_axis
        )
    
    def _parse_metal(self, metal_str: str) -> Optional[CNGMetal]:
        """Convert metal string to enum"""
        mapping = {
            'AV': CNGMetal.GOLD,
            'AR': CNGMetal.SILVER,
            'Æ': CNGMetal.BRONZE,
            'AE': CNGMetal.BRONZE,
            'BI': CNGMetal.BILLON,
            'EL': CNGMetal.ELECTRUM,
            'PB': CNGMetal.LEAD,
        }
        return mapping.get(metal_str.upper())
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DESCRIPTION PARSING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _parse_description(self, description: str) -> dict:
        """
        Parse the full description text.
        
        CNG descriptions follow this pattern:
        1. Title/header (duplicates title)
        2. Obverse / Reverse descriptions
        3. References (RIC, RSC, etc.)
        4. Condition notes
        5. Grade
        6. Provenance (often in italics, starts with "Ex")
        7. Historical notes (narrative about provenance)
        """
        result = {}
        
        # Split description into lines
        lines = [l.strip() for l in description.split('\n') if l.strip()]
        
        # Find obverse/reverse descriptions (usually contains "/")
        for line in lines:
            if '/' in line and not line.startswith('Ex') and 'Closing' not in line:
                parts = line.split('/')
                if len(parts) == 2:
                    result['obverse'] = parts[0].strip()
                    # Reverse continues until reference
                    reverse = parts[1]
                    ref_start = self._find_reference_start(reverse)
                    if ref_start > 0:
                        result['reverse'] = reverse[:ref_start].strip(' .')
                    else:
                        result['reverse'] = reverse.strip()
                break
        
        # Extract references
        result['references'] = self._extract_references(description)
        
        # Extract condition notes (text after references, before grade)
        result['condition_notes'] = self._extract_condition_notes(description)
        
        # Extract grade from description
        grade_match = re.search(
            r'\b(Superb EF|Choice EF|EF|Near EF|Good VF|Choice VF|VF|Near VF|'
            r'Good Fine|Fine|Near Fine|VG|Good|Fair|Poor)\b\.?\s*$',
            description[:500]  # Grade usually in first part
        )
        if grade_match:
            result['grade'] = grade_match.group(1)
        
        # Extract provenance
        result['provenance'] = self._extract_provenance(description)
        
        return result
    
    def _find_reference_start(self, text: str) -> int:
        """Find where catalog references begin in text"""
        for pattern in ['RIC', 'Crawford', 'Cr.', 'RSC', 'RPC', 'Sear', 'MIR', 'BMC', 'SNG']:
            idx = text.find(pattern)
            if idx > 0:
                return idx
        return -1
    
    def _extract_references(self, text: str) -> list[CatalogReference]:
        """Extract all catalog references from description"""
        references = []
        
        for pattern in self.REFERENCE_PATTERNS:
            for match in pattern.finditer(text):
                ref = self._build_reference(pattern, match)
                if ref:
                    references.append(ref)
        
        return references
    
    def _build_reference(self, pattern: re.Pattern, match: re.Match) -> Optional[CatalogReference]:
        """Build CatalogReference from regex match"""
        groups = match.groupdict()
        raw = match.group(0)
        
        # Determine catalog name from pattern
        pattern_str = pattern.pattern.lower()
        if 'ric' in pattern_str:
            catalog = 'RIC'
        elif 'crawford' in pattern_str or 'cr\\.' in pattern_str:
            catalog = 'Crawford'
        elif 'rsc' in pattern_str:
            catalog = 'RSC'
        elif 'rpc' in pattern_str:
            catalog = 'RPC'
        elif 'sear' in pattern_str:
            catalog = 'Sear'
        elif 'mir' in pattern_str:
            catalog = 'MIR'
        elif 'bmc' in pattern_str:
            catalog = 'BMC'
        elif 'sng' in pattern_str:
            catalog = 'SNG'
        else:
            return None
        
        return CatalogReference(
            catalog=catalog,
            volume=groups.get('vol') or groups.get('collection'),
            number=groups.get('num', ''),
            suffix=groups.get('suffix'),
            raw_text=raw
        )
    
    def _extract_condition_notes(self, text: str) -> Optional[str]:
        """Extract condition/toning notes"""
        condition_patterns = [
            r'((?:Deep|Old|Light|Cabinet|Rainbow)\s+)?(?:toning|patina|deposits)[^.]*\.',
            r'(?:scratch|scratches|porosity|corrosion|flan flaws?|marks?|cleaning)[^.]*\.',
        ]
        
        notes = []
        for pattern in condition_patterns:
            for match in re.finditer(pattern, text, re.I):
                notes.append(match.group(0).strip())
        
        return ' '.join(notes) if notes else None
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PROVENANCE PARSING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _extract_provenance(self, text: str) -> Provenance:
        """Extract provenance data from description"""
        entries = []
        pedigree_year = None
        historical_notes = None
        raw_text = ""
        
        # Find provenance section (usually starts with "Ex" in italics)
        ex_match = re.search(r'Ex\s+[^.]+(?:\([^)]+\))?[^.]*\.', text)
        if ex_match:
            raw_text = ex_match.group(0)
            
            # Parse the "Ex Collection (Auction, Date), lot X" format
            prov_text = raw_text
            
            # Extract auction info
            auction_match = re.search(
                r'Ex\s+(?P<collection>[^(]+?)\s*'
                r'(?:\((?P<auction>[^,)]+)(?:,\s*(?P<date>[^)]+))?\))?'
                r'(?:,\s*lot\s*(?P<lot>\d+))?'
                r'(?:,\s*(?P<extra>[^.]+))?',
                prov_text
            )
            
            if auction_match:
                groups = auction_match.groupdict()
                
                # Main collection entry
                if groups.get('collection'):
                    entries.append(ProvenanceEntry(
                        source_type="collection",
                        source_name=groups['collection'].strip(),
                        raw_text=raw_text
                    ))
                
                # Auction entry
                if groups.get('auction'):
                    auction_name = groups['auction'].strip()
                    entries.append(ProvenanceEntry(
                        source_type="auction",
                        source_name=auction_name,
                        date=groups.get('date', '').strip() or None,
                        lot_number=groups.get('lot'),
                        raw_text=raw_text
                    ))
                
                # Check for "purchased before XXXX" in extra
                if groups.get('extra'):
                    before_match = re.search(r'(?:purchased\s+)?before\s+(\d{4})', groups['extra'], re.I)
                    if before_match:
                        pedigree_year = int(before_match.group(1))
        
        # Look for extended historical narrative
        if raw_text:
            prov_end = text.find(raw_text) + len(raw_text)
            remaining = text[prov_end:].strip()
            
            if remaining and not remaining.startswith('Closing') and not remaining.startswith('All winning'):
                end_markers = ['Closing Date', 'All winning bids', '\n\n']
                end_idx = len(remaining)
                for marker in end_markers:
                    idx = remaining.find(marker)
                    if idx > 0:
                        end_idx = min(end_idx, idx)
                
                historical = remaining[:end_idx].strip()
                if len(historical) > 50:  # Substantial narrative
                    historical_notes = historical
        
        # Also check for "Pedigreed to XXXX" badge
        pedigree_match = re.search(r'Pedigreed to (\d{4})', text)
        if pedigree_match and not pedigree_year:
            pedigree_year = int(pedigree_match.group(1))
        
        return Provenance(
            entries=entries,
            pedigree_year=pedigree_year,
            historical_notes=historical_notes,
            raw_text=raw_text
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AUCTION INFO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _get_auction_info(self, price_data: dict) -> Optional[AuctionInfo]:
        """Extract auction metadata"""
        # Find auction name from page
        auction_link = self.soup.find('a', href=re.compile(r'/auctions/'))
        auction_name = ""
        if auction_link:
            auction_name = auction_link.get_text(strip=True)
        
        # Determine auction type
        auction_type = CNGAuctionType.ELECTRONIC
        if 'Triton' in auction_name:
            auction_type = CNGAuctionType.TRITON
        elif 'Feature' in auction_name:
            auction_type = CNGAuctionType.FEATURE
        elif 'Mail Bid' in auction_name:
            auction_type = CNGAuctionType.MAIL_BID
        
        # Find lot number
        lot_num = 0
        lot_match = re.search(r'Lot\s*#?\s*(\d+)', self.soup.get_text())
        if lot_match:
            lot_num = int(lot_match.group(1))
        
        # Find estimate
        estimate = None
        est_match = re.search(r'Est\.?\s*\$?([\d,]+)', self.soup.get_text())
        if est_match:
            estimate = int(est_match.group(1).replace(',', ''))
        
        # Find bids
        bids = None
        bids_match = re.search(r'Bids:\s*(\d+)', self.soup.get_text())
        if bids_match:
            bids = int(bids_match.group(1))
        
        # Closing date
        closing_date = None
        date_match = re.search(
            r'Closing Date and Time:\s*(\d+\s+\w+\s+\d{4})\s+at\s+([\d:]+)',
            self.soup.get_text()
        )
        if date_match:
            try:
                date_str = f"{date_match.group(1)} {date_match.group(2)}"
                closing_date = datetime.strptime(date_str, "%d %B %Y %H:%M:%S")
            except ValueError:
                pass
        
        return AuctionInfo(
            auction_name=auction_name,
            auction_type=auction_type,
            lot_number=lot_num,
            estimate_usd=estimate,
            sold_price_usd=price_data.get('price'),
            bids=bids,
            closing_date=closing_date,
            is_sold=price_data.get('is_sold', False),
            buyers_premium_pct=20.0
        )
    
    def _get_categories(self) -> list[str]:
        """Extract category tags"""
        categories = []
        
        # Look for category links
        for link in self.soup.find_all('a', href=re.compile(r'/lots\?categories=')):
            cat_text = link.get_text(strip=True)
            if cat_text and cat_text not in categories:
                categories.append(cat_text)
        
        return categories
    
    def _extract_lot_id(self, url: str) -> str:
        """Extract lot ID from URL"""
        # URL format: /lots/view/4-DJ6RZM/slug
        match = re.search(r'/lots/view/([^/]+)', url)
        if match:
            return match.group(1)
        return ""
