/**
 * CommandPalette - Global command palette (Cmd+K)
 * 
 * Features:
 * - Quick navigation to pages
 * - Coin search with results
 * - Quick actions with keyboard shortcuts
 * - Keyboard navigation hints
 * 
 * @module components/layout/CommandPalette
 */

import { useState, useMemo } from "react";
import { useUIStore } from "@/stores/uiStore";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import {
  Command,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandItem,
  CommandGroup,
  CommandSeparator
} from "@/components/ui/command";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { client } from "@/api/client";
import { Coin } from "@/domain/schemas";
import {
  Coins,
  BarChart3,
  Upload,
  Settings,
  Plus,
  Link as LinkIcon,
  Search,
  ScrollText,
  Sparkles,
  ClipboardCheck
} from "lucide-react";

// Navigation commands
const navigationCommands = [
  { id: "collection", label: "Go to Collection", icon: Coins, path: "/", shortcut: "G C" },
  { id: "stats", label: "Go to Statistics", icon: BarChart3, path: "/stats", shortcut: "G S" },
  { id: "settings", label: "Go to Settings", icon: Settings, path: "/settings", shortcut: "G E" },
];

// Quick action commands
const actionCommands = [
  { id: "add-coin", label: "Add Coin", description: "Manual entry", icon: Plus, path: "/coins/new", shortcut: "N" },
  { id: "paste-url", label: "Paste Auction URL", description: "Quick scrape", icon: LinkIcon, action: "quickScrape", shortcut: "U" },
  { id: "import", label: "Import Excel", description: "Batch import", icon: Upload, path: "/import" },
  { id: "cert-lookup", label: "Cert Lookup", description: "NGC/PCGS", icon: ScrollText, action: "certLookup" },
  { id: "bulk-enrich", label: "Bulk Normalize", description: "AI enrichment", icon: Sparkles, path: "/bulk-enrich" },
  { id: "audit", label: "Run Audit", description: "Check collection", icon: ClipboardCheck, path: "/audit" },
];

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen, setQuickScrapeOpen } = useUIStore();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");

  // Search coins when query is long enough
  const { data: coinResults } = useQuery({
    queryKey: ['coins', 'search', search],
    queryFn: () => client.getCoins({ search, limit: 5 }),
    enabled: search.length >= 2 && commandPaletteOpen,
    staleTime: 30000, // 30 seconds
  });

  // Filter commands based on search
  const filteredNavigation = useMemo(() => {
    if (!search) return navigationCommands;
    const lower = search.toLowerCase();
    return navigationCommands.filter(cmd =>
      cmd.label.toLowerCase().includes(lower)
    );
  }, [search]);

  const filteredActions = useMemo(() => {
    if (!search) return actionCommands;
    const lower = search.toLowerCase();
    return actionCommands.filter(cmd =>
      cmd.label.toLowerCase().includes(lower) ||
      cmd.description?.toLowerCase().includes(lower)
    );
  }, [search]);

  // Unified selection handler - receives value string from cmdk
  const handleValueSelect = (value: string) => {
    // Close and reset
    setCommandPaletteOpen(false);
    setSearch("");

    // Handle coin selection
    if (value.startsWith('coin-')) {
      const coinId = parseInt(value.replace('coin-', ''), 10);
      if (!isNaN(coinId)) {
        navigate(`/coins/${coinId}`);
      }
      return;
    }

    // Handle action commands
    const actionCmd = actionCommands.find(cmd => cmd.id === value);
    if (actionCmd) {
      if (actionCmd.action === 'quickScrape') {
        setQuickScrapeOpen(true);
      } else if (actionCmd.path) {
        navigate(actionCmd.path);
      }
      return;
    }

    // Handle navigation commands
    const navCmd = navigationCommands.find(cmd => cmd.id === value);
    if (navCmd?.path) {
      navigate(navCmd.path);
    }
  };

  return (
    <Dialog open={commandPaletteOpen} onOpenChange={(open) => {
      setCommandPaletteOpen(open);
      if (!open) setSearch("");
    }}>
      <DialogContent
        className="p-0 max-w-lg overflow-hidden"
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)'
        }}
      >
        <Command className="rounded-lg" shouldFilter={false}>
          <div className="flex items-center border-b px-3" style={{ borderColor: 'var(--border-subtle)' }}>
            <Search className="mr-2 h-4 w-4 shrink-0" style={{ color: 'var(--text-muted)' }} />
            <CommandInput
              placeholder="Search coins, commands..."
              value={search}
              onValueChange={setSearch}
              className="flex h-11 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
              style={{ color: 'var(--text-primary)' }}
            />
          </div>

          <CommandList className="max-h-[400px] overflow-y-auto">
            <CommandEmpty className="py-6 text-center text-sm" style={{ color: 'var(--text-muted)' }}>
              No results found.
            </CommandEmpty>

            {/* Coin search results */}
            {coinResults?.items && coinResults.items.length > 0 && (
              <CommandGroup heading="Coins">
                {coinResults.items.filter((coin: Coin) => coin.id !== null).map((coin: Coin) => (
                  <CommandItem
                    key={coin.id!}
                    value={`coin-${coin.id}`}
                    onSelect={handleValueSelect}
                    onClick={() => handleValueSelect(`coin-${coin.id}`)}
                    className="flex items-center gap-3 px-3 py-2 cursor-pointer"
                  >
                    {/* Coin thumbnail */}
                    <div
                      className="w-8 h-8 rounded flex-shrink-0 flex items-center justify-center"
                      style={{ background: 'var(--bg-elevated)' }}
                    >
                      {coin.images?.[0]?.url ? (
                        <img
                          src={coin.images[0].url}
                          alt=""
                          className="w-full h-full object-cover rounded"
                        />
                      ) : (
                        <Coins className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
                      )}
                    </div>

                    {/* Coin info */}
                    <div className="flex-1 min-w-0">
                      <div
                        className="font-medium truncate text-sm"
                        style={{ color: 'var(--text-primary)' }}
                      >
                        {coin.attribution?.issuer || 'Unknown Ruler'}
                      </div>
                      <div
                        className="text-xs truncate"
                        style={{ color: 'var(--text-muted)' }}
                      >
                        {coin.denomination} · {coin.metal}
                      </div>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}

            {/* Quick Actions */}
            {filteredActions.length > 0 && (
              <>
                {coinResults?.items && coinResults.items.length > 0 && <CommandSeparator />}
                <CommandGroup heading="Quick Actions">
                  {filteredActions.map((cmd) => {
                    const Icon = cmd.icon;
                    return (
                      <CommandItem
                        key={cmd.id}
                        value={cmd.id}
                        onSelect={handleValueSelect}
                        onClick={() => handleValueSelect(cmd.id)}
                        className="flex items-center justify-between px-3 py-2 cursor-pointer"
                      >
                        <div className="flex items-center gap-3">
                          <Icon className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
                          <div>
                            <span style={{ color: 'var(--text-primary)' }}>{cmd.label}</span>
                            {cmd.description && (
                              <span
                                className="ml-2 text-xs"
                                style={{ color: 'var(--text-muted)' }}
                              >
                                {cmd.description}
                              </span>
                            )}
                          </div>
                        </div>
                        {cmd.shortcut && (
                          <kbd
                            className="px-1.5 py-0.5 text-[10px] font-mono rounded"
                            style={{
                              background: 'var(--bg-subtle)',
                              color: 'var(--text-muted)',
                              border: '1px solid var(--border-subtle)'
                            }}
                          >
                            {cmd.shortcut}
                          </kbd>
                        )}
                      </CommandItem>
                    );
                  })}
                </CommandGroup>
              </>
            )}

            {/* Navigation */}
            {filteredNavigation.length > 0 && (
              <>
                <CommandSeparator />
                <CommandGroup heading="Navigation">
                  {filteredNavigation.map((cmd) => {
                    const Icon = cmd.icon;
                    return (
                      <CommandItem
                        key={cmd.id}
                        value={cmd.id}
                        onSelect={handleValueSelect}
                        onClick={() => handleValueSelect(cmd.id)}
                        className="flex items-center justify-between px-3 py-2 cursor-pointer"
                      >
                        <div className="flex items-center gap-3">
                          <Icon className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
                          <span style={{ color: 'var(--text-primary)' }}>{cmd.label}</span>
                        </div>
                        {cmd.shortcut && (
                          <kbd
                            className="px-1.5 py-0.5 text-[10px] font-mono rounded"
                            style={{
                              background: 'var(--bg-subtle)',
                              color: 'var(--text-muted)',
                              border: '1px solid var(--border-subtle)'
                            }}
                          >
                            {cmd.shortcut}
                          </kbd>
                        )}
                      </CommandItem>
                    );
                  })}
                </CommandGroup>
              </>
            )}
          </CommandList>

          {/* Footer with keyboard hints */}
          <div
            className="flex items-center justify-between px-3 py-2 text-[10px] border-t"
            style={{
              borderColor: 'var(--border-subtle)',
              color: 'var(--text-muted)',
              background: 'var(--bg-subtle)'
            }}
          >
            <div className="flex items-center gap-3">
              <span><kbd className="font-mono">↑↓</kbd> Navigate</span>
              <span><kbd className="font-mono">↵</kbd> Select</span>
              <span><kbd className="font-mono">Esc</kbd> Close</span>
            </div>
            <span><kbd className="font-mono">?</kbd> All shortcuts</span>
          </div>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
