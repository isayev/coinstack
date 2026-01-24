# CoinStack

A personal ancient coin collection management system for numismatists.

## Features

- **Collection Management**: Catalog coins with detailed metadata (denomination, metal, ruler, dates, legends, physical attributes)
- **Grid & Table Views**: Browse collection in visual grid or sortable table
- **Advanced Filtering**: Filter by category, metal, ruler, mint, storage location
- **Statistics Dashboard**: Visualize collection value, distribution by category/metal, top rulers
- **Import/Export**: Import from Excel/CSV, export to CSV, database backup
- **Coin Detail Pages**: Full coin information with design descriptions, references, provenance
- **Add/Edit Forms**: Comprehensive forms with organized tabs for all coin attributes
- **Dark/Light Theme**: System-aware theming

## Tech Stack

### Backend
- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 (ORM)
- Pydantic 2.x (validation)
- SQLite (database)

### Frontend
- React 18
- TypeScript 5.x
- Vite (build tool)
- TanStack Query (data fetching)
- Zustand (state management)
- Tailwind CSS + shadcn/ui (styling)
- Recharts (charts)
- React Hook Form + Zod (forms)

## Project Structure

```
coinstack/
├── backend/
│   ├── app/
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── routers/      # API endpoints
│   │   ├── services/     # Business logic
│   │   └── crud/         # Database operations
│   ├── data/             # SQLite database
│   └── uploads/          # Uploaded images
├── frontend/
│   └── src/
│       ├── components/   # React components
│       ├── pages/        # Page components
│       ├── hooks/        # Custom hooks
│       ├── stores/       # Zustand stores
│       └── types/        # TypeScript types
└── .cursor/rules/        # AI assistant rules
```

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings alembic python-multipart openpyxl anthropic python-dateutil
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/coins` | GET | List coins with pagination/filters |
| `/api/coins` | POST | Create new coin |
| `/api/coins/{id}` | GET | Get coin detail |
| `/api/coins/{id}` | PUT | Update coin |
| `/api/coins/{id}` | DELETE | Delete coin |
| `/api/stats` | GET | Collection statistics |
| `/api/import/collection` | POST | Import from Excel/CSV |
| `/api/settings/backup` | GET | Download database backup |
| `/api/settings/export-csv` | GET | Export to CSV |

## Roadmap

### Completed (v0.1.0)
- [x] Core data model (Coin, Mint, Reference, Image, Provenance)
- [x] Collection grid/table views with filtering
- [x] Coin detail pages with tabs
- [x] Add/Edit coin forms
- [x] Statistics dashboard with charts
- [x] Excel/CSV import wizard
- [x] Settings page (backup, export, theme)
- [x] Dark/light theme support

### Planned (v0.2.0)
- [ ] Image upload and management
- [ ] Reference catalog integration (RIC lookup)
- [ ] Advanced search with natural language
- [ ] Bulk edit operations
- [ ] Print collection reports

### Future
- [ ] LLM-powered auction listing parser
- [ ] Legend expansion using Claude API
- [ ] Die study tracking
- [ ] Value estimation trends
- [ ] Mobile-responsive improvements

## License

Private project - All rights reserved.

## Author

isayev (olexandr@olexandrisayev.com)
