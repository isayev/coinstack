"""
Heritage Auctions Parser

Extracts structured coin data from Heritage Auctions HTML pages.
Heritage uses server-rendered HTML (not SPA), making parsing straightforward.
"""

import re
from typing import Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from .models import (
    HeritageCoinData, PhysicalData, CatalogReference, Provenance,
    ProvenanceEntry, HeritageImage, AuctionInfo, HeritageAuctionType,
    HeritageMetal, SlabGrade, RawGrade, GradingService
)

logger = logging.getLogger(__name__)


class HeritageParser:
    """
    Parser for Heritage Auctions lot pages.
    
    Heritage URL format:
    /itm/{category}/{subcategory}/{slug}/a/{auction_id}-{lot_number}.s
    
    Example:
    /itm/ancients/roman-imperial/roman-imperial-domitian.../a/61519-25289.s
    """
    
    # ─── Title Parsing Patterns ───
    
    # Physical data: "(28mm, 10.94 gm, 5h)" - note Heritage uses "gm" not "g"
    PHYSICAL_PATTERN = re.compile(
        r'\((?P<diameter>[\d.]+)mm'
        r'(?:,\s*(?P<weight>[\d.]+)\s*gm?)?'
        r'(?:,\s*(?P<axis>\d+)h)?\)'
    )
    
    # NGC grade: "NGC MS 4/5 - 4/5" or "NGC Choice AU 5/5 - 4/5, Fine Style"
    NGC_GRADE_PATTERN = re.compile(
        r'NGC\s+'
        r'(?P<designation>Choice\s+)?'
        r'(?P<grade>MS|AU|XF|VF|Fine|VG|Good)\s*'
        r'(?P<numeric>\d+)?\s*'
        r'(?:(?P<strike>\d/\d)\s*-\s*(?P<surface>\d/\d))?'
        r'(?:,?\s*(?P<extra>[^.]+))?'
    )
    
    # PCGS grade: "PCGS MS65" or "PCGS AU58"
    PCGS_GRADE_PATTERN = re.compile(
        r'PCGS\s+'
        r'(?P<grade>MS|AU|XF|VF|Fine|VG|Good)\s*'
        r'(?P<numeric>\d+)?'
    )
    
    # Raw grade: "Choice VF", "XF", "VF", "Fine", etc.
    RAW_GRADE_PATTERN = re.compile(
        r'(?P<grade>(?:Superb|Choice|Good|Near)?\s*'
        r'(?:EF|XF|VF|AU|MS|Fine|VG|Good|Fair|Poor))'
        r'(?:,?\s*(?P<qualifier>[^.]+))?'
        r'\s*\.?\s*$'
    )
    
    # Reference patterns
    REFERENCE_PATTERNS = [
        # RIC with volume: "RIC II.1 756" or "RIC V.I 160"
        (re.compile(r'RIC\s+(?P<vol>[IVX]+(?:\.\d)?)\s+(?P<num>\d+[a-z]?)', re.I), 'RIC'),
        # Crawford: "Crawford 44/5"
        (re.compile(r'(?:Crawford|Cr\.?)\s*(?P<num>\d+/\d+[a-z]?)', re.I), 'Crawford'),
        # RSC: "RSC 162"
        (re.compile(r'RSC\s+(?P<num>\d+[a-z]?)', re.I), 'RSC'),
        # RPC: "RPC I 1234"
        (re.compile(r'RPC\s+(?P<vol>[IVX]+)\s+(?P<num>\d+)', re.I), 'RPC'),
        # Sear: "Sear 1234"
        (re.compile(r'Sear\s+(?P<num>\d+)', re.I), 'Sear'),
        # BMC: "BMC 123"
        (re.compile(r'BMC\s+(?P<num>\d+)', re.I), 'BMC'),
        # Sydenham
        (re.compile(r'Sydenham\s+(?P<num>\d+)', re.I), 'Sydenham'),
        # Cohen
        (re.compile(r'Cohen\s+(?P<num>\d+)', re.I), 'Cohen'),
        # SNG
        (re.compile(r'SNG\s+(?P<vol>\w+)\s+(?P<num>\d+)', re.I), 'SNG'),
        # Calicó
        (re.compile(r'Calicó\s+(?P<num>\d+[a-z]?)', re.I), 'Calicó'),
    ]
    
    def __init__(self):
        self.soup: Optional[BeautifulSoup] = None
    
    def parse(self, html: str, url: str) -> HeritageCoinData:
        """
        Parse Heritage lot page HTML into structured data.
        """
        self.soup = BeautifulSoup(html, 'html.parser')
        
        # Extract IDs from URL
        lot_id, auction_id, lot_number = self._extract_ids(url)
        category, subcategory = self._extract_category(url)
        
        # Get title
        title = self._get_title()
        
        # Parse title for structured fields
        title_data = self._parse_title(title)
        
        # Get description section
        description = self._get_description()
        desc_data = self._parse_description(description)
        
        # Get grading info
        grade_data = self._parse_grading(title, description)
        
        # Get auction info
        auction = self._get_auction_info(auction_id, lot_number)
        
        # Get images
        images = self._get_images()
        
        # Get provenance
        provenance = self._parse_provenance(description)
        
        return HeritageCoinData(
            heritage_lot_id=lot_id,
            url=url,
            category=category,
            subcategory=subcategory,
            title=title,
            ruler=title_data.get('ruler'),
            ruler_title=title_data.get('ruler_title'),
            reign_dates=title_data.get('reign_dates'),
            denomination=title_data.get('denomination'),
            metal=title_data.get('metal'),
            mint=desc_data.get('mint'),
            mint_date=desc_data.get('mint_date'),
            physical=title_data.get('physical', PhysicalData()),
            is_slabbed=grade_data.get('is_slabbed', False),
            slab_grade=grade_data.get('slab_grade'),
            raw_grade=grade_data.get('raw_grade'),
            obverse_legend=desc_data.get('obverse_legend'),
            obverse_description=desc_data.get('obverse_description'),
            reverse_legend=desc_data.get('reverse_legend'),
            reverse_description=desc_data.get('reverse_description'),
            exergue=desc_data.get('exergue'),
            references=desc_data.get('references', []),
            condition_notes=desc_data.get('condition_notes'),
            surface_issues=grade_data.get('surface_issues'),
            provenance=provenance,
            historical_notes=desc_data.get('historical_notes'),
            auction=auction,
            images=images,
            raw_description=description,
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # URL PARSING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _extract_ids(self, url: str) -> tuple[str, int, int]:
        """Extract lot ID, auction ID, and lot number from URL"""
        # Pattern: /a/{auction_id}-{lot_number}.s
        match = re.search(r'/a/(\d+)-(\d+)\.s', url)
        if match:
            auction_id = int(match.group(1))
            lot_number = int(match.group(2))
            lot_id = f"{auction_id}-{lot_number}"
            return lot_id, auction_id, lot_number
        
        # Try query string format
        auction_match = re.search(r'saleNo=(\d+)', url)
        lot_match = re.search(r'lotIdNo=(\d+)', url)
        if auction_match and lot_match:
            auction_id = int(auction_match.group(1))
            lot_number = int(lot_match.group(1))
            return f"{auction_id}-{lot_number}", auction_id, lot_number
        
        # Fallback for unknown URLs
        return "unknown", 0, 0
    
    def _extract_category(self, url: str) -> tuple[str, Optional[str]]:
        """Extract category from URL path"""
        # Pattern: /itm/{category}/{subcategory}/...
        match = re.search(r'/itm/([^/]+)/([^/]+)/', url)
        if match:
            category = match.group(1).replace('-', ' ').title()
            subcategory = match.group(2).replace('-', ' ').title()
            return category, subcategory
        
        return "Unknown", None
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TITLE EXTRACTION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _get_title(self) -> str:
        """Get coin title from page"""
        # Look for the main heading
        h1 = self.soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        # Fallback to title tag
        title_tag = self.soup.find('title')
        if title_tag:
            title = title_tag.text
            # Remove " | Lot #XXXXX | Heritage Auctions"
            return re.sub(r'\s*\|\s*Lot.*$', '', title).strip()
        
        return ""
    
    def _parse_title(self, title: str) -> dict:
        """
        Parse Heritage title format.
        """
        result = {}
        
        # Remove category prefix "Roman Imperial: " or similar
        if ':' in title:
            title = title.split(':', 1)[1].strip()
        
        # Parse ruler and title
        # Pattern: "Ruler, Title (AD dates)."
        ruler_match = re.match(
            r'^(?P<ruler>[^,(]+)'
            r'(?:,\s*(?P<title>[^(]+))?'
            r'\s*\((?P<dates>[^)]+)\)',
            title
        )
        
        if ruler_match:
            result['ruler'] = ruler_match.group('ruler').strip()
            if ruler_match.group('title'):
                result['ruler_title'] = ruler_match.group('title').strip()
            result['reign_dates'] = ruler_match.group('dates').strip()
        
        # Parse metal and denomination
        # Pattern: "AE as" or "BI antoninianus" or "AR denarius"
        metal_denom_match = re.search(
            r'\.\s*(AV|AR|AE|BI|EL|Orichalcum)\s+(\w+)',
            title, re.I
        )
        
        if metal_denom_match:
            result['metal'] = self._parse_metal(metal_denom_match.group(1))
            result['denomination'] = metal_denom_match.group(2)
        
        # Parse physical data
        phys_match = self.PHYSICAL_PATTERN.search(title)
        if phys_match:
            result['physical'] = PhysicalData(
                diameter_mm=float(phys_match.group('diameter')) if phys_match.group('diameter') else None,
                weight_gm=float(phys_match.group('weight')) if phys_match.group('weight') else None,
                die_axis_hours=int(phys_match.group('axis')) if phys_match.group('axis') else None,
            )
        
        return result
    
    def _parse_metal(self, metal_str: str) -> Optional[HeritageMetal]:
        """Convert metal string to enum"""
        mapping = {
            'AV': HeritageMetal.GOLD,
            'AR': HeritageMetal.SILVER,
            'AE': HeritageMetal.BRONZE,
            'BI': HeritageMetal.BILLON,
            'EL': HeritageMetal.ELECTRUM,
            'Orichalcum': HeritageMetal.ORICHALCUM,
        }
        return mapping.get(metal_str.upper(), HeritageMetal.BRONZE)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DESCRIPTION PARSING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _get_description(self) -> str:
        """Extract description text from page"""
        # Look for description section
        desc_section = self.soup.find(id='auction-description')
        if desc_section:
            return desc_section.get_text(separator='\n', strip=True)
        
        # Alternative: look for Description heading
        desc_heading = self.soup.find('h2', string=re.compile('Description', re.I))
        if desc_heading:
            content = []
            for sibling in desc_heading.find_next_siblings():
                if sibling.name in ['h2', 'h3']:
                    break
                content.append(sibling.get_text(strip=True))
            return '\n'.join(content)
        
        # Fallback: get body text
        body = self.soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)[:5000]
        
        return ""
    
    def _parse_description(self, description: str) -> dict:
        """
        Parse the description text.
        """
        result = {}
        
        # Find mint and date
        # Pattern: "Rome, AD 92-94." or "Antioch, circa AD 270."
        mint_match = re.search(
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*((?:circa\s+)?AD\s*\d+(?:\s*-\s*\d+)?)\.',
            description,
            re.M
        )
        if mint_match:
            result['mint'] = mint_match.group(1)
            result['mint_date'] = mint_match.group(2)
        
        # Find obverse/reverse split by " / "
        obv_rev_match = re.search(
            r'([A-Z][^/]+?)\s*/\s*([A-Z].+?)(?:\.\s*(?:RIC|Crawford|Sear|RSC|BMC)|\.\s*[A-Z][a-z])',
            description
        )
        
        if obv_rev_match:
            obverse_full = obv_rev_match.group(1).strip()
            reverse_full = obv_rev_match.group(2).strip()
            
            result['obverse_legend'], result['obverse_description'] = self._split_legend_desc(obverse_full)
            result['reverse_legend'], result['reverse_description'] = self._split_legend_desc(reverse_full)
        
        # Extract exergue
        exergue_match = re.search(r'(?:in exergue|ex\.?)[,:]?\s*([^.;]+)', description, re.I)
        if exergue_match:
            result['exergue'] = exergue_match.group(1).strip()
        
        # Extract references
        result['references'] = self._extract_references(description)
        
        # Extract condition notes
        condition_patterns = [
            r'((?:Deep|Old|Light|Cabinet|Rainbow|Attractive|Lovely)\s+)?'
            r'(?:toning|patina|deposits|luster)[^.]*\.',
            r'(?:Struck|Well[- ]struck|Lightly struck)[^.]*\.',
        ]
        
        condition_notes = []
        for pattern in condition_patterns:
            for match in re.finditer(pattern, description, re.I):
                condition_notes.append(match.group(0).strip())
        
        if condition_notes:
            result['condition_notes'] = ' '.join(condition_notes)
        
        # Extract historical notes
        historical_match = re.search(
            r'([A-Z][a-z]+(?:,\s+[a-z]+)?\s+(?:often|was|is|became|ruled|reigned)[^.]+\.(?:\s+[A-Z][^.]+\.)*)',
            description
        )
        if historical_match:
            result['historical_notes'] = historical_match.group(1).strip()
        
        return result
    
    def _split_legend_desc(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Split "LEGEND, description" into separate parts"""
        match = re.match(r'^([A-Z][A-Z\s\-]+),\s*(.+)$', text)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return None, text
    
    def _extract_references(self, text: str) -> list[CatalogReference]:
        """Extract catalog references from description"""
        references = []
        
        for pattern, catalog in self.REFERENCE_PATTERNS:
            for match in forPattern.finditer(text):
                raw = match.group(0)
                groups = match.groupdict()
                
                references.append(CatalogReference(
                    catalog=catalog,
                    volume=groups.get('vol'),
                    number=groups.get('num', ''),
                    raw_text=raw
                ))
        
        return references
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GRADING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _parse_grading(self, title: str, description: str) -> dict:
        """Parse grading information from title and description"""
        result = {'is_slabbed': False}
        text = f"{title} {description}"
        
        # Check for NGC certification link
        ngc_link = self.soup.find('a', href=re.compile(r'ngccoin\.com/certlookup')) if self.soup else None
        if ngc_link:
            cert_match = re.search(r'/certlookup/(\d+)/', ngc_link.get('href', ''))
            cert_number = cert_match.group(1) if cert_match else None
            
            ngc_match = self.NGC_GRADE_PATTERN.search(text)
            if ngc_match:
                result['is_slabbed'] = True
                result['slab_grade'] = SlabGrade(
                    service=GradingService.NGC,
                    grade=ngc_match.group('grade'),
                    strike_score=ngc_match.group('strike'),
                    surface_score=ngc_match.group('surface'),
                    numeric_grade=int(ngc_match.group('numeric')) if ngc_match.group('numeric') else None,
                    designation=f"{ngc_match.group('designation') or ''}{ngc_match.group('extra') or ''}".strip() or None,
                    certification_number=cert_number,
                    verification_url=ngc_link.get('href')
                )
                return result
        
        # Check for NGC in title without link
        ngc_match = self.NGC_GRADE_PATTERN.search(text)
        if ngc_match:
            result['is_slabbed'] = True
            cert_match = re.search(r'(?:NGC|cert)\s*#?\s*(\d{7,})', text, re.I)
            result['slab_grade'] = SlabGrade(
                service=GradingService.NGC,
                grade=ngc_match.group('grade'),
                strike_score=ngc_match.group('strike'),
                surface_score=ngc_match.group('surface'),
                numeric_grade=int(ngc_match.group('numeric')) if ngc_match.group('numeric') else None,
                designation=f"{ngc_match.group('designation') or ''}{ngc_match.group('extra') or ''}".strip() or None,
                certification_number=cert_match.group(1) if cert_match else None,
            )
            return result
        
        # Check for PCGS
        pcgs_match = self.PCGS_GRADE_PATTERN.search(text)
        if pcgs_match:
            result['is_slabbed'] = True
            cert_match = re.search(r'(?:PCGS|cert)\s*#?\s*(\d{7,})', text, re.I)
            result['slab_grade'] = SlabGrade(
                service=GradingService.PCGS,
                grade=pcgs_match.group('grade'),
                numeric_grade=int(pcgs_match.group('numeric')) if pcgs_match.group('numeric') else None,
                certification_number=cert_match.group(1) if cert_match else None,
            )
            return result
        
        # Raw coin grading
        raw_match = self.RAW_GRADE_PATTERN.search(title)
        if raw_match:
            grade = raw_match.group('grade').strip()
            qualifier = raw_match.group('qualifier')
            
            surface_issues = None
            if qualifier:
                issue_keywords = ['altered surface', 'tooled', 'scratches', 
                                 'smoothed', 'cleaned', 'corrosion', 'porosity']
                for keyword in issue_keywords:
                    if keyword in qualifier.lower():
                        surface_issues = qualifier.strip()
                        break
            
            result['raw_grade'] = RawGrade(
                grade=grade,
                qualifier=qualifier.strip() if qualifier else None
            )
            result['surface_issues'] = surface_issues
        
        return result
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PROVENANCE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _parse_provenance(self, description: str) -> Provenance:
        """Extract provenance from description"""
        entries = []
        collection_name = None
        raw_text = ""
        
        # Look for "From the X Collection"
        collection_match = re.search(
            r'From the\s+([^.]+Collection[^.]*)\.',
            description
        )
        if collection_match:
            collection_name = collection_match.group(1).strip()
            raw_text = collection_match.group(0)
            
            entries.append(ProvenanceEntry(
                source_type="collection",
                source_name=collection_name,
                raw_text=raw_text
            ))
        
        # Look for "Ex" provenance
        ex_matches = re.finditer(
            r'Ex\s+([^,]+?)(?:,\s*([^.]+))?\.?',
            description
        )
        
        for match in ex_matches:
            source = match.group(1).strip()
            extra = match.group(2).strip() if match.group(2) else None
            
            if 'auction' in source.lower() or 'sale' in source.lower():
                source_type = "auction"
            elif 'collection' in source.lower():
                source_type = "collection"
            else:
                source_type = "dealer"
            
            entries.append(ProvenanceEntry(
                source_type=source_type,
                source_name=source,
                notes=extra,
                raw_text=match.group(0)
            ))
            
            raw_text += " " + match.group(0)
        
        return Provenance(
            entries=entries,
            collection_name=collection_name,
            raw_text=raw_text.strip()
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AUCTION INFO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _get_auction_info(self, auction_id: int, lot_number: int) -> AuctionInfo:
        """Extract auction metadata"""
        
        auction_name = ""
        if self.soup:
            breadcrumb = self.soup.find('a', href=re.compile(f'saleNo={auction_id}'))
            if breadcrumb:
                auction_name = breadcrumb.get_text(strip=True)
        
        # Determine auction type
        auction_type = HeritageAuctionType.SHOWCASE
        if 'Signature' in auction_name:
            auction_type = HeritageAuctionType.SIGNATURE
        elif 'Weekly' in auction_name:
            auction_type = HeritageAuctionType.WEEKLY
        elif 'Monthly' in auction_name:
            auction_type = HeritageAuctionType.MONTHLY
        
        # Get sale status and price
        is_sold = False
        sold_price = None
        estimate_low = None
        estimate_high = None
        bids = None
        
        if self.soup:
            sold_text = self.soup.find(string=re.compile(r'Sold on|Price Realized'))
            if sold_text:
                is_sold = True
                # Try to extract price
                price_match = re.search(r'\$?([\d,]+)', str(sold_text.find_next()))
                if price_match:
                    sold_price = int(price_match.group(1).replace(',', ''))
            
            # Estimates
            est_text = self.soup.find(string=re.compile(r'Estimate'))
            if est_text:
                est_match = re.search(r'\$?([\d,]+)\s*-\s*\$?([\d,]+)', str(est_text.find_next()))
                if est_match:
                    estimate_low = int(est_match.group(1).replace(',', ''))
                    estimate_high = int(est_match.group(2).replace(',', ''))
            
            # Bids
            bids_text = self.soup.find(string=re.compile(r'(\d+)\s+bids?', re.I))
            if bids_text:
                bids_match = re.search(r'(\d+)\s+bids?', str(bids_text), re.I)
                if bids_match:
                    bids = int(bids_match.group(1))
        
        # Get auction date
        auction_date = None
        date_match = re.search(
            r'(\d{4})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+)',
            auction_name
        )
        if date_match:
            try:
                auction_date = datetime.strptime(
                    f"{date_match.group(1)} {date_match.group(2)} {date_match.group(3)}",
                    "%Y %B %d"
                ).date()
            except ValueError:
                pass
        
        return AuctionInfo(
            auction_id=auction_id,
            auction_name=auction_name,
            auction_type=auction_type,
            lot_number=lot_number,
            auction_date=auction_date,
            sold_price_usd=sold_price,
            estimate_low_usd=estimate_low,
            estimate_high_usd=estimate_high,
            is_sold=is_sold,
            bids=bids,
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # IMAGES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _get_images(self) -> list[HeritageImage]:
        """Extract image URLs from page"""
        images = []
        
        if not self.soup:
            return images
        
        # Find main coin images - Heritage uses heritagestatic.com and cloudfront CDN
        img_patterns = [
            re.compile(r'heritagestatic\.com'),
            re.compile(r'cloudfront\.net/images'),
            re.compile(r'd1lfxha3ugu3d4\.cloudfront\.net'),
        ]
        
        for i, img in enumerate(self.soup.find_all('img')):
            url = img.get('src', '') or img.get('data-src', '')
            if not url:
                continue
            
            # Check if URL matches our patterns
            if not any(p.search(url) for p in img_patterns):
                continue
            
            if 'logo' in url.lower() or 'icon' in url.lower():
                continue
            
            # Determine image type
            img_type = "coin"
            caption = img.get('alt', '').lower()
            
            if 'ngc' in caption or 'photovision' in url.lower():
                source = "ngc_photovision"
            elif 'pcgs' in caption:
                source = "heritage"
                img_type = "slab_front"
            else:
                source = "heritage"
            
            # Upgrade to high-res if possible
            url_full = url.replace('/thumb/', '/').replace('/sm/', '/lg/')
            
            images.append(HeritageImage(
                url=url,
                url_full_res=url_full,
                index=i,
                image_type=img_type,
                source=source
            ))
        
        # Also look for high-res image links
        for link in self.soup.find_all('a', href=re.compile(r'\.(?:jpg|jpeg|png)', re.I)):
            url = link.get('href', '')
            if any(p.search(url) for p in img_patterns):
                if not any(img.url == url for img in images):
                    images.append(HeritageImage(
                        url=url,
                        url_full_res=url,
                        index=len(images),
                        image_type="coin",
                        source="heritage"
                    ))
        
        return images
