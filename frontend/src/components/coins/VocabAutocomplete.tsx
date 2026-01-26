import { useState, useMemo, useCallback } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Check, Search, AlertCircle, Loader2, Sparkles } from 'lucide-react'
import { 
  Command, 
  CommandInput, 
  CommandList, 
  CommandEmpty, 
  CommandItem,
  CommandGroup
} from '@/components/ui/command'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'
import { useDebounce } from '@/hooks/useDebounce'

// V3 API response types
interface VocabTermResponse {
  id: number
  vocab_type: string
  canonical_name: string
  nomisma_uri: string | null
  metadata: {
    issuer_type?: string
    reign_start?: number
    reign_end?: number
    period_start?: number
    period_end?: number
    active_from?: number
    active_to?: number
    rulers?: string[]
    expected_count?: number
    [key: string]: unknown
  }
}

interface NormalizeResponse {
  success: boolean
  term: VocabTermResponse | null
  method: string
  confidence: number
  needs_review: boolean
  alternatives: VocabTermResponse[]
}

// Supported vocab types
type VocabType = 'issuer' | 'mint' | 'denomination' | 'dynasty' | 'canonical_series'

// Map display names
const VOCAB_TYPE_LABELS: Record<VocabType, string> = {
  issuer: 'Issuer',
  mint: 'Mint',
  denomination: 'Denomination',
  dynasty: 'Dynasty',
  canonical_series: 'Series Template',
}

interface VocabAutocompleteProps {
  vocabType: VocabType
  value: number | null
  displayValue?: string
  onChange: (id: number | null, display: string) => void
  placeholder?: string
  dateContext?: { start?: number; end?: number }
  className?: string
  allowNormalize?: boolean  // Enable Enter-to-normalize behavior
}

