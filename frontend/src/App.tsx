import { BrowserRouter, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import { AppShell } from "@/components/layout/AppShell";
import { Routes, Route } from "react-router-dom";
import React from "react";

import { CoinGridPage } from "@/pages/CoinGridPage";
import { CoinTablePage } from "@/pages/CoinTablePage";
import { CoinDetailPage } from "@/pages/CoinDetailPage";
import { AddCoinPage } from "@/pages/AddCoinPage";
import { EditCoinPage } from "@/pages/EditCoinPage";
import { ImportPage } from "@/pages/ImportPage";
import { StatsPageV3 } from "@/pages/StatsPageV3";
import { SettingsPage } from "@/pages/SettingsPage";
import { BulkEnrichPage } from "@/pages/BulkEnrichPage";
import { AuctionsPage } from "@/pages/AuctionsPage";
import { SeriesDashboard } from "@/pages/SeriesDashboard";
import { CreateSeriesPage } from "@/pages/CreateSeriesPage";
import { SeriesDetailPage } from "@/pages/SeriesDetailPage";
import { ReviewCenterPage } from "@/pages/ReviewCenterPage";

// Error Boundary to catch rendering errors
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '40px',
          background: '#1a1a2e',
          color: '#fff',
          minHeight: '100vh',
          fontFamily: 'monospace'
        }}>
          <h1 style={{ color: '#ff6b6b', marginBottom: '20px' }}>Something went wrong</h1>
          <pre style={{
            background: '#0f0f1a',
            padding: '20px',
            borderRadius: '8px',
            overflow: 'auto',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word'
          }}>
            {this.state.error?.toString()}
            {'\n\n'}
            {this.state.error?.stack}
          </pre>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              background: '#7c3aed',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider defaultTheme="dark" storageKey="coinstack-theme">
          <BrowserRouter>
            <AppShell>
              <Routes>
                <Route path="/" element={<Navigate to="/collection/grid" replace />} />
                <Route path="/collection" element={<Navigate to="/collection/grid" replace />} />
                <Route path="/collection/grid" element={<CoinGridPage />} />
                <Route path="/collection/table" element={<CoinTablePage />} />

                <Route path="/coins/new" element={<AddCoinPage />} />
                <Route path="/coins/:id" element={<CoinDetailPage />} />
                <Route path="/coins/:id/edit" element={<EditCoinPage />} />
                <Route path="/import" element={<ImportPage />} />
                <Route path="/stats" element={<StatsPageV3 />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/bulk-enrich" element={<BulkEnrichPage />} />
                <Route path="/auctions" element={<AuctionsPage />} />
                <Route path="/audit" element={<Navigate to="/review" replace />} />
                <Route path="/series" element={<SeriesDashboard />} />
                <Route path="/series/new" element={<CreateSeriesPage />} />
                <Route path="/series/:id" element={<SeriesDetailPage />} />
                <Route path="/review" element={<ReviewCenterPage />} />
              </Routes>
            </AppShell>
          </BrowserRouter>
          <Toaster />
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
