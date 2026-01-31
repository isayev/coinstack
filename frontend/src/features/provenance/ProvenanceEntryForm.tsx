/**
 * ProvenanceEntryForm - Progressive disclosure form for provenance entries
 *
 * Features:
 * - 3-level progressive disclosure (Basic → Auction Details → Documentation)
 * - Event type-aware field visibility
 * - Auction house suggestions with auto-currency
 * - Zod validation with React Hook Form
 */

import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Gavel,
  Store,
  Library,
  Handshake,
  BookOpen,
  Map,
  Home,
  ShoppingBag,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import {
  ProvenanceFormSchema,
  ProvenanceFormData,
  PROVENANCE_EVENT_TYPES,
  COMMON_AUCTION_HOUSES,
  getDefaultCurrency,
  detectEventType,
  getDefaultFormValues,
  type ProvenanceEventTypeValue,
} from './schema';

// Icon mapping for event types
const EVENT_TYPE_ICONS: Record<string, React.ElementType> = {
  auction: Gavel,
  dealer: Store,
  collection: Library,
  private_sale: Handshake,
  publication: BookOpen,
  hoard_find: Map,
  estate: Home,
  acquisition: ShoppingBag,
};

interface ProvenanceEntryFormProps {
  /** Initial values for editing */
  initialValues?: Partial<ProvenanceFormData>;
  /** Submit handler */
  onSubmit: (data: ProvenanceFormData) => void;
  /** Cancel handler */
  onCancel: () => void;
  /** Whether form is submitting */
  isSubmitting?: boolean;
  /** Mode: add or edit */
  mode?: 'add' | 'edit';
}

