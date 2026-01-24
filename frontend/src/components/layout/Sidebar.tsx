import { NavLink } from "react-router-dom";
import { useUIStore } from "@/stores/uiStore";
import { cn } from "@/lib/utils";
import { 
  BarChart3, Upload, Settings, 
  ChevronLeft, ChevronRight, Sparkles, Library
} from "lucide-react";
import { Button } from "@/components/ui/button";

const navItems = [
  { 
    to: "/", 
    icon: Library, 
    label: "Collection",
    description: "Browse your coins"
  },
  { 
    to: "/stats", 
    icon: BarChart3, 
    label: "Statistics",
    description: "Collection analytics"
  },
  { 
    to: "/import", 
    icon: Upload, 
    label: "Import",
    description: "Add from file"
  },
  { 
    to: "/bulk-enrich", 
    icon: Sparkles, 
    label: "Enrich",
    description: "Catalog lookup"
  },
  { 
    to: "/settings", 
    icon: Settings, 
    label: "Settings",
    description: "Preferences"
  },
];

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  
  return (
    <aside className={cn(
      "fixed left-0 top-14 bottom-0 z-40 border-r bg-card/50 backdrop-blur-sm transition-all duration-200 flex flex-col",
      sidebarOpen ? "w-52" : "w-14"
    )}>
      {/* Navigation */}
      <nav className="flex-1 flex flex-col gap-0.5 p-2 pt-3">
        {navItems.map(({ to, icon: Icon, label, description }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => cn(
              "flex items-center gap-3 px-2.5 py-2 rounded-md transition-all group relative",
              isActive 
                ? "bg-primary/10 text-primary font-medium" 
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            )}
          >
            {({ isActive }) => (
              <>
                {/* Active indicator */}
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-primary rounded-full" />
                )}
                
                {/* Icon */}
                <div className={cn(
                  "flex-shrink-0 w-8 h-8 rounded-md flex items-center justify-center transition-colors",
                  isActive 
                    ? "bg-primary/15 text-primary" 
                    : "bg-muted/50 text-muted-foreground group-hover:bg-muted group-hover:text-foreground"
                )}>
                  <Icon className="w-4 h-4" />
                </div>
                
                {/* Label and description */}
                {sidebarOpen && (
                  <div className="flex flex-col min-w-0">
                    <span className="text-sm truncate">{label}</span>
                    <span className={cn(
                      "text-[10px] truncate transition-colors",
                      isActive ? "text-primary/70" : "text-muted-foreground/70"
                    )}>
                      {description}
                    </span>
                  </div>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>
      
      {/* Bottom section */}
      <div className="p-2 border-t">
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            "w-full justify-center text-muted-foreground hover:text-foreground",
            sidebarOpen ? "px-2" : "px-0"
          )}
          onClick={toggleSidebar}
        >
          {sidebarOpen ? (
            <>
              <ChevronLeft className="w-4 h-4 mr-2" />
              <span className="text-xs">Collapse</span>
            </>
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </Button>
      </div>
    </aside>
  );
}
