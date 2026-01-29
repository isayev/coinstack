/**
 * Grade tier definitions for filtering and display.
 * Tiers: poor < good < fine < ef < au < ms
 */
export type GradeTier = 'poor' | 'good' | 'fine' | 'ef' | 'au' | 'ms' | 'unknown';

/**
 * Maps a raw grade string to a display tier.
 * Used for filtering, stats aggregation, and color selection.
 * Order matters: check more specific / higher grades first.
 */
export function getGradeTier(grade: string | null | undefined): GradeTier {
  if (!grade) return 'unknown';

  const g = grade.toLowerCase();

  // Mint State (highest)
  if (
    g.includes('ms') ||
    g.includes('mint state') ||
    g.includes('fdc') ||
    g.includes('unc') ||
    g.includes('bu') ||
    g.includes('brilliant')
  ) {
    return 'ms';
  }

  // About Uncirculated
  if (g.includes('au') || g.includes('about unc') || g.includes('almost unc')) {
    return 'au';
  }

  // Extremely Fine (check before VF/F so "Superb EF" → ef)
  if (
    g.includes('ef') ||
    g.includes('xf') ||
    g.includes('extremely') ||
    g.includes('superb')
  ) {
    return 'ef';
  }

  // Very Fine (check before Fine so "Good VF" → fine, "Nearly VF" → fine)
  if (g.includes('vf') || g.includes('very fine') || g.includes('choice')) {
    return 'fine';
  }

  // Very Good (check before Good so "VG" doesn't match "good" only)
  if (g.includes('vg') || g.includes('very good')) {
    return 'good';
  }

  // Fine (F, F12, or word "fine"; "very fine" already handled above)
  if (/\bf\d*\b/.test(g) || g.includes('fine')) {
    return 'fine';
  }

  // Good
  if (/\bg\d*\b/.test(g) || g.startsWith('good')) {
    return 'good';
  }

  // Poor
  if (
    g.includes('poor') ||
    g.includes('fair') ||
    g.includes('ag') ||
    g.includes('basal') ||
    g.includes('fr')
  ) {
    return 'poor';
  }

  return 'unknown';
}

/**
 * Returns CSS variable for grade color based on tier.
 */
export function getGradeColor(grade: string | null | undefined): string {
  const tier = getGradeTier(grade);
  return `var(--grade-${tier})`;
}

/**
 * Returns display label for a tier.
 */
export function getTierLabel(tier: GradeTier): string {
  const labels: Record<GradeTier, string> = {
    poor: 'Poor',
    good: 'Good',
    fine: 'Fine',
    ef: 'EF',
    au: 'AU',
    ms: 'Mint State',
    unknown: 'Unknown',
  };
  return labels[tier];
}
