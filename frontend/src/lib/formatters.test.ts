import { describe, it, expect } from 'vitest'
import { formatYear } from './formatters'

describe('formatYear', () => {
  it('formats positive years as AD', () => {
    expect(formatYear(2023)).toBe('2023')
    // Optional: expect(formatYear(100)).toBe('AD 100') if we want explicit AD
  })

  it('formats negative years as BC', () => {
    expect(formatYear(-27)).toBe('27 BC')
    expect(formatYear(-44)).toBe('44 BC')
  })

  it('formats zero as ??? or specific convention', () => {
    // There is no year 0, but if data has it, handle gracefully
    expect(formatYear(0)).toBe('0') 
  })

  it('handles null/undefined', () => {
    expect(formatYear(null)).toBe('?')
    expect(formatYear(undefined)).toBe('?')
  })
})
