import { useUIStore } from "@/stores/uiStore";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Command, CommandInput, CommandList, CommandEmpty, CommandItem } from "@/components/ui/command";
import { useNavigate } from "react-router-dom";
import { Coins, BarChart3, Upload, Settings, Plus } from "lucide-react";

const commands = [
  { id: "add-coin", label: "Add Coin", icon: Plus, path: "/coins/new" },
  { id: "collection", label: "Collection", icon: Coins, path: "/" },
  { id: "stats", label: "Statistics", icon: BarChart3, path: "/stats" },
  { id: "import", label: "Import", icon: Upload, path: "/import" },
  { id: "settings", label: "Settings", icon: Settings, path: "/settings" },
];

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();
  const navigate = useNavigate();
  
  return (
    <Dialog open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen}>
      <DialogContent className="p-0 max-w-lg">
        <Command>
          <CommandInput placeholder="Type a command or search..." />
          <CommandList>
            <CommandEmpty>No results found.</CommandEmpty>
            {commands.map((cmd) => {
              const Icon = cmd.icon;
              return (
                <CommandItem
                  key={cmd.id}
                  onSelect={() => {
                    navigate(cmd.path);
                    setCommandPaletteOpen(false);
                  }}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {cmd.label}
                </CommandItem>
              );
            })}
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
