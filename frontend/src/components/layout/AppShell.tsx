import { ReactNode } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { CommandPalette } from "./CommandPalette";
import { useUIStore } from "@/stores/uiStore";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: ReactNode }) {
  const { sidebarOpen } = useUIStore();
  
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className={cn(
          "flex-1 transition-all duration-200",
          sidebarOpen ? "ml-64" : "ml-16"
        )}>
          {children}
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}