export function VocabAutocomplete({
  vocabType,
  value,
  displayValue,
  onChange,
  placeholder = 'Select...',
  dateContext,
  className,
  allowNormalize = true,
}: VocabAutocompleteProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [normalizing, setNormalizing] = useState(false)
  const debouncedSearch = useDebounce(search, 300)
  
  // V3 API: Fetch options using FTS5 search
  const { data, isLoading } = useQuery({
    queryKey: ['vocab', 'v3', vocabType, debouncedSearch],
    queryFn: async () => {
      if (!debouncedSearch || debouncedSearch.length < 1) {
        return [] as VocabTermResponse[]
      }
      const response = await api.get(`/api/v2/vocab/search/${vocabType}`, {
        params: { q: debouncedSearch, limit: 20 }
      })
      return response.data as VocabTermResponse[]
    },
    enabled: open && debouncedSearch.length >= 1,
  })
  
  // V3 API: Get current selection detail for temporal validation
  const { data: selectedOption } = useQuery({
    queryKey: ['vocab', 'v3', vocabType, 'detail', value],
    queryFn: async () => {
      if (!value) return null
      const response = await api.get(`/api/v2/vocab/terms/${vocabType}/${value}`)
      return response.data as VocabTermResponse
    },
    enabled: !!value,
  })
  
  // V3 API: Normalize mutation
  const normalizeMutation = useMutation({
    mutationFn: async (raw: string) => {
      const response = await api.post('/api/v2/vocab/normalize', {
        raw,
        vocab_type: vocabType,
        context: {}
      })
      return response.data as NormalizeResponse
    },
    onSuccess: (result) => {
      if (result.success && result.term) {
        onChange(result.term.id, result.term.canonical_name)
        setOpen(false)
      }
      setNormalizing(false)
    },
    onError: () => {
      setNormalizing(false)
    }
  })
  
  // Handle Enter-to-normalize
  const handleNormalize = useCallback(async () => {
    if (!search || search.length < 2 || !allowNormalize) return
    
    setNormalizing(true)
    normalizeMutation.mutate(search)
  }, [search, allowNormalize, normalizeMutation])
  
  // Handle keyboard events
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading && (!data || data.length === 0) && search.length >= 2) {
      e.preventDefault()
      handleNormalize()
    }
  }, [isLoading, data, search, handleNormalize])
  
  // Temporal validation
  const temporalWarning = useMemo(() => {
    if (!selectedOption || !dateContext || (!dateContext.start && !dateContext.end)) return null
    
    const metadata = selectedOption.metadata || {}
    const start = metadata.reign_start ?? metadata.period_start ?? metadata.active_from
    const end = metadata.reign_end ?? metadata.period_end ?? metadata.active_to
    
    if (end !== undefined && dateContext.start !== undefined && dateContext.start > end) {
      return `Coin dated ${formatYear(dateContext.start)} but ${selectedOption.canonical_name} ended ${formatYear(end)}`
    }
    if (start !== undefined && dateContext.end !== undefined && dateContext.end < start) {
      return `Coin dated ${formatYear(dateContext.end)} but ${selectedOption.canonical_name} started ${formatYear(start)}`
    }
    return null
  }, [selectedOption, dateContext])
  
  // Get display info for an option
  const getOptionInfo = (option: VocabTermResponse) => {
    const metadata = option.metadata || {}
    const start = metadata.reign_start ?? metadata.period_start ?? metadata.active_from
    const end = metadata.reign_end ?? metadata.period_end ?? metadata.active_to
    const issuerType = metadata.issuer_type
    const rulers = metadata.rulers
    const expectedCount = metadata.expected_count
    
    const parts: string[] = []
    
    if (issuerType) {
      parts.push(issuerType.charAt(0).toUpperCase() + issuerType.slice(1))
    }
    
    if (start !== undefined || end !== undefined) {
      const startStr = formatYear(start)
      const endStr = formatYear(end) || 'present'
      parts.push(`${startStr} – ${endStr}`)
    }
    
    if (rulers && rulers.length > 0) {
      const rulerPreview = rulers.slice(0, 3).join(', ')
      const suffix = rulers.length > 3 ? ` +${rulers.length - 3} more` : ''
      parts.push(`${rulerPreview}${suffix}`)
    }
    
    if (expectedCount !== undefined) {
      parts.push(`${expectedCount} items`)
    }
    
    return parts.join(' • ')
  }
  
  return (
    <div className={cn('space-y-1', className)}>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className={cn(
              "w-full justify-between font-normal",
              !value && "text-muted-foreground",
              temporalWarning && "border-yellow-500 bg-yellow-50/50 dark:bg-yellow-950/20"
            )}
          >
            {selectedOption?.canonical_name || displayValue || placeholder}
            <Search className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </DialogTrigger>
        <DialogContent className="p-0 sm:max-w-[450px]">
          <DialogHeader className="p-4 pb-0">
            <DialogTitle>Search {VOCAB_TYPE_LABELS[vocabType]}</DialogTitle>
          </DialogHeader>
          <Command shouldFilter={false} className="rounded-lg">
            <CommandInput 
              placeholder={`Search ${VOCAB_TYPE_LABELS[vocabType].toLowerCase()}...`} 
              value={search}
              onValueChange={setSearch}
              onKeyDown={handleKeyDown}
            />
            <CommandList>
              {isLoading || normalizing ? (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  {normalizing && <span className="ml-2 text-sm text-muted-foreground">Normalizing...</span>}
                </div>
              ) : data && data.length === 0 && search.length >= 2 ? (
                <CommandEmpty>
                  <div className="flex flex-col items-center gap-2 py-4">
                    <p className="text-sm text-muted-foreground">No results found.</p>
                    <div className="flex flex-col gap-2 w-full px-4">
                      {allowNormalize && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleNormalize}
                          className="gap-1.5 w-full justify-start"
                        >
                          <Sparkles className="h-3.5 w-3.5" />
                          Normalize "{search}"
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          onChange(null, search)
                          setOpen(false)
                        }}
                        className="gap-1.5 w-full justify-start text-muted-foreground hover:text-foreground"
                      >
                        <Check className="h-3.5 w-3.5" />
                        Use "{search}" as is
                      </Button>
                    </div>
                  </div>
                </CommandEmpty>
              ) : data && data.length === 0 ? (
                <CommandEmpty>Type to search...</CommandEmpty>
              ) : (
                <>
                  <CommandGroup>
                    {data?.map((option) => (
                      <CommandItem
                        key={option.id}
                        value={option.id.toString()}
                        onSelect={() => {
                          onChange(option.id, option.canonical_name)
                          setOpen(false)
                        }}
                        className="cursor-pointer"
                      >
                        <div className="flex w-full items-center justify-between">
                          <div className="flex flex-col">
                            <span className="font-medium">{option.canonical_name}</span>
                            {getOptionInfo(option) && (
                              <span className="text-xs text-muted-foreground">
                                {getOptionInfo(option)}
                              </span>
                            )}
                          </div>
                          {value === option.id && (
                            <Check className="h-4 w-4 text-primary" />
                          )}
                        </div>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                  {search && search.length > 1 && !data?.find(o => o.canonical_name.toLowerCase() === search.toLowerCase()) && (
                    <CommandGroup heading="Custom Value">
                      <CommandItem
                        value={`raw-${search}`}
                        onSelect={() => {
                          onChange(null, search)
                          setOpen(false)
                        }}
                        className="cursor-pointer"
                      >
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Check className="h-3.5 w-3.5" />
                          Use "{search}" as is
                        </div>
                      </CommandItem>
                    </CommandGroup>
                  )}
                </>
              )}
            </CommandList>
          </Command>
        </DialogContent>
      </Dialog>
      
      {temporalWarning && (
        <div className="flex items-center gap-1.5 text-xs text-yellow-600 dark:text-yellow-400 px-1">
          <AlertCircle className="h-3.5 w-3.5" />
          <span>{temporalWarning}</span>
        </div>
      )}
    </div>
  )
}

function formatYear(year?: number): string {
  if (year === undefined || year === null) return ''
  return year < 0 ? `${Math.abs(year)} BC` : `AD ${year}`
}

// Legacy support: Map old vocab types to new ones
export function mapLegacyVocabType(legacyType: 'issuers' | 'mints'): VocabType {
  return legacyType === 'issuers' ? 'issuer' : 'mint'
}
