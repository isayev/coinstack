# CoinStack Frontend

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The app will be available at http://localhost:3000

## Features

- React 18 with TypeScript
- Vite for fast development
- Tailwind CSS for styling
- shadcn/ui components
- TanStack Query for data fetching
- Zustand for state management
- React Router for navigation
- Dark/Light theme support

## Project Structure

```
src/
├── components/
│   ├── ui/          # shadcn/ui components
│   ├── coins/       # Coin-specific components
│   └── layout/      # App shell components
├── hooks/           # React Query hooks
├── pages/           # Page components
├── stores/          # Zustand stores
├── types/           # TypeScript types
└── lib/             # Utilities and API client
```
