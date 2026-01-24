import { Plus, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { useUIStore } from "@/stores/uiStore";
import { ThemeToggle } from "./ThemeToggle";

export function Header() {
  const navigate = useNavigate();
  const { setCommandPaletteOpen } = useUIStore();
  
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold">CoinStack</h1>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCommandPaletteOpen(true)}
          >
            <Search className="w-4 h-4" />
          </Button>
          <Button onClick={() => navigate("/coins/new")}>
            <Plus className="w-4 h-4 mr-2" />
            Add Coin
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
