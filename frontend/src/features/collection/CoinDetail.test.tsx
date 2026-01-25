import { render, screen } from '@/test-utils'
import { CoinDetail } from './CoinDetail'
import { describe, it, expect } from 'vitest'
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

describe('CoinDetail', () => {
  it('renders attribution correctly', () => {
    render(<CoinDetail coin={mockCoin} />)
    expect(screen.getByRole('heading', { name: 'Augustus' })).toBeInTheDocument()
    expect(screen.getByText(/Lugdunum/)).toBeInTheDocument()
  })

  it('renders physics data', () => {
    render(<CoinDetail coin={mockCoin} />)
    expect(screen.getByText('3.52 g')).toBeInTheDocument()
    expect(screen.getByText('18.5 mm')).toBeInTheDocument()
  })

  it('renders grading', () => {
    render(<CoinDetail coin={mockCoin} />)
    expect(screen.getByText('VF')).toBeInTheDocument()
  })
})
