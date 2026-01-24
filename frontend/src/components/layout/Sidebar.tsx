import { NavLink } from "react-router-dom";
import { useUIStore } from "@/stores/uiStore";
import { cn } from "@/lib/utils";
import { 
  Coins, BarChart3, Upload, Settings, 
  ChevronLeft, ChevronRight, Sparkles 
} from "lucide-react";
import { Button } from "@/components/ui/button";

const navItems = [
  { to: "/", icon: Coins, label: "Collection" },
  { to: "/stats", icon: BarChart3, label: "Statistics" },
  { to: "/import", icon: Upload, label: "Import" },
  { to: "/bulk-enrich", icon: Sparkles, label: "Bulk Enrich" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  
  return (
    <aside className={cn(
      "fixed left-0 top-14 bottom-0 z-40 border-r bg-card transition-all duration-200",
      sidebarOpen ? "w-64" : "w-16"
    )}>
      <nav className="flex flex-col gap-1 p-2">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => cn(
              "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
              isActive 
                ? "bg-accent text-accent-foreground" 
                : "hover:bg-muted"
            )}
          >
            <Icon className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>
      
      <Button
        variant="ghost"
        size="icon"
        className="absolute bottom-4 right-2"
        onClick={toggleSidebar}
      >
        {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </Button>
    </aside>
  );
}
