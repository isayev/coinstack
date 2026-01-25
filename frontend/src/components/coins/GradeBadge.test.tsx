import { render, screen } from '@/test-utils'
import { GradeBadge } from './GradeBadge'
import { describe, it, expect } from 'vitest'

describe('GradeBadge', () => {
  it('renders correctly', () => {
    render(<GradeBadge grade="XF" />)
    expect(screen.getByText('XF')).toBeInTheDocument()
  })

  it('renders service if provided', () => {
    render(<GradeBadge grade="MS 65" service="ngc" />)
    expect(screen.getByText('MS 65')).toBeInTheDocument()
    expect(screen.getByText('NGC')).toBeInTheDocument()
  })
})
