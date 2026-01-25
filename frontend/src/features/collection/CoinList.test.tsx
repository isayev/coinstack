import { render, screen, waitFor } from '@/test-utils'
import { CoinList } from './CoinList'
import { describe, it, expect } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '@/mocks/server'

describe('CoinList', () => {
  it('renders coins from API', async () => {
    render(<CoinList />)
    
    // Should show loading skeletons initially
    // Then show data
    await waitFor(() => {
      expect(screen.getByText('Augustus')).toBeInTheDocument()
      expect(screen.getByText('Philip II')).toBeInTheDocument()
    })
  })

  it('renders error state', async () => {
    server.use(
      http.get('http://localhost:8000/api/v2/coins', () => {
        return new HttpResponse(null, { status: 500 })
      })
    )

    render(<CoinList />)
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to load collection/)).toBeInTheDocument()
    })
  })
})