export function ProvenanceEntryForm({
  initialValues,
  onSubmit,
  onCancel,
  isSubmitting = false,
  mode = 'add',
}: ProvenanceEntryFormProps) {
  const [showAuctionDetails, setShowAuctionDetails] = useState(false);
  const [showDocumentation, setShowDocumentation] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<ProvenanceFormData>({
    resolver: zodResolver(ProvenanceFormSchema),
    defaultValues: {
      ...getDefaultFormValues('auction'),
      ...initialValues,
    },
  });

  const eventType = watch('event_type');
  const sourceName = watch('source_name');

  // Auto-detect event type from source name
  useEffect(() => {
    if (sourceName && mode === 'add') {
      const detected = detectEventType(sourceName);
      if (detected !== eventType) {
        setValue('event_type', detected);
      }
      // Auto-set currency for known auction houses
      const currency = getDefaultCurrency(sourceName);
      if (currency !== 'USD') {
        setValue('currency', currency);
      }
    }
  }, [sourceName, mode, eventType, setValue]);

  // Reset form when initialValues change (edit mode)
  useEffect(() => {
    if (initialValues) {
      reset({ ...getDefaultFormValues('auction'), ...initialValues });
      // Expand sections if they have data
      if (initialValues.sale_name || initialValues.lot_number || initialValues.hammer_price) {
        setShowAuctionDetails(true);
      }
      if (initialValues.url || initialValues.notes) {
        setShowDocumentation(true);
      }
    }
  }, [initialValues, reset]);

  // Should show auction/sale details section?
  const showAuctionSection = ['auction', 'dealer', 'private_sale'].includes(eventType);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* =========== LEVEL 1: Basic Info (Always Visible) =========== */}
      <div className="space-y-4">
        {/* Event Type Selection */}
        <div className="space-y-2">
          <Label className="text-xs font-semibold text-muted-foreground">Event Type</Label>
          <div className="grid grid-cols-4 gap-2">
            {PROVENANCE_EVENT_TYPES.map((type) => {
              const Icon = EVENT_TYPE_ICONS[type.value] || Library;
              const isSelected = eventType === type.value;
              return (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setValue('event_type', type.value as ProvenanceEventTypeValue)}
                  className={cn(
                    'flex flex-col items-center gap-1 p-2 rounded-lg border transition-all',
                    isSelected
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border hover:border-primary/50 text-muted-foreground hover:text-foreground'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span className="text-[10px] font-medium">{type.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Source Name with Suggestions */}
        <div className="space-y-2">
          <Label htmlFor="source_name" className="text-xs font-semibold text-muted-foreground">
            {eventType === 'auction'
              ? 'Auction House'
              : eventType === 'dealer'
              ? 'Dealer Name'
              : eventType === 'collection'
              ? 'Collection Name'
              : 'Source Name'}
          </Label>
          <Input
            id="source_name"
            {...register('source_name')}
            placeholder={
              eventType === 'auction'
                ? 'e.g. Heritage Auctions, CNG'
                : eventType === 'collection'
                ? 'e.g. The Hunt Collection'
                : eventType === 'dealer'
                ? 'e.g. Harlan J. Berk'
                : 'Source name...'
            }
            list="auction-houses"
            autoComplete="off"
          />
          <datalist id="auction-houses">
            {COMMON_AUCTION_HOUSES.map((house) => (
              <option key={house.name} value={house.name} />
            ))}
          </datalist>
          {errors.source_name && (
            <p className="text-xs text-destructive">{errors.source_name.message}</p>
          )}
        </div>

        {/* Date Fields (Flexible) */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="event_date" className="text-xs font-semibold text-muted-foreground">
              Exact Date
            </Label>
            <Input
              id="event_date"
              type="date"
              {...register('event_date')}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="date_string" className="text-xs font-semibold text-muted-foreground">
              Or Approximate
            </Label>
            <Input
              id="date_string"
              {...register('date_string')}
              placeholder="e.g. 1920s, circa 1980"
            />
          </div>
        </div>
        {errors.date_string && (
          <p className="text-xs text-destructive">{errors.date_string.message}</p>
        )}
      </div>

      {/* =========== LEVEL 2: Auction/Sale Details (Collapsible) =========== */}
      {showAuctionSection && (
        <Collapsible open={showAuctionDetails} onOpenChange={setShowAuctionDetails}>
          <CollapsibleTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="w-full justify-between text-muted-foreground hover:text-foreground"
            >
              <span className="text-xs font-semibold">Sale Details</span>
              {showAuctionDetails ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-4 pt-2">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">Sale Name</Label>
                <Input
                  {...register('sale_name')}
                  placeholder="e.g. January NYINC Sale"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">Sale #</Label>
                <Input
                  {...register('sale_number')}
                  placeholder="e.g. 114"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">Lot #</Label>
                <Input
                  {...register('lot_number')}
                  placeholder="e.g. 1234"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">Catalog Ref</Label>
                <Input
                  {...register('catalog_reference')}
                  placeholder="e.g. cf. RIC 245"
                />
              </div>
            </div>

            {/* Pricing Section */}
            <div className="space-y-2">
              <Label className="text-xs font-semibold text-muted-foreground">Pricing</Label>
              <div className="grid grid-cols-4 gap-2">
                <div className="col-span-1">
                  <Input
                    type="number"
                    step="0.01"
                    {...register('hammer_price')}
                    placeholder="Hammer"
                  />
                </div>
                <div className="col-span-1">
                  <Input
                    type="number"
                    step="0.1"
                    {...register('buyers_premium_pct')}
                    placeholder="BP %"
                  />
                </div>
                <div className="col-span-1">
                  <Input
                    type="number"
                    step="0.01"
                    {...register('total_price')}
                    placeholder="Total"
                  />
                </div>
                <div className="col-span-1">
                  <Select
                    onValueChange={(val) => setValue('currency', val)}
                    defaultValue={watch('currency') || 'USD'}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="USD">USD</SelectItem>
                      <SelectItem value="EUR">EUR</SelectItem>
                      <SelectItem value="GBP">GBP</SelectItem>
                      <SelectItem value="CHF">CHF</SelectItem>
                      <SelectItem value="AUD">AUD</SelectItem>
                      <SelectItem value="CAD">CAD</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      )}

      {/* =========== LEVEL 3: Documentation (Collapsible) =========== */}
      <Collapsible open={showDocumentation} onOpenChange={setShowDocumentation}>
        <CollapsibleTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="w-full justify-between text-muted-foreground hover:text-foreground"
          >
            <span className="text-xs font-semibold">Documentation</span>
            {showDocumentation ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-4 pt-2">
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">URL/Link</Label>
            <Input
              type="url"
              {...register('url')}
              placeholder="https://..."
            />
            {errors.url && (
              <p className="text-xs text-destructive">{errors.url.message}</p>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="receipt_available"
              checked={watch('receipt_available')}
              onCheckedChange={(checked) => setValue('receipt_available', checked as boolean)}
            />
            <Label htmlFor="receipt_available" className="text-sm text-muted-foreground">
              Receipt/documentation available
            </Label>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Notes</Label>
            <Textarea
              {...register('notes')}
              placeholder="Additional details, pedigree notes..."
              className="resize-none h-20"
            />
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* =========== Actions =========== */}
      <div className="flex justify-end gap-2 pt-4 border-t">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting
            ? mode === 'edit'
              ? 'Saving...'
              : 'Adding...'
            : mode === 'edit'
            ? 'Save Changes'
            : 'Add Entry'}
        </Button>
      </div>
    </form>
  );
}
