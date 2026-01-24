import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import { AppShell } from "@/components/layout/AppShell";
import { Routes, Route } from "react-router-dom";

import { CollectionPage } from "@/pages/CollectionPage";
import { CoinDetailPage } from "@/pages/CoinDetailPage";
import { AddCoinPage } from "@/pages/AddCoinPage";
import { EditCoinPage } from "@/pages/EditCoinPage";
import { ImportPage } from "@/pages/ImportPage";
import { StatsPage } from "@/pages/StatsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { BulkEnrichPage } from "@/pages/BulkEnrichPage";

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
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="coinstack-theme">
        <BrowserRouter>
          <AppShell>
            <Routes>
              <Route path="/" element={<CollectionPage />} />
              <Route path="/coins/new" element={<AddCoinPage />} />
              <Route path="/coins/:id" element={<CoinDetailPage />} />
              <Route path="/coins/:id/edit" element={<EditCoinPage />} />
              <Route path="/import" element={<ImportPage />} />
              <Route path="/stats" element={<StatsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/bulk-enrich" element={<BulkEnrichPage />} />
            </Routes>
          </AppShell>
        </BrowserRouter>
        <Toaster />
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
