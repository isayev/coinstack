/**
 * CommandBar - Main application header with quick actions
 * 
 * Features:
 * - Logo with home navigation
 * - Split button for Add Coin (with dropdown for Import, Normalize)
 * - Quick Scrape URL button with popover
 * - Cert Lookup button with popover
 * - Expandable search input
 * - Theme toggle and settings
 * 
 * @module components/layout/CommandBar
 */

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Plus,
  Search,

  ChevronDown,
  PenLine,
  FileSpreadsheet,
  Sparkles,
  ClipboardCheck,
  Link as LinkIcon,
  ScrollText,
  Settings
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { useUIStore } from "@/stores/uiStore";
import { ThemeToggle } from "../ThemeToggle";
import { QuickScrapePopover } from "./QuickScrapePopover";
import { CertLookupPopover } from "./CertLookupPopover";
import { cn } from "@/lib/utils";

export function CommandBar() {
  const navigate = useNavigate();
  const { setCommandPaletteOpen } = useUIStore();
  const [searchExpanded, setSearchExpanded] = useState(false);
  const [searchValue, setSearchValue] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchValue.trim()) {
      // Navigate to collection with search query
      navigate(`/?search=${encodeURIComponent(searchValue.trim())}`);
      setSearchValue("");
      setSearchExpanded(false);
    }
  };

  return (
    <header
      className="sticky top-0 z-50 w-full backdrop-blur"
      style={{
        background: 'var(--bg-elevated)',
        borderBottom: '1px solid var(--border-subtle)'
      }}
    >
      <div className="flex h-20 items-center justify-between px-4 gap-4">
        {/* Logo - Clickable to home */}
        <Link
          to="/"
          className="flex items-center gap-3 hover:opacity-80 transition-opacity flex-shrink-0"
        >
          <img
            src="/logo-sm.png"
            alt="CoinStack"
            className="h-14 w-14 object-contain"
          />
          <span
            className="text-3xl font-bold tracking-tight hidden sm:inline"
            style={{
              background: 'linear-gradient(135deg, var(--metal-au), var(--metal-ag))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}
          >
            CoinStack
          </span>
        </Link>

        {/* Primary Actions Group */}
        <div className="flex items-center gap-2">
          {/* Split Button: Add Coin */}
          <div className="flex">
            <Button
              onClick={() => navigate("/coins/new")}
              className="rounded-r-none gap-1.5"
              style={{
                background: 'var(--metal-au)',
                color: '#000'
              }}
            >
              <Plus className="w-4 h-4" />
              <span className="hidden md:inline">Add Coin</span>
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  className="rounded-l-none border-l border-black/20 px-2"
                  style={{
                    background: 'var(--metal-au)',
                    color: '#000'
                  }}
                >
                  <ChevronDown className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={() => navigate("/coins/new")}>
                  <PenLine className="mr-2 h-4 w-4" />
                  Manual Entry
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate("/import")}>
                  <FileSpreadsheet className="mr-2 h-4 w-4" />
                  Import Excel
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate("/bulk-enrich")}>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Bulk Normalize
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate("/audit")}>
                  <ClipboardCheck className="mr-2 h-4 w-4" />
                  Run Audit
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Quick Scrape URL */}
          <QuickScrapePopover>
            <Button
              variant="outline"
              className="gap-1.5"
              style={{
                borderColor: 'var(--border-subtle)',
                color: 'var(--text-secondary)'
              }}
            >
              <LinkIcon className="w-4 h-4" />
              <span className="hidden lg:inline">Paste URL</span>
            </Button>
          </QuickScrapePopover>

          {/* Cert Lookup */}
          <CertLookupPopover>
            <Button
              variant="outline"
              className="gap-1.5"
              style={{
                borderColor: 'var(--border-subtle)',
                color: 'var(--text-secondary)'
              }}
            >
              <ScrollText className="w-4 h-4" />
              <span className="hidden lg:inline">Cert #</span>
            </Button>
          </CertLookupPopover>
        </div>

        {/* Search - Consolidated with Command Palette hint */}
        <div className="flex-1 max-w-md">
          <form onSubmit={handleSearch} className="relative">
            <Input
              type="text"
              placeholder="Search coins, rulers..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onFocus={() => setSearchExpanded(true)}
              onBlur={() => !searchValue && setSearchExpanded(false)}
              onKeyDown={(e) => {
                // Cmd/Ctrl+K opens command palette
                if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                  e.preventDefault();
                  setCommandPaletteOpen(true);
                }
              }}
              className={cn(
                "pl-10 pr-20 transition-all duration-200",
                searchExpanded ? "w-full" : "w-full"
              )}
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
                color: 'var(--text-primary)'
              }}
            />
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
              style={{ color: 'var(--text-muted)' }}
            />
            {/* Keyboard shortcut hint */}
            <button
              type="button"
              onClick={() => setCommandPaletteOpen(true)}
              className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium transition-colors hover:bg-[var(--bg-hover)]"
              style={{
                color: 'var(--text-muted)',
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)'
              }}
              title="Command Palette"
            >
              <span className="hidden sm:inline">⌘K</span>
              <span className="sm:hidden">⌘</span>
            </button>
          </form>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {/* Theme toggle */}
          <ThemeToggle />

          {/* Settings */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate("/settings")}
            style={{ color: 'var(--text-secondary)' }}
          >
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}
