import { NavLink } from "react-router-dom";
import { useUIStore } from "@/stores/uiStore";
import { cn } from "@/lib/utils";
import { 
  BarChart3, Upload, Settings, 
  ChevronLeft, ChevronRight, Sparkles, Library
} from "lucide-react";
import { Button } from "@/components/ui/button";

const navItems = [
  { to: "/", icon: Library, label: "Collection" },
  { to: "/stats", icon: BarChart3, label: "Statistics" },
  { to: "/import", icon: Upload, label: "Import" },
  { to: "/bulk-enrich", icon: Sparkles, label: "Enrich" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  
  return (
    <aside 
      className={cn(
        "fixed left-0 top-14 bottom-0 z-40 transition-all duration-200 flex flex-col",
        sidebarOpen ? "w-48" : "w-14"
      )}
      style={{ 
        background: 'var(--bg-surface)',
        borderRight: '1px solid var(--border-subtle)'
      }}
    >
      {/* Navigation */}
      <nav className="flex-1 flex flex-col gap-1 p-2 pt-3">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => cn(
              "flex items-center gap-3 px-2.5 py-2 rounded-md transition-all relative",
              isActive 
                ? "font-medium" 
                : "hover:bg-[var(--bg-elevated)]"
            )}
            style={({ isActive }) => ({
              color: isActive ? 'var(--metal-au)' : 'var(--text-secondary)',
              background: isActive ? 'var(--metal-au-subtle)' : undefined,
            })}
          >
            {({ isActive }) => (
              <>
                {/* Active indicator bar */}
                {isActive && (
                  <div 
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full"
                    style={{ background: 'var(--metal-au)' }}
                  />
                )}
                
                {/* Icon */}
                <Icon className="w-5 h-5 flex-shrink-0" />
                
                {/* Label */}
                {sidebarOpen && (
                  <span className="text-sm">{label}</span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>
      
      {/* Bottom section */}
      <div className="p-2" style={{ borderTop: '1px solid var(--border-subtle)' }}>
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            "w-full justify-center",
            sidebarOpen ? "px-2" : "px-0"
          )}
          style={{ color: 'var(--text-tertiary)' }}
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
