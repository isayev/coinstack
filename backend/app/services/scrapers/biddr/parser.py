"""
Biddr Parser

Extracts structured coin data from Biddr auction pages.
Handles multiple sub-houses (Savoca, Roma, Leu, etc.) with varying formats.
"""

import re
from typing import Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from .models import (
    BiddrCoinData, BiddrPhysicalData, BiddrCatalogReference, 
    BiddrProvenance, BiddrProvenanceEntry, BiddrImage, 
    BiddrAuctionInfo, BiddrMetal, BiddrSubHouse
)

logger = logging.getLogger(__name__)


class BiddrParser:
    """
    Parser for Biddr auction lot pages.
    
    Biddr hosts many auction houses with slightly different formats,
    but shares a common overall structure.
    """
    
    # Sub-house detection
    SUB_HOUSE_PATTERNS = {
        'savoca': BiddrSubHouse.SAVOCA,
        'roma': BiddrSubHouse.ROMA,
        'leu': BiddrSubHouse.LEU,
        'nomos': BiddrSubHouse.NOMOS,
        'kunker': BiddrSubHouse.KUNKER,
        'künker': BiddrSubHouse.KUNKER,
        'nummitra': BiddrSubHouse.NUMMITRA,
        'rexnumis': BiddrSubHouse.REXNUMIS,
        'coin-cabinet': BiddrSubHouse.COIN_CABINET,
        'agora': BiddrSubHouse.AGORA,
        'nac': BiddrSubHouse.NUMISMATICA_ARS_CLASSICA,
        'pecunem': BiddrSubHouse.PECUNEM,
    }
    
    # Reference patterns
    REFERENCE_PATTERNS = [
        # RIC with volume
        (re.compile(r'RIC\s+([IVX]+(?:\.\d)?)\s+(\d+[a-z]?)(?:\s*\(([^)]+)\))?', re.I), 'RIC'),
        # Crawford for Roman Republic
        (re.compile(r'(?:Crawford|Cr\.?)\s*(\d+/\d+[a-z]?)', re.I), 'Crawford'),
        # Sydenham
        (re.compile(r'Sydenham\s+(\d+[a-z]?)', re.I), 'Sydenham'),
        # RSC
        (re.compile(r'RSC\s+(\d+[a-z]?)', re.I), 'RSC'),
        # RPC
        (re.compile(r'RPC\s+([IVX]+)\s+(\d+)', re.I), 'RPC'),
        # Sear
        (re.compile(r'Sear\s+(\d+)', re.I), 'Sear'),
        # SNG
        (re.compile(r'SNG\s+(\w+)\s+(\d+)', re.I), 'SNG'),
        # BMC
        (re.compile(r'BMC\s+(\d+)', re.I), 'BMC'),
        # Cohen
        (re.compile(r'Cohen\s+(\d+)', re.I), 'Cohen'),
        # Calicó
        (re.compile(r'Calicó\s+(\d+[a-z]?)', re.I), 'Calicó'),
    ]
    
    # Grade patterns (English and German)
    GRADE_PATTERNS = [
        # English grades
        (r'\b(FDC|Fleur de Coin)\b', 'FDC'),
        (r'\b(Superb EF|Choice EF|Near EF|EF|Extremely Fine)\b', None),
        (r'\b(Good VF|Choice VF|Near VF|VF|Very Fine)\b', None),
        (r'\b(Good Fine|Near Fine|Fine)\b', None),
        (r'\b(VG|Very Good)\b', None),
        (r'\b(Good|Fair|Poor)\b', None),
        # German grades
        (r'\b(Stempelglanz|St)\b', 'FDC'),
        (r'\b(Vorzüglich|vzgl?\.?)\b', 'EF'),
        (r'\b(Sehr schön|ss\.?)\b', 'VF'),
        (r'\b(Schön|s\.?)\b', 'Fine'),
        (r'\b(Gering erhalten|ge\.?)\b', 'Poor'),
    ]
    
    # Metal patterns
    METAL_PATTERNS = {
        r'\bAV\b': BiddrMetal.GOLD,
        r'\bAR\b': BiddrMetal.SILVER,
        r'\bAE\b': BiddrMetal.BRONZE,
        r'\bBI\b': BiddrMetal.BILLON,
        r'\bEL\b': BiddrMetal.ELECTRUM,
        r'\bPB\b': BiddrMetal.LEAD,
        r'\bOR\b': BiddrMetal.ORICHALCUM,
        r'\bGold\b': BiddrMetal.GOLD,
        r'\bSilver\b': BiddrMetal.SILVER,
        r'\bSilber\b': BiddrMetal.SILVER,
        r'\bBronze\b': BiddrMetal.BRONZE,
    }
    
    # Denomination patterns
    DENOMINATION_PATTERNS = [
        r'\b(Aureus|Solidus|Tremissis|Semissis)\b',  # Gold
        r'\b(Denarius|Denar|Antoninianus|Quinarius|Drachm|Tetradrachm|Didrachm)\b',  # Silver
        r'\b(Sestertius|Sesterz|Dupondius|As|Semis|Quadrans|Follis)\b',  # Bronze
        r'\b(Stater|Drachme|Obol|Hemiobol|Tetrobol)\b',  # Greek
    ]
    
    def __init__(self):
        self.soup: Optional[BeautifulSoup] = None
        self.body_text: str = ""
    
    def parse(self, html: str, url: str) -> BiddrCoinData:
        """
        Parse Biddr lot page HTML into structured data.
        """
        self.soup = BeautifulSoup(html, 'html.parser')
        self.body_text = self.soup.get_text(separator='\n')
        
        # Extract IDs from URL
        lot_id = self._extract_lot_id(url)
        auction_id = self._extract_auction_id(url)
        sub_house = self._detect_sub_house(url)
        
        # Extract description section
        description = self._extract_description()
        
        # Parse the description for structured data
        title = self._extract_title(description)
        coin_type = self._parse_coin_type(description)
        physical = self._parse_physical(description)
        references = self._extract_references(description)
        grade_info = self._extract_grade(description)
        provenance = self._extract_provenance(description)
        
        # Auction info
        auction = self._parse_auction_info(auction_id)
        
        # Images
        images = self._extract_images()
        
        return BiddrCoinData(
            biddr_lot_id=lot_id,
            url=url,
            sub_house=sub_house,
            title=title,
            ruler=coin_type.get('ruler'),
            ruler_title=coin_type.get('ruler_title'),
            reign_dates=coin_type.get('reign_dates'),
            era=coin_type.get('era'),
            denomination=coin_type.get('denomination'),
            metal=coin_type.get('metal'),
            mint=coin_type.get('mint'),
            mint_date=coin_type.get('mint_date'),
            physical=physical,
            obverse_description=coin_type.get('obverse'),
            reverse_description=coin_type.get('reverse'),
            exergue=coin_type.get('exergue'),
            references=references,
            grade=grade_info.get('grade'),
            grade_german=grade_info.get('grade_german'),
            condition_notes=grade_info.get('condition_notes'),
            provenance=provenance,
            auction=auction,
            images=images,
            raw_description=description,
        )
    
    def _detect_sub_house(self, url: str) -> Optional[BiddrSubHouse]:
        """Detect which sub-house this lot belongs to"""
        url_lower = url.lower()
        for pattern, house in self.SUB_HOUSE_PATTERNS.items():
            if pattern in url_lower:
                return house
        return None
    
    def _extract_lot_id(self, url: str) -> str:
        """Extract lot ID from URL"""
        auction_match = re.search(r'[?&]a=(\d+)', url)
        lot_match = re.search(r'[?&]l=(\d+)', url)
        
        auction_id = auction_match.group(1) if auction_match else "0"
        lot_id = lot_match.group(1) if lot_match else "0"
        
        return f"{auction_id}-{lot_id}"
    
    def _extract_auction_id(self, url: str) -> Optional[int]:
        """Extract auction ID from URL"""
        match = re.search(r'[?&]a=(\d+)', url)
        return int(match.group(1)) if match else None
    
    def _extract_description(self) -> str:
        """Extract the main description section"""
        # Look for description section markers
        desc_match = re.search(
            r'Description\s*\n([\s\S]*?)(?:Question|Bidding|\n#|\Z)',
            self.body_text,
            re.I
        )
        if desc_match:
            return desc_match.group(1).strip()
        
        # Fallback: look for coin-related content
        lines = self.body_text.split('\n')
        desc_lines = []
        in_desc = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Start capturing when we see typical coin description patterns
            if re.search(r'\b(circa|AD|BC|mm|g\b)', line, re.I):
                in_desc = True
            if in_desc:
                if 'Question about' in line or 'Bidding' in line:
                    break
                desc_lines.append(line)
        
        return '\n'.join(desc_lines)
    
    def _extract_title(self, description: str) -> str:
        """Extract the title/first line of description"""
        lines = [l.strip() for l in description.split('\n') if l.strip()]
        if lines:
            # First substantial line is usually the title
            for line in lines[:3]:
                if len(line) > 10:
                    return line
        return ""
    
    def _parse_coin_type(self, description: str) -> dict:
        """Parse coin type, ruler, denomination, metal, mint from description"""
        result = {}
        
        # Ruler - look for names with dates
        ruler_patterns = [
            # Roman emperors
            r'\b(Augustus|Tiberius|Caligula|Claudius|Nero|Galba|Otho|Vitellius|'
            r'Vespasian|Titus|Domitian|Nerva|Trajan|Hadrian|Antoninus Pius|'
            r'Marcus Aurelius|Lucius Verus|Commodus|Pertinax|Septimius Severus|'
            r'Caracalla|Geta|Macrinus|Elagabalus|Severus Alexander|Maximinus|'
            r'Gordian|Philip|Decius|Trebonianus Gallus|Volusian|Aemilian|Valerian|'
            r'Gallienus|Claudius II|Aurelian|Tacitus|Probus|Carus|Carinus|Numerian|'
            r'Diocletian|Maximian|Constantius|Galerius|Constantine|Licinius|'
            r'Constans|Constantius II|Julian|Jovian|Valentinian|Valens|Gratian|'
            r'Theodosius|Arcadius|Honorius)\b',
            # With titles
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\.\s*(As Caesar|Augusta|Caesar)',
        ]
        
        for pattern in ruler_patterns:
            match = re.search(pattern, description, re.I)
            if match:
                result['ruler'] = match.group(1) if match.lastindex >= 1 else match.group(0)
                if match.lastindex >= 2:
                    result['ruler_title'] = match.group(2)
                break
        
        # Reign dates
        dates_match = re.search(r'\b(AD|BC)\s*(\d+)(?:\s*[-–]\s*(?:AD|BC)?\s*(\d+))?\b', description)
        if dates_match:
            if dates_match.group(3):
                result['reign_dates'] = f"{dates_match.group(1)} {dates_match.group(2)}-{dates_match.group(3)}"
            else:
                result['reign_dates'] = f"{dates_match.group(1)} {dates_match.group(2)}"
        
        # Mint date (circa patterns)
        mint_date_match = re.search(r'(circa\s+)?(\d+(?:\s*[-–]\s*\d+)?)\s*(BC|AD)', description, re.I)
        if mint_date_match:
            result['mint_date'] = mint_date_match.group(0).strip()
        
        # Era detection
        if 'republic' in description.lower():
            result['era'] = 'Roman Republic'
        elif 'imperial' in description.lower() or re.search(r'\bAD\s+\d', description):
            result['era'] = 'Roman Imperial'
        elif 'greek' in description.lower():
            result['era'] = 'Greek'
        elif 'byzantine' in description.lower():
            result['era'] = 'Byzantine'
        elif 'provincial' in description.lower():
            result['era'] = 'Roman Provincial'
        
        # Metal
        for pattern, metal in self.METAL_PATTERNS.items():
            if re.search(pattern, description, re.I):
                result['metal'] = metal
                break
        
        # Denomination
        for pattern in self.DENOMINATION_PATTERNS:
            match = re.search(pattern, description, re.I)
            if match:
                result['denomination'] = match.group(1)
                break
        
        # Mint
        mint_patterns = [
            r'\b(Rome|Roma|Alexandria|Antioch|Constantinople|Lugdunum|'
            r'Siscia|Nicomedia|Cyzicus|Thessalonica|Heraclea|Aquileia|'
            r'Trier|Arles|Milan|Ravenna)\s*(?:mint)?',
        ]
        for pattern in mint_patterns:
            match = re.search(pattern, description, re.I)
            if match:
                result['mint'] = match.group(1)
                break
        
        # Obverse/Reverse descriptions
        # Look for "/" separator or "Obv:"/"Rev:" markers
        if '/' in description:
            parts = description.split('/')
            if len(parts) >= 2:
                # First part after physical specs is obverse
                obv_text = parts[0]
                # Clean up - remove physical specs
                obv_clean = re.sub(r'\d+mm[,.]?\s*\d+[,.]?\d*\s*g[,.]?\s*', '', obv_text)
                obv_clean = re.sub(r'^[^.]*\.\s*', '', obv_clean)  # Remove title part
                result['obverse'] = obv_clean.strip()
                
                # Reverse is second part up to references
                rev_text = parts[1]
                rev_end = self._find_reference_start(rev_text)
                if rev_end > 0:
                    result['reverse'] = rev_text[:rev_end].strip()
                else:
                    result['reverse'] = rev_text.strip()
        
        # Exergue
        exergue_match = re.search(r'(?:in exergue|ex\.?)[,:]?\s*([^.;]+)', description, re.I)
        if exergue_match:
            result['exergue'] = exergue_match.group(1).strip()
        
        return result
    
    def _parse_physical(self, description: str) -> BiddrPhysicalData:
        """Parse physical measurements"""
        diameter = None
        weight = None
        die_axis = None
        
        # Diameter - handles European format (20mm or 20,5mm)
        diam_match = re.search(r'(\d+)[,.]?(\d*)\s*mm', description, re.I)
        if diam_match:
            if diam_match.group(2):
                diameter = float(f"{diam_match.group(1)}.{diam_match.group(2)}")
            else:
                diameter = float(diam_match.group(1))
        
        # Weight - handles European format (3,74g or 3.74g)
        weight_match = re.search(r'(\d+)[,.](\d+)\s*g(?:m|r)?', description, re.I)
        if weight_match:
            weight = float(f"{weight_match.group(1)}.{weight_match.group(2)}")
        else:
            # Integer weight
            weight_match = re.search(r'(\d+)\s*g(?:m|r)?(?:\b|$)', description, re.I)
            if weight_match:
                weight = float(weight_match.group(1))
        
        # Die axis
        die_match = re.search(r'(\d{1,2})\s*h\b', description)
        if die_match:
            die_axis = int(die_match.group(1))
        
        return BiddrPhysicalData(
            diameter_mm=diameter,
            weight_g=weight,
            die_axis_hours=die_axis
        )
    
    def _find_reference_start(self, text: str) -> int:
        """Find where catalog references begin"""
        patterns = ['RIC', 'Crawford', 'Cr.', 'RSC', 'RPC', 'Sear', 'Sydenham', 'BMC', 'SNG', 'Cohen']
        min_idx = -1
        for pattern in patterns:
            idx = text.find(pattern)
            if idx > 0 and (min_idx < 0 or idx < min_idx):
                min_idx = idx
        return min_idx
    
    def _extract_references(self, description: str) -> list[BiddrCatalogReference]:
        """Extract all catalog references"""
        references = []
        
        for pattern, catalog in self.REFERENCE_PATTERNS:
            for match in pattern.finditer(description):
                raw = match.group(0)
                groups = match.groups()
                
                if catalog == 'RIC' and len(groups) >= 2:
                    ref = BiddrCatalogReference(
                        catalog='RIC',
                        volume=groups[0],
                        number=groups[1],
                        suffix=groups[2] if len(groups) > 2 else None,
                        raw_text=raw
                    )
                elif catalog == 'RPC' and len(groups) >= 2:
                    ref = BiddrCatalogReference(
                        catalog='RPC',
                        volume=groups[0],
                        number=groups[1],
                        raw_text=raw
                    )
                elif catalog == 'SNG' and len(groups) >= 2:
                    ref = BiddrCatalogReference(
                        catalog='SNG',
                        volume=groups[0],
                        number=groups[1],
                        raw_text=raw
                    )
                else:
                    ref = BiddrCatalogReference(
                        catalog=catalog,
                        number=groups[0] if groups else raw.split()[-1],
                        raw_text=raw
                    )
                
                # Avoid duplicates
                if not any(r.raw_text == ref.raw_text for r in references):
                    references.append(ref)
        
        return references
    
    def _extract_grade(self, description: str) -> dict:
        """Extract grade information"""
        result = {}
        
        for pattern, english_equiv in self.GRADE_PATTERNS:
            match = re.search(pattern, description, re.I)
            if match:
                grade_text = match.group(1)
                if english_equiv:
                    result['grade'] = english_equiv
                    result['grade_german'] = grade_text
                else:
                    result['grade'] = grade_text
                break
        
        # Condition notes - look for descriptions of flaws
        condition_patterns = [
            r'((?:light|minor|small|some)\s+(?:scratch|scratches|corrosion|porosity|deposits?|marks?|cleaning))',
            r'(toned|toning|patina|cabinet tone)',
            r'(flan (?:crack|flaw)s?)',
            r'(off[- ]?cent[re]+)',
        ]
        
        notes = []
        for pattern in condition_patterns:
            matches = re.findall(pattern, description, re.I)
            notes.extend(matches)
        
        if notes:
            result['condition_notes'] = ', '.join(notes)
        
        return result
    
    def _extract_provenance(self, description: str) -> BiddrProvenance:
        """Extract provenance data"""
        entries = []
        pedigree_year = None
        raw_text = ""
        
        # Look for "Ex" provenance markers
        ex_matches = re.findall(
            r'Ex\s+([^.;]+(?:\([^)]+\))?[^.;]*)',
            description,
            re.I
        )
        
        for match in ex_matches:
            raw_text = match.strip()
            
            # Parse collection/auction name
            auction_match = re.search(
                r'([^(]+?)(?:\s*\(([^)]+)\))?(?:,\s*lot\s*(\d+))?',
                raw_text
            )
            
            if auction_match:
                source_name = auction_match.group(1).strip()
                source_type = "collection"
                
                # Detect if it's an auction
                if any(x in source_name.lower() for x in ['auction', 'sale', 'numismatica']):
                    source_type = "auction"
                
                entries.append(BiddrProvenanceEntry(
                    source_type=source_type,
                    source_name=source_name,
                    date=auction_match.group(2) if auction_match.lastindex >= 2 else None,
                    lot_number=auction_match.group(3) if auction_match.lastindex >= 3 else None,
                    raw_text=raw_text
                ))
        
        # Pedigree year
        pedigree_match = re.search(r'(?:before|since|from)\s+(\d{4})', description, re.I)
        if pedigree_match:
            pedigree_year = int(pedigree_match.group(1))
        
        return BiddrProvenance(
            entries=entries,
            pedigree_year=pedigree_year,
            raw_text=raw_text
        )
    
    def _parse_auction_info(self, auction_id: Optional[int]) -> BiddrAuctionInfo:
        """Extract auction information"""
        info = BiddrAuctionInfo()
        
        if auction_id:
            info.auction_id = auction_id
        
        # Auction name from page
        auction_name_match = re.search(
            r'((?:Live|Online|Silent|Floor)\s+(?:Auction|Sale)\s*\d*[^–\n]*)',
            self.body_text,
            re.I
        )
        if auction_name_match:
            info.auction_name = auction_name_match.group(1).strip()
        
        # Lot number
        lot_match = re.search(r'Lot\s+(\d+)', self.body_text)
        if lot_match:
            info.lot_number = int(lot_match.group(1))
        
        # Price realized
        price_match = re.search(
            r'Price realized\s*[:\s]*([\d,.]+)\s*(EUR|USD|CHF|GBP)',
            self.body_text,
            re.I
        )
        if price_match:
            price_str = price_match.group(1).replace(',', '.')
            # Handle European thousands separator
            if price_str.count('.') > 1:
                price_str = price_str.replace('.', '', price_str.count('.') - 1)
            info.hammer_price = float(price_str)
            info.currency = price_match.group(2).upper()
            info.is_sold = True
        
        # Starting price
        start_match = re.search(
            r'Starting price\s*[:\s]*([\d,.]+)\s*(EUR|USD|CHF|GBP)?',
            self.body_text,
            re.I
        )
        if start_match:
            price_str = start_match.group(1).replace(',', '.')
            if price_str.count('.') > 1:
                price_str = price_str.replace('.', '', price_str.count('.') - 1)
            info.starting_price = float(price_str)
            info.estimate_low = info.starting_price
        
        # Bids
        bids_match = re.search(r'(\d+)\s*bids?', self.body_text, re.I)
        if bids_match:
            info.bids = int(bids_match.group(1))
        
        # Auction closed
        if 'auction is closed' in self.body_text.lower():
            info.is_closed = True
        
        return info
    
    def _extract_images(self) -> list[BiddrImage]:
        """Extract image URLs"""
        images = []
        
        # Find images in img tags
        for img in self.soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if not src:
                continue
            
            # Filter to auction lot images
            if 'auction_lots' in src or 'media.biddr' in src:
                if 'placeholder' not in src.lower() and 'logo' not in src.lower():
                    # Upgrade to large version
                    large_url = src.replace('.s.', '.l.').replace('.m.', '.l.')
                    
                    if not any(i.url == large_url for i in images):
                        img_type = "combined"
                        if len(images) == 0:
                            img_type = "obverse"
                        elif len(images) == 1:
                            img_type = "reverse"
                        
                        images.append(BiddrImage(
                            url=large_url,
                            url_large=large_url,
                            index=len(images),
                            image_type=img_type
                        ))
        
        # Also check for image links
        for link in self.soup.find_all('a', href=re.compile(r'\.(?:jpg|jpeg|png)', re.I)):
            href = link.get('href', '')
            if 'auction_lots' in href or 'media.biddr' in href:
                if not any(i.url == href for i in images):
                    images.append(BiddrImage(
                        url=href,
                        url_large=href,
                        index=len(images),
                        image_type="other"
                    ))
        
        return images
