/**
 * Reference Links - Build validated external links for numismatic references
 *
 * Only generates links that are likely to work based on reference format.
 * Use backend POST /api/v2/catalog/parse for authoritative parsing.
 *
 * @module lib/referenceLinks
 */

/** Fallback list when GET /api/v2/catalog/systems is unavailable (display order). */
export const SUPPORTED_CATALOGS_FALLBACK: string[] = [
  "RIC",
  "RPC",
  "RRC",
  "RSC",
  "DOC",
  "BMCRR",
  "BMCRE",
  "SNG",
  "Cohen",
  "Calicó",
  "Sear",
  "Sydenham",
];

export interface ExternalLink {
  /** Display name */
  name: string;
  /** Full URL */
  url: string;
  /** Whether this link is validated for the reference type */
  validated: boolean;
}

export interface CatalogReference {
  catalog: string;
  number: string;
  volume?: string | null;
  is_primary?: boolean;
  notes?: string | null;
  variant_notes?: string | null;
  raw_text?: string | null;
  /** Origin: user | import | scraper | llm_approved | catalog_lookup */
  source?: string | null;
  variant?: string | null;   // e.g. "a", "b" (RIC, Crawford)
  mint?: string | null;     // RIC mint code
  supplement?: string | null;  // RPC S, S2
  collection?: string | null;  // SNG collection
}

/**
 * Build external links for a set of references.
 * Returns only links that are valid for the given reference types.
 */
export function buildExternalLinks(references: CatalogReference[]): ExternalLink[] {
  const links: ExternalLink[] = [];
  const addedLinks = new Set<string>();

  for (const ref of references) {
    const refString = formatReference(ref);
    const catalog = (ref.catalog || "").toUpperCase();

    // OCRE - Online Coins of the Roman Empire (RIC only)
    if (catalog === "RIC" && !addedLinks.has("OCRE")) {
      const volPart = (ref.volume || "").toString().toLowerCase();
      links.push({
        name: "OCRE",
        url: volPart
          ? `https://numismatics.org/ocre/results?q=ric_id:ric.${volPart}.*`
          : `https://numismatics.org/ocre/results?q=${encodeURIComponent(refString)}`,
        validated: true,
      });
      addedLinks.add("OCRE");
    }

    // CRRO - Coinage of the Roman Republic Online (Crawford/RRC only)
    if ((catalog === "RRC" || catalog === "CRAWFORD") && !addedLinks.has("CRRO")) {
      const number = (ref.number || "").replace(/\//g, "-");
      links.push({
        name: "CRRO",
        url: `https://numismatics.org/crro/id/rrc-${number}`,
        validated: true,
      });
      addedLinks.add("CRRO");
    }

    // RPC Online - Roman Provincial Coinage
    if (catalog === "RPC" && !addedLinks.has("RPC")) {
      links.push({
        name: "RPC Online",
        url: `https://rpc.ashmus.ox.ac.uk/search?q=${encodeURIComponent(refString)}`,
        validated: true,
      });
      addedLinks.add("RPC");
    }
  }

  // Always add general search links (less validated but useful)
  if (references.length > 0) {
    const primaryRef = references[0];
    const searchQuery = formatReference(primaryRef);

    // ACSearch - works for any reference
    if (!addedLinks.has('ACSearch')) {
      links.push({
        name: 'ACSearch',
        url: `https://www.acsearch.info/search.html?search=${encodeURIComponent(searchQuery)}`,
        validated: false,
      });
      addedLinks.add('ACSearch');
    }

    // Wildwinds - general search
    if (!addedLinks.has('Wildwinds')) {
      links.push({
        name: 'Wildwinds',
        url: `http://www.wildwinds.com/coins/ric/search.php?search=${encodeURIComponent(searchQuery)}`,
        validated: false,
      });
      addedLinks.add('Wildwinds');
    }

    // CoinArchives - auction records
    if (!addedLinks.has('CoinArchives')) {
      links.push({
        name: 'CoinArchives',
        url: `https://www.coinarchives.com/a/results.php?search=${encodeURIComponent(searchQuery)}`,
        validated: false,
      });
      addedLinks.add('CoinArchives');
    }
  }

  return links;
}

/**
 * Format a catalog reference for display.
 * Includes volume, supplement (RPC S/S2), mint (RIC), collection (SNG) when present.
 */
export function formatReference(ref: CatalogReference): string {
  const parts: string[] = [ref.catalog];
  if (ref.volume) parts.push(ref.volume);
  if (ref.supplement) parts.push(ref.supplement);
  if (ref.mint) parts.push(ref.mint);
  if (ref.collection) parts.push(ref.collection);
  parts.push(ref.number);
  return parts.filter(Boolean).join(" ");
}

/**
 * Best-effort client-side parse of a reference string.
 * For authoritative parsing and validation use the backend parse API (POST /api/v2/catalog/parse).
 */
export function parseReference(refString: string): CatalogReference | null {
  const s = refString.trim();
  if (!s) return null;

  // RIC: RIC II 118, RIC IV.1 289c, RIC VII Ticinum 123
  const ricMatch = s.match(/^(RIC)\s+([IVX]+(?:[.\-/]\d+)?)\s+(?:([A-Za-z]+)\s+)?(\d+[a-z]?)$/i);
  if (ricMatch) {
    const [, catalog, volume, mint, number] = ricMatch;
    const out: CatalogReference = { catalog: catalog!.toUpperCase(), number: number! };
    if (volume) out.volume = volume.toUpperCase();
    if (mint) out.mint = mint;
    return out;
  }

  // RPC: RPC I 1234, RPC I S 123
  const rpcMatch = s.match(/^(RPC)\s+([IVX]+|\d+)(?:\s+(S\d?))?\s+(\d+[a-z]?)$/i);
  if (rpcMatch) {
    const [, catalog, vol, supp, number] = rpcMatch;
    const out: CatalogReference = { catalog: catalog!.toUpperCase(), number: number! };
    if (vol) out.volume = /^\d+$/.test(vol) ? vol : vol.toUpperCase();
    if (supp) out.supplement = supp.toUpperCase();
    return out;
  }

  // Crawford/RRC: Crawford 335/1c, RRC 335/1 (display as RRC)
  const crawfordMatch = s.match(/^(Crawford|RRC)\s+(.+)$/i);
  if (crawfordMatch) {
    return { catalog: "RRC", number: crawfordMatch[2]!.trim() };
  }

  // SNG: SNG Cop 123, SNG ANS 336
  const sngMatch = s.match(/^(SNG)\s+([A-Za-z][A-Za-z.]*?)\s+(\d+[a-z]?)$/i);
  if (sngMatch) {
    return {
      catalog: "SNG",
      number: sngMatch[3]!,
      collection: sngMatch[2]!.trim(),
    };
  }

  // DOC: DOC 1 234, DOC III 100
  const docMatch = s.match(/^(DOC)\s+([IVX]+|\d+)\s+(\d+[a-z]?)$/i);
  if (docMatch) {
    return {
      catalog: "DOC",
      volume: /^\d+$/.test(docMatch[2]!) ? docMatch[2]! : docMatch[2]!.toUpperCase(),
      number: docMatch[3]!,
    };
  }

  // Generic: CatalogName number (e.g. Sear 3124, Cohen 382, BMCRR 100)
  const simpleMatch = s.match(/^([A-Za-zÀ-ÿ.\s]+?)\s+(\d+[a-z]?(?:\/\d+[a-z]?)?)$/);
  if (simpleMatch) {
    return {
      catalog: simpleMatch[1]!.trim(),
      number: simpleMatch[2]!,
    };
  }

  return null;
}
