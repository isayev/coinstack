"""Roman ruler data with reign dates.

This module provides reign dates for Roman and related ancient rulers.
Dates are stored as integers:
- Negative numbers = BC (e.g., -27 = 27 BC)
- Positive numbers = AD (e.g., 14 = AD 14)
"""

# Dictionary of rulers with their reign dates
# Format: "Ruler Name": (reign_start, reign_end)
RULERS = {
    # Roman Republic - Key figures (using their active political period)
    "C. Malleolus": (-96, -96),
    "L. Sulla": (-82, -79),
    "Pompey": (-49, -48),
    "Julius Caesar": (-49, -44),
    "Brutus": (-44, -42),
    "Cassius": (-44, -42),
    "Mark Antony": (-44, -30),
    "Octavian": (-44, -27),
    
    # Julio-Claudian Dynasty
    "Augustus": (-27, 14),
    "Tiberius": (14, 37),
    "Caligula": (37, 41),
    "Gaius": (37, 41),  # Alternate name for Caligula
    "Claudius": (41, 54),
    "Nero": (54, 68),
    
    # Year of Four Emperors
    "Galba": (68, 69),
    "Otho": (69, 69),
    "Vitellius": (69, 69),
    
    # Flavian Dynasty
    "Vespasian": (69, 79),
    "Titus": (79, 81),
    "Domitian": (81, 96),
    
    # Nerva-Antonine Dynasty
    "Nerva": (96, 98),
    "Trajan": (98, 117),
    "Hadrian": (117, 138),
    "Antoninus Pius": (138, 161),
    "Marcus Aurelius": (161, 180),
    "Lucius Verus": (161, 169),
    "Commodus": (177, 192),
    
    # Year of Five Emperors
    "Pertinax": (193, 193),
    "Didius Julianus": (193, 193),
    
    # Severan Dynasty
    "Septimius Severus": (193, 211),
    "Caracalla": (198, 217),
    "Geta": (209, 211),
    "Macrinus": (217, 218),
    "Diadumenian": (218, 218),
    "Elagabalus": (218, 222),
    "Severus Alexander": (222, 235),
    
    # Crisis of the Third Century
    "Maximinus I": (235, 238),
    "Maximinus Thrax": (235, 238),
    "Gordian I": (238, 238),
    "Gordian II": (238, 238),
    "Pupienus": (238, 238),
    "Balbinus": (238, 238),
    "Gordian III": (238, 244),
    "Philip I": (244, 249),
    "Philip the Arab": (244, 249),
    "Philip II": (247, 249),
    "Trajan Decius": (249, 251),
    "Decius": (249, 251),
    "Herennius Etruscus": (251, 251),
    "Hostilian": (251, 251),
    "Trebonianus Gallus": (251, 253),
    "Volusian": (251, 253),
    "Aemilian": (253, 253),
    "Valerian": (253, 260),
    "Valerian I": (253, 260),
    "Gallienus": (253, 268),
    "Salonina": (253, 268),
    "Saloninus": (260, 260),
    "Postumus": (260, 269),
    "Laelianus": (269, 269),
    "Marius": (269, 269),
    "Victorinus": (269, 271),
    "Tetricus I": (271, 274),
    "Tetricus II": (273, 274),
    "Claudius II": (268, 270),
    "Claudius Gothicus": (268, 270),
    "Quintillus": (270, 270),
    "Aurelian": (270, 275),
    "Tacitus": (275, 276),
    "Florianus": (276, 276),
    "Probus": (276, 282),
    "Carus": (282, 283),
    "Carinus": (283, 285),
    "Numerian": (283, 284),
    
    # Tetrarchy and Constantine
    "Diocletian": (284, 305),
    "Maximian": (286, 305),
    "Constantius I": (293, 306),
    "Constantius Chlorus": (293, 306),
    "Galerius": (293, 311),
    "Severus II": (306, 307),
    "Maxentius": (306, 312),
    "Maximinus II": (305, 313),
    "Maximinus Daia": (305, 313),
    "Licinius": (308, 324),
    "Licinius I": (308, 324),
    "Licinius II": (317, 324),
    "Constantine I": (306, 337),
    "Constantine the Great": (306, 337),
    "Crispus": (317, 326),
    "Constantine II": (337, 340),
    "Constans": (337, 350),
    "Constans I": (337, 350),
    "Constantius II": (337, 361),
    "Magnentius": (350, 353),
    "Decentius": (351, 353),
    "Vetranio": (350, 350),
    "Julian II": (360, 363),
    "Julian": (360, 363),
    "Julian the Apostate": (360, 363),
    "Jovian": (363, 364),
    
    # Valentinian Dynasty
    "Valentinian I": (364, 375),
    "Valens": (364, 378),
    "Gratian": (367, 383),
    "Valentinian II": (375, 392),
    "Magnus Maximus": (383, 388),
    
    # Theodosian Dynasty
    "Theodosius I": (379, 395),
    "Theodosius the Great": (379, 395),
    "Arcadius": (383, 408),
    "Honorius": (393, 423),
    "Theodosius II": (408, 450),
    "Constantius III": (421, 421),
    "Valentinian III": (425, 455),
    "Marcian": (450, 457),
    
    # Later Western Empire
    "Petronius Maximus": (455, 455),
    "Avitus": (455, 456),
    "Majorian": (457, 461),
    "Libius Severus": (461, 465),
    "Anthemius": (467, 472),
    "Olybrius": (472, 472),
    "Glycerius": (473, 474),
    "Julius Nepos": (474, 480),
    "Romulus Augustulus": (475, 476),
    
    # Eastern/Byzantine (early)
    "Leo I": (457, 474),
    "Leo II": (474, 474),
    "Zeno": (474, 491),
    "Basiliscus": (475, 476),
    "Anastasius I": (491, 518),
    "Justin I": (518, 527),
    "Justinian I": (527, 565),
    "Justinian": (527, 565),
    "Justin II": (565, 578),
    "Tiberius II": (578, 582),
    "Maurice": (582, 602),
    "Phocas": (602, 610),
    "Heraclius": (610, 641),
    
    # Notable Empresses
    "Livia": (-27, 14),
    "Agrippina Senior": (14, 33),
    "Agrippina Junior": (49, 59),
    "Messalina": (41, 48),
    "Faustina I": (138, 140),
    "Faustina the Elder": (138, 140),
    "Faustina II": (145, 175),
    "Faustina the Younger": (145, 175),
    "Lucilla": (164, 182),
    "Julia Domna": (193, 217),
    "Julia Paula": (219, 220),
    "Julia Soaemias": (218, 222),
    "Julia Maesa": (218, 224),
    "Julia Mamaea": (222, 235),
    "Orbiana": (225, 227),
    "Tranquillina": (241, 244),
    "Otacilia Severa": (244, 249),
    "Mariniana": (253, 254),
    "Cornelia Supera": (253, 253),
    "Helena": (306, 330),
    "Fausta": (307, 326),
    "Theodora": (293, 306),
    "Aelia Flaccilla": (379, 386),
    "Galla Placidia": (421, 450),
    "Pulcheria": (414, 453),
    "Eudocia": (421, 460),
    "Verina": (457, 484),
    "Ariadne": (474, 515),
    "Theodora": (527, 548),
    
    # Provincial/Client rulers
    "Coson": (-54, -29),
    "Herod the Great": (-37, -4),
    "Herod Antipas": (-4, 39),
    "Agrippa I": (37, 44),
    "Agrippa II": (48, 100),
    
    # Usurpers/Brief reigns (additional)
    "Carausius": (286, 293),
    "Allectus": (293, 296),
    "Domitius Domitianus": (297, 298),
}


def get_reign_dates(ruler_name: str) -> tuple[int | None, int | None]:
    """Get reign dates for a ruler.
    
    Args:
        ruler_name: Name of the ruler (case-insensitive lookup)
        
    Returns:
        Tuple of (reign_start, reign_end) or (None, None) if not found
    """
    if not ruler_name:
        return None, None
    
    # Try exact match first
    if ruler_name in RULERS:
        return RULERS[ruler_name]
    
    # Try case-insensitive match
    ruler_lower = ruler_name.lower()
    for name, dates in RULERS.items():
        if name.lower() == ruler_lower:
            return dates
    
    # Try partial match (ruler name contains or is contained in)
    for name, dates in RULERS.items():
        if name.lower() in ruler_lower or ruler_lower in name.lower():
            return dates
    
    return None, None


def get_all_rulers() -> dict[str, tuple[int, int]]:
    """Get all rulers and their reign dates."""
    return RULERS.copy()
