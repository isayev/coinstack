import { render, screen, fireEvent, waitFor } from '@/test-utils'
import { ScraperForm } from './ScraperForm'
import { describe, it, expect, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '@/mocks/server'

describe('ScraperForm', () => {
  it('calls API and returns data on success', async () => {
    const onSuccess = vi.fn()
    
    server.use(
      http.post('http://localhost:8000/api/v2/scrape/lot', () => {
        return HttpResponse.json({
          source: 'Heritage',
          lot_id: '12345',
          url: 'https://coins.ha.com/itm/12345',
          issuer: 'Augustus',
          hammer_price: 500
        })
      })
    )

    render(<ScraperForm onScrapeSuccess={onSuccess} />)
    
    const input = screen.getByPlaceholderText(/Paste Heritage/)
    fireEvent.change(input, { target: { value: 'https://coins.ha.com/itm/12345' } })
    
    fireEvent.click(screen.getByRole('button', { name: /Scrape/ }))
    
    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith(expect.objectContaining({
        source: 'Heritage',
        issuer: 'Augustus'
      }))
    })
  })
})
