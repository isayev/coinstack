import { render, screen } from '@/test-utils'
import { MetalBadge } from './MetalBadge'
import { describe, it, expect } from 'vitest'

describe('MetalBadge', () => {
  it('renders gold badge correctly', () => {
    render(<MetalBadge metal="gold" />)
    expect(screen.getByText('gold')).toBeInTheDocument()
    expect(screen.getByText('Au')).toBeInTheDocument()
  })

  it('renders silver badge correctly', () => {
    render(<MetalBadge metal="silver" />)
    expect(screen.getByText('silver')).toBeInTheDocument()
    expect(screen.getByText('Ag')).toBeInTheDocument()
  })
})
