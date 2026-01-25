import { render, screen, waitFor } from '@/test-utils'
import { AuditPanel } from './AuditPanel'
import { describe, it, expect } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '@/mocks/server'

describe('AuditPanel', () => {
  it('renders "No discrepancies" when audit is clean', async () => {
    server.use(
      http.get('http://localhost:8000/api/v2/audit/1', () => {
        return HttpResponse.json({
          coin_id: 1,
          has_issues: false,
          discrepancies: []
        })
      })
    )

    render(<AuditPanel coinId={1} />)
    
    await waitFor(() => {
      expect(screen.getByText(/No discrepancies found/)).toBeInTheDocument()
    })
  })

  it('renders discrepancy cards when issues found', async () => {
    server.use(
      http.get('http://localhost:8000/api/v2/audit/1', () => {
        return HttpResponse.json({
          coin_id: 1,
          has_issues: true,
          discrepancies: [
            {
              field: 'grade',
              current_value: 'VF',
              auction_value: 'XF',
              confidence: 1.0,
              source: 'Heritage'
            }
          ]
        })
      })
    )

    render(<AuditPanel coinId={1} />)
    
    await waitFor(() => {
      // Use regex for case-insensitivity or match exact case in DOM
      expect(screen.getByText(/grade/i)).toBeInTheDocument()
      expect(screen.getByText('VF')).toBeInTheDocument()
      expect(screen.getByText('XF')).toBeInTheDocument()
    })
  })
})