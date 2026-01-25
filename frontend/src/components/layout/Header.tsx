import { Plus, Search, Coins } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate, Link } from "react-router-dom";
import { useUIStore } from "@/stores/uiStore";
import { ThemeToggle } from "./ThemeToggle";

export function Header() {
  const navigate = useNavigate();
  const { setCommandPaletteOpen } = useUIStore();
  
  return (
    <header
      className="sticky top-0 z-50 w-full backdrop-blur"
      style={{
        background: 'var(--bg-elevated)',
        borderBottom: '1px solid var(--border-subtle)'
      }}
    >
      <div className="flex h-14 items-center justify-between px-4">
        {/* Logo - Clickable to home */}
        <Link 
          to="/" 
          className="flex items-center gap-2.5 hover:opacity-80 transition-opacity"
        >
          {/* Logo icon with gold/silver gradient */}
          <div 
            className="relative w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ 
              background: 'linear-gradient(135deg, var(--metal-au), var(--metal-ag))'
            }}
          >
            <Coins className="w-4 h-4 text-black" />
          </div>
          {/* Logo text */}
          <span 
            className="text-xl font-bold"
            style={{ 
              background: 'linear-gradient(135deg, var(--metal-au), var(--metal-ag))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}
          >
            CoinStack
          </span>
        </Link>
        
        {/* Right side controls */}
        <div className="flex items-center gap-2">
          {/* Search button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCommandPaletteOpen(true)}
            className="hover:bg-[var(--bg-elevated)]"
            style={{ color: 'var(--text-secondary)' }}
          >
            <Search className="w-4 h-4" />
          </Button>
          
          {/* Add Coin button */}
          <Button
            onClick={() => navigate("/coins/new")}
            className="gap-2"
            style={{
              background: 'var(--metal-au)',
              color: '#000'
            }}
          >
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">Add Coin</span>
          </Button>
          
          {/* Theme toggle */}
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
