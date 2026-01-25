import { render, screen, fireEvent } from '@/test-utils'
import { CoinCard } from './CoinCard'
import { describe, it, expect, vi } from 'vitest'
import { Coin } from '@/domain/schemas'

const mockCoin: Coin = {
  id: 1,
  category: 'roman_imperial',
  metal: 'silver',
  dimensions: {
    weight_g: 3.52,
    diameter_mm: 18.5,
    thickness_mm: 2,
    die_axis: 6
  },
  attribution: {
    issuer: 'Augustus',
    mint: 'Lugdunum',
    year_start: 2,
    year_end: 4
  },
  grading: {
    grading_state: 'raw',
    grade: 'VF',
    service: null,
    certification_number: null,
    strike: null,
    surface: null
  },
  acquisition: {
    price: 250,
    currency: 'USD',
    source: 'Heritage',
    date: '2023-01-01',
    url: ''
  },
  images: []
}

describe('CoinCard', () => {
  it('renders attribution correctly', () => {
    render(<CoinCard coin={mockCoin} />)
    expect(screen.getByText('Augustus')).toBeInTheDocument()
    expect(screen.getByText(/Lugdunum/)).toBeInTheDocument()
  })

  it('renders physics data', () => {
    render(<CoinCard coin={mockCoin} />)
    expect(screen.getByText('3.52g')).toBeInTheDocument()
    expect(screen.getByText('18.5mm')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn()
    render(<CoinCard coin={mockCoin} onClick={handleClick} />)

    fireEvent.click(screen.getByText('Augustus'))
    expect(handleClick).toHaveBeenCalledWith(mockCoin)
  })

  it('formats price correctly', () => {
    render(<CoinCard coin={mockCoin} />)
    // Non-breaking space might be used in currency formatting, use regex
    expect(screen.getByText(/\$250\.00/)).toBeInTheDocument()
  })
})
