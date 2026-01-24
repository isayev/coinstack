import { useState, useCallback, useEffect } from "react";
import {
  Command,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
} from "@/components/ui/command";
import { Badge } from "@/components/ui/badge";
import { Loader2, ExternalLink } from "lucide-react";
import { useLookupReference, LookupResponse } from "@/hooks/useCatalog";
import { useDebounce } from "@/hooks/useDebounce";

interface ReferenceSuggestProps {
  value: string;
  onChange: (value: string) => void;
  onSelectSuggestion?: (suggestion: LookupResponse) => void;
  coinContext?: {
    ruler?: string;
    denomination?: string;
    mint?: string;
  };
  placeholder?: string;
}

export function ReferenceSuggest({
  value,
  onChange,
  onSelectSuggestion,
  coinContext,
  placeholder = "Enter reference (e.g., RIC I 207)",
}: ReferenceSuggestProps) {
  const [open, setOpen] = useState(false);
  const [suggestions, setSuggestions] = useState<LookupResponse | null>(null);
  const debouncedValue = useDebounce(value, 500);
  const lookupMutation = useLookupReference();
  
  // Fetch suggestions when debounced value changes
  useEffect(() => {
    if (debouncedValue && debouncedValue.length >= 3) {
      lookupMutation.mutate(
        {
          raw_reference: debouncedValue,
          context: coinContext,
        },
        {
          onSuccess: (result) => {
            setSuggestions(result);
            if (result.status === "success" || result.status === "ambiguous") {
              setOpen(true);
            }
          },
        }
      );
    } else {
      setSuggestions(null);
      setOpen(false);
    }
  }, [debouncedValue, coinContext]);
  
  const handleSelect = (suggestion: LookupResponse) => {
    setOpen(false);
    if (onSelectSuggestion) {
      onSelectSuggestion(suggestion);
    }
  };
  
  return (
    <div className="relative">
      <Command className="rounded-lg border shadow-md" shouldFilter={false}>
        <CommandInput
          placeholder={placeholder}
          value={value}
          onValueChange={onChange}
          onFocus={() => suggestions && setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 200)}
        />
        
        {open && (
          <CommandList>
            {lookupMutation.isPending && (
              <div className="flex items-center justify-center p-4">
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                <span className="text-sm text-muted-foreground">Looking up...</span>
              </div>
            )}
            
            {!lookupMutation.isPending && suggestions?.status === "not_found" && (
              <CommandEmpty>
                No matches found in catalog
              </CommandEmpty>
            )}
            
            {!lookupMutation.isPending && suggestions?.status === "success" && (
              <CommandGroup heading="Best Match">
                <CommandItem
                  value={suggestions.external_id || ""}
                  onSelect={() => handleSelect(suggestions)}
                  className="cursor-pointer"
                >
                  <SuggestionItem suggestion={suggestions} />
                </CommandItem>
              </CommandGroup>
            )}
            
            {!lookupMutation.isPending && suggestions?.status === "ambiguous" && suggestions.candidates && (
              <CommandGroup heading="Multiple Matches">
                {suggestions.candidates.map((candidate, i) => (
                  <CommandItem
                    key={candidate.external_id || i}
                    value={candidate.external_id}
                    onSelect={() => handleSelect({
                      ...suggestions,
                      status: "success",
                      external_id: candidate.external_id,
                      external_url: candidate.external_url,
                      confidence: candidate.confidence,
                    })}
                    className="cursor-pointer"
                  >
                    <CandidateItem candidate={candidate} />
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
            
            {!lookupMutation.isPending && suggestions?.status === "deferred" && (
              <CommandGroup heading="Manual Lookup Required">
                <CommandItem className="cursor-pointer">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">
                      {suggestions.error_message || "API not available"}
                    </span>
                    {suggestions.external_url && (
                      <a
                        href={suggestions.external_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:underline flex items-center gap-1"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Open catalog
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </CommandItem>
              </CommandGroup>
            )}
          </CommandList>
        )}
      </Command>
      
      {/* Status indicator */}
      {suggestions && !open && (
        <div className="mt-1 text-xs text-muted-foreground">
          {suggestions.status === "success" && (
            <span className="text-green-600">
              Matched: {suggestions.external_id}
            </span>
          )}
          {suggestions.status === "not_found" && (
            <span className="text-red-600">
              Not found in catalog
            </span>
          )}
          {suggestions.status === "ambiguous" && (
            <span className="text-yellow-600">
              {suggestions.candidates?.length} possible matches - select one
            </span>
          )}
        </div>
      )}
    </div>
  );
}

// Suggestion item component
function SuggestionItem({ suggestion }: { suggestion: LookupResponse }) {
  const payload = suggestion.payload as any;
  
  return (
    <div className="flex flex-col gap-1 w-full">
      <div className="flex items-center justify-between">
        <span className="font-medium">{suggestion.external_id}</span>
        <Badge variant="outline" className="text-xs">
          {Math.round((suggestion.confidence || 0) * 100)}% match
        </Badge>
      </div>
      {payload && (
        <div className="text-sm text-muted-foreground">
          {payload.authority && <span>{payload.authority}</span>}
          {payload.authority && payload.mint && <span> • </span>}
          {payload.mint && <span>{payload.mint}</span>}
          {(payload.authority || payload.mint) && payload.date_from && <span> • </span>}
          {payload.date_from && (
            <span>
              {payload.date_from < 0 ? `${Math.abs(payload.date_from)} BC` : `AD ${payload.date_from}`}
              {payload.date_to && payload.date_to !== payload.date_from && (
                <span>
                  –{payload.date_to < 0 ? `${Math.abs(payload.date_to)} BC` : payload.date_to}
                </span>
              )}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

// Candidate item component
function CandidateItem({ candidate }: { candidate: any }) {
  return (
    <div className="flex flex-col gap-1 w-full">
      <div className="flex items-center justify-between">
        <span className="font-medium">{candidate.name || candidate.external_id}</span>
        <Badge variant="outline" className="text-xs">
          {Math.round((candidate.confidence || 0) * 100)}%
        </Badge>
      </div>
      {candidate.description && (
        <div className="text-sm text-muted-foreground line-clamp-1">
          {candidate.description}
        </div>
      )}
    </div>
  );
}
