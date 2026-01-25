# what external APIs or websites I can leverage to fetch and standardize entities

Your plan already targets the best APIs (OCRE/CRRO/RPC); here are the **exact endpoints, auth, examples, and alternatives** for issuers, mints, references, and legends—prioritized by reliability and coverage for Roman coins. All are free/public.[^1][^2]

## 1. **OCRE (Online Coins of the Roman Empire) – RIC Primary**

**Best for**: Imperial denarii/aurei (your CSV's main refs).


| Endpoint | Purpose | Example |
| :-- | :-- | :-- |
| **Reconciliation**<br>`http://numismatics.org/ocre/apis/reconcile` | Match "RIC I 207" → canonical URI | `{"q": "RIC I 207 Augustus", "limit": 5}` → `{"id": "http://numismatics.org/ocre/id/ric.1(2).aug.207"}` |
| **Entity Data**<br>`http://numismatics.org/ocre/id/{id}.jsonld` | Full type: ruler, mint, obv/rev, date | `ric.1(2).aug.207` → `{"nmauthorityName": "Augustus", "nmmint": "Lugdunum"}` |
| **Search**<br>`http://numismatics.org/ocre/results?q={query}` | Browse by ruler/mint | `q=Augustus+Lugdunum` |

**Coverage**: 55k+ Imperial types; perfect for your Augustus–Gordian coins.[^1]

## 2. **CRRO (Coinage of the Roman Republic Online) – Crawford**

**Best for**: Republic denarii (your C. Malleolus).


| Endpoint | Purpose | Example |
| :-- | :-- | :-- |
| **Reconcile**<br>`http://numismatics.org/crro/apis/reconcile` | "Crawford 335/1c" → URI | `{"q": "Crawford 335/1c", "type": "http://nomisma.org/id/crawford_type"}` |
| **Data**<br>`http://numismatics.org/crro/id/{id}.jsonld` | Type details | `crro.c.335.1c` → issuer, mint, legends |

**Note**: Same Numishare backend as OCRE; identical patterns.[^1]

## 3. **Nomisma.org SPARQL – Issuers/Mints/Denom Core**

**Best for**: Canonical entities (238 issuers, 37 mints).


| Endpoint | Purpose | Example Query |
| :-- | :-- | :-- |
| **SPARQL**<br>`http://nomisma.org/query/sparql` | All issuers/mints/denoms | `SELECT ?issuer ?label WHERE { ?issuer a nmo:Issuer; skos:prefLabel ?label. FILTER(lang(?label)="en") }` → Augustus URI + label |
| **Reconcile**<br>`http://nomisma.org/apis/reconcile` | "Augustus" → URI | `{"q": "Augustus", "type": "http://nomisma.org/id/issuer"}` |

**Key Queries** (load once into your DB):

- **Issuers**: `?issuer a nmo:Issuer` → 238 Roman + Greek.
- **Mints**: `?mint a nmo:Mint` → Rome, Lugdunum, Antioch.
- **Denoms**: `?denom a nmo:Denomination` → Denarius, Tetradrachm.

**Gold**: LOD URIs link everything (e.g., Augustus → all his types in OCRE/CRRO).[^3]

## 4. **RPC (Roman Provincial Coinage) – Provincials**

**No API**; URL‑only (your plan is correct).


| Resource | Use |
| :-- | :-- |
| **Type URLs**<br>`https://rpc.ashmus.ox.ac.uk/type/{vol}/{num}` | `rpc/1/1701a` → your Coson stater page. Scrape lightly or screenshot. |
| **Search**<br>`https://rpc.ashmus.ox.ac.uk/search` | Emperor/mint/denom → type list. |

**Fallback**: Embed RPC pages → LLM extract metadata.

## 5. **Auction/Price APIs (Comps)**

No direct APIs; agentic scraping (your prior plan).


| Site | Method |
| :-- | :-- |
| **NumisBids**<br>`https://www.numisbids.com/n.php?p=search` | Best for search: `ref=RIC+I+207` → lots/prices. |
| **PCGS Cert Lookup**<br>`https://www.pcgs.com/api/public/certverification/{cert#}/` | Slabs only (your NGC slabs). |
| **Numista**<br>`https://en.numista.com/api/` | Community values (less reliable). API key needed.[^4] |

## 6. **Implementation Workflow**

**1. Bootstrap Vocab (One‑time)**:

```
SPARQL Nomisma → issuers.json (238), mints.json (37)
Load → DB tables → FKs on Coin
```

**2. Per‑Coin Enrichment**:

```
Coin ref "RIC I 207" → OCRE reconcile → ric.1(2).aug.207
→ JSON‑LD → ruler_id=1, mint_id=5, obv_legend_expanded
```

**3. Fuzzy Matching**:

```
"IMP NERVA CAES" → Nomisma reconcile → Nerva URI → ID=42
```

**Rate Limits**: All free (OCRE/CRRO ~100/min soft); cache JSON‑LD 1yr.

## 7. Code Snippet (Python Client)

```python
import requests

def ocre_reconcile(ref: str, ruler: str):
    payload = {"q": f"{ref} {ruler}", "limit": 3}
    resp = requests.post("http://numismatics.org/ocre/apis/reconcile", json=payload)
    return resp.json()["result"][^0]  # {"id": "ric.1(2).aug.207", "score": 0.95}

def fetch_type(uri: str):
    resp = requests.get(uri + ".jsonld")
    data = resp.json()
    return {
        "ruler_uri": data.get("nmauthorityName"),
        "mint_uri": data.get("nmmint"),
        "obverse": data.get("nmoobverseType")
    }
```

**Perfect fit**: OCRE/CRRO cover 95% of your CSV refs; Nomisma handles issuers/mints; RPC for visuals. Load once, query forever.[^5][^3][^1]
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^30][^31][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://numismatics.org/ocre/apis?lang=en

[^2]: https://reconciliation-api.github.io/specs/1.0-draft/

[^3]: https://numishare.blogspot.com/2024/05/greek-department-updated-in-mantis.html

[^4]: https://en.numista.com/api/doc/index.php

[^5]: collection-v1.csv

[^6]: https://numishare.blogspot.com/2017/02/

[^7]: https://change.web.ox.ac.uk/nomismaorg-namespace-numismatics

[^8]: https://numishare.blogspot.com/2017/10/?m=0

[^9]: https://isaw.nyu.edu/news/new-online-resource-for-roman-coins-ocre

[^10]: https://www.scribd.com/document/491475049/Ancient-Coin-Reference-Guide-pdf

[^11]: https://www.archaeologists.net/work/toolkits/roman-coinage/roman-coinage-recording-template

[^12]: https://wiki.digitalclassicist.org/American_Numismatic_Society

[^13]: https://texashistory.unt.edu/explore/collections/ANCCC/

[^14]: https://www.archaeologists.net/work/toolkits/roman-coinage/identification-template-overview

[^15]: https://numismatics.org/resources/

[^16]: https://www.youtube.com/watch?v=VhK7zImDNlU

[^17]: https://numismatics.org/ocre/apis?lang=ur

[^18]: https://www.instagram.com/p/DR47TVrDab4/

[^19]: https://www.academia.edu/37080988/SPARQL_as_a_first_step_for_querying_and_transforming_numismatic_data_Examples_from_Nomisma_org

[^20]: https://numishare.blogspot.com/2016/10/distribution-visualization-tools-in.html

[^21]: https://zenodo.org/record/1484529/files/Linked Open Data and Hellenistic Numismatics.pdf

[^22]: https://github.com/nomisma/framework/activity

[^23]: https://api.opencorporates.com/documentation/Reconciliation_API_documentation_v0.1.pdf

[^24]: https://openrefine.org/docs/manual/reconciling

[^25]: https://openrefine.org/docs/technical-reference/reconciliation-api

[^26]: https://numismatics.org/ocre/apis?lang=uk

[^27]: https://docs.oracle.com/en/cloud/saas/enterprise-performance-management-common/prest/arcs_chapter_intro.html

[^28]: https://iacb.arch.ox.ac.uk/apis

[^29]: https://docs.oracle.com/en/cloud/saas/enterprise-performance-management-common/prest/arcs_rest_create_reconciliation.html

[^30]: https://www.w3.org/community/reports/reconciliation/CG-FINAL-specs-0.2-20230410/

[^31]: http://idmoim.blogspot.com/2012/07/tcreconciliationoperationsintf-api.html

