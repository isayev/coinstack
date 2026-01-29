import { render, screen, fireEvent, waitFor } from '@/test-utils'
import { ScraperForm } from './ScraperForm'
import { describe, it, expect, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '@/mocks/server'

describe('ScraperForm', () => {
  it('calls API and returns data on success', async () => {
    const onSuccess = vi.fn()

    // Match backend ImportPreviewResponse: success, source_type, source_id, source_url, coin_data (CoinPreviewData with issuing_authority)
    server.use(
      http.post('http://localhost:8000/api/v2/import/from-url', () => {
        return HttpResponse.json({
          success: true,
          source_type: 'heritage',
          source_id: '12345',
          source_url: 'https://coins.ha.com/itm/12345',
          coin_data: {
            issuing_authority: 'Augustus',
            mint: null,
            year_start: null,
            year_end: null,
            grade: 'VF',
            grade_service: null
          },
          field_confidence: {}
        })
      })
    )

    render(<ScraperForm onScrapeSuccess={onSuccess} />)

    const input = screen.getByPlaceholderText(/Paste Heritage/)
    fireEvent.change(input, { target: { value: 'https://coins.ha.com/itm/12345' } })

    fireEvent.click(screen.getByRole('button', { name: /Scrape/ }))

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith(
        expect.objectContaining({
          success: true,
          source_type: 'heritage',
          coin_data: expect.objectContaining({ issuing_authority: 'Augustus' })
        })
      )
    })
  })
})
