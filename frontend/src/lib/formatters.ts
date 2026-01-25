export function formatYear(year: number | null | undefined): string {
  if (year === null || year === undefined) return '?'
  if (year === 0) return '0'
  
  if (year < 0) {
    return `${Math.abs(year)} BC`
  }
  
  return year.toString()
}
