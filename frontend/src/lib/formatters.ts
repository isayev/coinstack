export function formatYear(year: number | null | undefined): string {
  if (year === null || year === undefined) return '?'
  if (year === 0) return '0'
  
  if (year < 0) {
    return `${Math.abs(year)} BC`
  }
  
  return year.toString()
}

/** Minimal coin-like shape for attribution display */
export interface AttributionDisplayInput {
  attribution?: { issuer?: string | null } | null
  portrait_subject?: string | null
  issuing_authority?: string | null
}

/** Label for "struck under" when portrait subject is shown (numismatic convention) */
export const STRUCK_UNDER_LABEL = 'Struck under'

/**
 * Returns primary and optional secondary title for coin attribution.
 * Numismatic convention: when obverse shows someone other than the issuer (empress, deified, deity),
 * show portrait subject as primary and issuer as "Struck under {issuer}".
 */
export function getAttributionTitle(coin: AttributionDisplayInput): {
  primary: string
  secondary: string | null
  isPortraitSubject: boolean
} {
  const issuer = coin.attribution?.issuer ?? coin.issuing_authority ?? 'Unknown'
  const portraitSubject = coin.portrait_subject?.trim()
  if (portraitSubject) {
    return {
      primary: portraitSubject,
      secondary: `${STRUCK_UNDER_LABEL} ${issuer}`,
      isPortraitSubject: true,
    }
  }
  return {
    primary: issuer || 'Unknown Ruler',
    secondary: null,
    isPortraitSubject: false,
  }
}
