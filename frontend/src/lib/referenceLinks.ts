/**
 * Reference Links - Build validated external links for numismatic references
 * 
 * Only generates links that are likely to work based on reference format.
 * 
 * @module lib/referenceLinks
 */

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
    const refString = `${ref.catalog} ${ref.number}`;

    // OCRE - Online Coins of the Roman Empire (RIC only)
    // Format: RIC I 207, RIC II 118, etc.
    const ricMatch = refString.match(/^RIC\s+([IVX]+)\s+(.+)$/i);
    if (ricMatch && !addedLinks.has('OCRE')) {
      const [, volume] = ricMatch;
      // OCRE search works better than direct ID lookup
      links.push({
        name: 'OCRE',
        url: `https://numismatics.org/ocre/results?q=ric_id:ric.${volume.toLowerCase()}.*`,
        validated: true,
      });
      addedLinks.add('OCRE');
    }

    // CRRO - Coinage of the Roman Republic Online (Crawford/RRC only)
    // Format: Crawford 335/1c, RRC 494/43
    const rrcMatch = refString.match(/^(?:RRC|Crawford)\s+(\d+\/\d+[a-z]?)$/i);
    if (rrcMatch && !addedLinks.has('CRRO')) {
      const [, number] = rrcMatch;
      const normalized = number.replace('/', '-');
      links.push({
        name: 'CRRO',
        url: `https://numismatics.org/crro/id/rrc-${normalized}`,
        validated: true,
      });
      addedLinks.add('CRRO');
    }

    // RPC Online - Roman Provincial Coinage
    // Format: RPC I 1234, RPC II 567
    const rpcMatch = refString.match(/^RPC\s+([IVX]+)\s+(\d+)$/i);
    if (rpcMatch && !addedLinks.has('RPC')) {
      links.push({
        name: 'RPC Online',
        url: `https://rpc.ashmus.ox.ac.uk/search?q=${encodeURIComponent(refString)}`,
        validated: true,
      });
      addedLinks.add('RPC');
    }
  }

  // Always add general search links (less validated but useful)
  if (references.length > 0) {
    const primaryRef = references[0];
    const searchQuery = `${primaryRef.catalog} ${primaryRef.number}`;

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
 * Format a catalog reference for display
 */
export function formatReference(ref: CatalogReference): string {
  let formatted = ref.catalog;
  if (ref.volume) {
    formatted += ` ${ref.volume}`;
  }
  formatted += ` ${ref.number}`;
  return formatted;
}

/**
 * Parse a reference string into components
 * Handles formats like "RIC II 118", "Crawford 335/1c", "Sear 3124"
 */
export function parseReference(refString: string): CatalogReference | null {
  // Try RIC format: RIC II 118
  const ricMatch = refString.match(/^(RIC)\s+([IVX]+)\s+(.+)$/i);
  if (ricMatch) {
    return { catalog: ricMatch[1].toUpperCase(), volume: ricMatch[2], number: ricMatch[3] };
  }

  // Try Crawford/RRC format: Crawford 335/1c
  const crawfordMatch = refString.match(/^(Crawford|RRC)\s+(.+)$/i);
  if (crawfordMatch) {
    return { catalog: crawfordMatch[1], number: crawfordMatch[2] };
  }

  // Try simple format: Sear 3124
  const simpleMatch = refString.match(/^(\w+)\s+(.+)$/);
  if (simpleMatch) {
    return { catalog: simpleMatch[1], number: simpleMatch[2] };
  }

  return null;
}
