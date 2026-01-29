import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useDatabaseInfo, downloadBackup, downloadCSV } from "@/hooks/useSettings";
import { useLLMStatusQuery, useLLMCostReport } from "@/hooks/useLLM";
import { useFilterStore } from "@/stores/filterStore";
import { useTheme } from "@/components/theme-provider";
import { 
  Database, Download, FileSpreadsheet, Trash2, 
  Sun, Moon, Monitor, HardDrive, Info, RefreshCw, Library, Sparkles, ExternalLink
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useState } from "react";
import { cn } from "@/lib/utils";

// -----------------------------------------------------------------------------
// LLM & AI Settings Card
// -----------------------------------------------------------------------------
const ANTHROPIC_BILLING_URL = "https://console.anthropic.com/settings/billing";
const OPENROUTER_PRICING_URL = "https://openrouter.ai/pricing";

function LLMAISettingsCard() {
  const { data: status, isLoading: statusLoading, error: statusError } = useLLMStatusQuery();
  const { data: costReport, isLoading: costLoading } = useLLMCostReport(30);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5" />
          LLM & AI
        </CardTitle>
        <CardDescription>
          Status, provider keys, usage, and billing for AI enrichment (historical context, legend expansion, etc.)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {statusLoading && (
          <p className="text-sm text-muted-foreground">Loading LLM status...</p>
        )}
        {statusError && (
          <p className="text-sm text-destructive">
            Could not load LLM status. Is the backend running?
          </p>
        )}
        {status && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Profile</div>
                <div className="font-medium capitalize">{status.profile}</div>
              </div>
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Monthly cost</div>
                <div className="font-medium">${status.monthly_cost_usd.toFixed(2)}</div>
              </div>
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Budget</div>
                <div className="font-medium">${status.monthly_budget_usd.toFixed(2)}</div>
              </div>
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Remaining</div>
                <div className="font-medium">${status.budget_remaining_usd.toFixed(2)}</div>
              </div>
            </div>
            {status.provider_keys && (
              <div>
                <div className="text-sm font-medium mb-2">Provider API keys</div>
                <ul className="text-sm space-y-1 text-muted-foreground">
                  <li>
                    Anthropic: {status.provider_keys.anthropic ? (
                      <span className="text-green-600 dark:text-green-400">Configured</span>
                    ) : (
                      <span className="text-amber-600 dark:text-amber-400">Not set</span>
                    )}
                  </li>
                  <li>
                    OpenRouter: {status.provider_keys.openrouter ? (
                      <span className="text-green-600 dark:text-green-400">Configured</span>
                    ) : (
                      <span className="text-amber-600 dark:text-amber-400">Not set</span>
                    )}
                  </li>
                  <li>
                    Google: {status.provider_keys.google ? (
                      <span className="text-green-600 dark:text-green-400">Configured</span>
                    ) : (
                      <span className="text-amber-600 dark:text-amber-400">Not set</span>
                    )}
                  </li>
                </ul>
                <p className="text-xs text-muted-foreground mt-1">
                  Set in backend <code className="bg-muted px-1 rounded">.env</code> (ANTHROPIC_API_KEY, OPENROUTER_API_KEY, GOOGLE_API_KEY). Restart backend after changes.
                </p>
              </div>
            )}
            {!costLoading && costReport && costReport.total_cost_usd > 0 && (
              <div>
                <div className="text-sm font-medium mb-2">Usage (last 30 days)</div>
                <p className="text-sm text-muted-foreground">
                  Total: ${costReport.total_cost_usd.toFixed(2)} — see cost report below for breakdown by capability and model.
                </p>
              </div>
            )}
            <div>
              <div className="text-sm font-medium mb-2">Billing & credits</div>
              <ul className="text-sm space-y-2">
                <li>
                  <a
                    href={ANTHROPIC_BILLING_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary underline inline-flex items-center gap-1"
                  >
                    Anthropic Plans & Billing <ExternalLink className="w-3 h-3" />
                  </a>
                  — Top up credits or enable auto-reload.
                </li>
                <li>
                  <a
                    href={OPENROUTER_PRICING_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary underline inline-flex items-center gap-1"
                  >
                    OpenRouter Pricing <ExternalLink className="w-3 h-3" />
                  </a>
                  — Check credits and usage (e.g. for DeepSeek).
                </li>
              </ul>
            </div>
            <div className="rounded-lg border bg-muted/50 p-3 text-sm text-muted-foreground">
              <strong className="text-foreground">Troubleshooting:</strong> If you see &quot;credit balance too low&quot; or &quot;All providers failed&quot;, top up Anthropic credits or set <code className="bg-muted px-1 rounded">LLM_PROFILE=development</code> in backend <code className="bg-muted px-1 rounded">.env</code> to use OpenRouter (e.g. DeepSeek) as primary, then restart the backend.
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export function SettingsPage() {
  const { data: dbInfo, isLoading } = useDatabaseInfo();
  const { theme, setTheme } = useTheme();
  const resetFilters = useFilterStore((s) => s.reset);
  const [isSyncing, setIsSyncing] = useState<string | null>(null);

  const handleBackup = () => {
    downloadBackup();
    toast.success("Database backup started");
  };

  const handleExportCSV = () => {
    downloadCSV();
    toast.success("CSV export started");
  };

  const handleClearCache = () => {
    // Clear localStorage except theme preference
    const themeValue = localStorage.getItem("coinstack-theme");
    localStorage.clear();
    if (themeValue) {
      localStorage.setItem("coinstack-theme", themeValue);
    }
    resetFilters();
    toast.success("Cache cleared successfully");
  };

  const handleSyncVocab = async (type: 'issuers' | 'mints') => {
    setIsSyncing(type);
    try {
      await api.post(`/api/vocab/sync/nomisma/${type}`);
      toast.success(`Nomisma ${type} sync started in background`);
    } catch (error: any) {
      toast.error(`Failed to start sync: ${error.message}`);
    } finally {
      setIsSyncing(null);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Manage your collection and preferences</p>
      </div>

      {/* Vocabulary Sync */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Library className="w-5 h-5" />
            Vocabulary Management
          </CardTitle>
          <CardDescription>Synchronize authoritative data from Nomisma.org</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <Button 
              onClick={() => handleSyncVocab('issuers')} 
              disabled={!!isSyncing}
              variant="outline"
              className="flex-1"
            >
              <RefreshCw className={cn("w-4 h-4 mr-2", isSyncing === 'issuers' && "animate-spin")} />
              Sync Issuers
            </Button>
            <Button 
              onClick={() => handleSyncVocab('mints')} 
              disabled={!!isSyncing}
              variant="outline"
              className="flex-1"
            >
              <RefreshCw className={cn("w-4 h-4 mr-2", isSyncing === 'mints' && "animate-spin")} />
              Sync Mints
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            This updates the local database with the latest rulers and mints from the Nomisma Linked Open Data cloud.
            The process runs in the background on the server.
          </p>
        </CardContent>
      </Card>

      {/* LLM & AI */}
      <LLMAISettingsCard />

      {/* Database Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            Database
          </CardTitle>
          <CardDescription>Information about your collection database</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <div className="text-muted-foreground">Loading...</div>
          ) : dbInfo ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Coins</div>
                <div className="text-2xl font-bold">{dbInfo.coin_count}</div>
              </div>
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-sm text-muted-foreground">Size</div>
                <div className="text-2xl font-bold">{dbInfo.size_mb} MB</div>
              </div>
              <div className="p-3 bg-muted rounded-lg col-span-2">
                <div className="text-sm text-muted-foreground">Last Modified</div>
                <div className="text-lg font-semibold">{dbInfo.last_modified}</div>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {/* Backup & Export */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="w-5 h-5" />
            Backup & Export
          </CardTitle>
          <CardDescription>Download your data for safekeeping</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <Button onClick={handleBackup} className="flex-1">
              <Download className="w-4 h-4 mr-2" />
              Download Database Backup
            </Button>
            <Button onClick={handleExportCSV} variant="outline" className="flex-1">
              <FileSpreadsheet className="w-4 h-4 mr-2" />
              Export to CSV
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            The database backup (.db file) can be restored by replacing the existing database file.
            CSV export includes all coin data in spreadsheet format.
          </p>
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sun className="w-5 h-5" />
            Appearance
          </CardTitle>
          <CardDescription>Customize how CoinStack looks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Button 
              variant={theme === "light" ? "default" : "outline"} 
              onClick={() => setTheme("light")}
              className="flex-1"
            >
              <Sun className="w-4 h-4 mr-2" />
              Light
            </Button>
            <Button 
              variant={theme === "dark" ? "default" : "outline"} 
              onClick={() => setTheme("dark")}
              className="flex-1"
            >
              <Moon className="w-4 h-4 mr-2" />
              Dark
            </Button>
            <Button 
              variant={theme === "system" ? "default" : "outline"} 
              onClick={() => setTheme("system")}
              className="flex-1"
            >
              <Monitor className="w-4 h-4 mr-2" />
              System
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Data Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trash2 className="w-5 h-5" />
            Data Management
          </CardTitle>
          <CardDescription>Clear cached data and reset preferences</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button variant="outline" onClick={handleClearCache}>
            <Trash2 className="w-4 h-4 mr-2" />
            Clear Cache & Reset Filters
          </Button>
          <p className="text-sm text-muted-foreground">
            This clears locally stored filter preferences and cached data. 
            Your coin collection data will not be affected.
          </p>
        </CardContent>
      </Card>

      {/* About */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="w-5 h-5" />
            About
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Version</span>
            <span className="font-medium">0.1.0</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Stack</span>
            <span className="font-medium">React + FastAPI + SQLite</span>
          </div>
          <p className="text-sm text-muted-foreground pt-2">
            CoinStack is a personal ancient coin collection management system.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
