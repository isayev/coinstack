import { http, HttpResponse } from 'msw'
import { Coin } from '@/domain/schemas'

export const handlers = [
  http.get('http://localhost:8000/api/v2/coins', () => {
    return HttpResponse.json([
      {
        id: 1,
        category: 'roman_imperial',
        metal: 'silver',
        dimensions: {
          weight_g: 3.52,
          diameter_mm: 18.5,
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
          url: null
        }
      },
      {
        id: 2,
        category: 'greek',
        metal: 'gold',
        dimensions: {
          weight_g: 8.4,
          diameter_mm: 22.0,
          die_axis: 12
        },
        attribution: {
          issuer: 'Philip II',
          mint: 'Pella',
          year_start: -359,
          year_end: -336
        },
        grading: {
          grading_state: 'slabbed',
          grade: 'MS 65',
          service: 'ngc',
          certification_number: '123456-001',
          strike: '5/5',
          surface: '5/5'
        },
        acquisition: {
          price: 2500,
          currency: 'USD',
          source: 'CNG',
          date: '2022-05-15',
          url: null
        }
      }
    ] as Coin[])
  }),
]
