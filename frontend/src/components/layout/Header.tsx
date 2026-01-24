import { Plus, Search, Coins } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate, Link } from "react-router-dom";
import { useUIStore } from "@/stores/uiStore";
import { ThemeToggle } from "./ThemeToggle";

export function Header() {
  const navigate = useNavigate();
  const { setCommandPaletteOpen } = useUIStore();
  
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center justify-between px-4">
        {/* Logo - Clickable to home */}
        <Link 
          to="/" 
          className="flex items-center gap-2.5 hover:opacity-80 transition-opacity"
        >
          {/* Logo icon */}
          <div className="relative w-8 h-8 rounded-lg bg-gradient-to-br from-primary/90 to-primary flex items-center justify-center shadow-sm">
            <Coins className="w-4.5 h-4.5 text-primary-foreground" />
            {/* Subtle shine effect */}
            <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-white/20 to-transparent" />
          </div>
          {/* Logo text */}
          <div className="flex flex-col leading-none">
            <span className="logo-text text-xl text-foreground">
              CoinStack
            </span>
            <span className="text-[10px] text-muted-foreground font-medium tracking-wider uppercase">
              Collection Manager
            </span>
          </div>
        </Link>
        
        {/* Right side controls */}
        <div className="flex items-center gap-2">
          {/* Search button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCommandPaletteOpen(true)}
            className="text-muted-foreground hover:text-foreground"
          >
            <Search className="w-4 h-4" />
          </Button>
          
          {/* Add Coin button */}
          <Button 
            onClick={() => navigate("/coins/new")}
            className="gap-2 shadow-sm"
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
