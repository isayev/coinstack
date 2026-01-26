import { useState } from "react"
import { Plus, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Monogram } from "@/domain/schemas"

interface MonogramPickerProps {
  value: Monogram[]
  onChange: (value: Monogram[]) => void
}

export function MonogramPicker({ value, onChange }: MonogramPickerProps) {
  const [isAdding, setIsAdding] = useState(false)
  const [newLabel, setNewLabel] = useState("")
  const [newUrl, setNewUrl] = useState("")

  const handleAdd = () => {
    if (!newLabel) return
    const newMonogram: Monogram = {
      label: newLabel,
      image_url: newUrl || null,
    }
    onChange([...value, newMonogram])
    setIsAdding(false)
    setNewLabel("")
    setNewUrl("")
  }

  const handleRemove = (index: number) => {
    onChange(value.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {value.map((m, i) => (
          <Badge key={i} variant="secondary" className="pl-3 pr-1 py-1 gap-2 h-8">
            <span className="font-mono text-xs">{m.label}</span>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-5 w-5 rounded-full"
              onClick={() => handleRemove(i)}
            >
              <X className="h-3 w-3" />
            </Button>
          </Badge>
        ))}
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-8 border-dashed gap-2"
          onClick={() => setIsAdding(true)}
        >
          <Plus className="h-3.5 w-3.5" />
          Add Monogram
        </Button>
      </div>

      {isAdding && (
        <div className="p-4 rounded-lg border bg-muted/30 space-y-3 animate-in fade-in zoom-in-95">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold uppercase text-muted-foreground">Label</label>
              <Input 
                placeholder="e.g. Price 123" 
                value={newLabel}
                onChange={(e) => setNewLabel(e.target.value)}
                className="h-9 text-sm"
                autoFocus
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold uppercase text-muted-foreground">Image URL (Optional)</label>
              <Input 
                placeholder="https://..." 
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                className="h-9 text-sm"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" size="sm" onClick={() => setIsAdding(false)}>Cancel</Button>
            <Button type="button" size="sm" onClick={handleAdd} disabled={!newLabel}>Add</Button>
          </div>
        </div>
      )}
    </div>
  )
}
