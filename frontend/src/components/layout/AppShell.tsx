import { ReactNode, useEffect } from "react";
import { CommandBar } from "./CommandBar";
import { Sidebar } from "./Sidebar";
import { CommandPalette } from "./CommandPalette";
import { useUIStore, getScreenSize } from "@/stores/uiStore";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: ReactNode }) {
  const { sidebarOpen, setScreenSize } = useUIStore();

  useEffect(() => {
    const handleResize = () => {
      setScreenSize(getScreenSize());
    };

    handleResize();

    let timeoutId: NodeJS.Timeout;
    const debouncedResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(handleResize, 100);
    };

    window.addEventListener('resize', debouncedResize);
    return () => {
      window.removeEventListener('resize', debouncedResize);
      clearTimeout(timeoutId);
    };
  }, [setScreenSize]);

  return (
    <div
      className="min-h-screen"
      style={{ background: 'var(--bg-app)' }}
    >
      <CommandBar />
      <div className="flex">
        <Sidebar />
        <main className={cn(
          "flex-1 transition-all duration-200",
          sidebarOpen ? "ml-48" : "ml-14"
        )}>
          {children}
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}
