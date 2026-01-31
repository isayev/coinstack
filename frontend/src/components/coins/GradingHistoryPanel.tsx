/**
 * GradingHistoryPanel - Displays and manages a coin's TPG grading lifecycle.
 *
 * Shows a timeline of grading events (initial submission, crossovers, regrades, crack-outs)
 * with the ability to add, edit, delete, and mark entries as current.
 */

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  ChevronDown,
  ChevronRight,
  Plus,
  Pencil,
  Trash2,
  Star,
  StarOff,
  Award,
  RefreshCw,
  ArrowRightLeft,
  Scissors,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { toast } from 'sonner'

import {
  useGradingHistory,
  useCreateGradingHistory,
  useUpdateGradingHistory,
  useDeleteGradingHistory,
  useSetCurrentGrading,
  type GradingHistoryEntry,
} from '@/hooks/useGradingHistory'

// Form schema
const GradingHistoryFormSchema = z.object({
  grading_state: z.string().min(1, 'Grading state is required'),
  event_type: z.string().min(1, 'Event type is required'),
  grade: z.string().optional(),
  grade_service: z.string().optional(),
  certification_number: z.string().optional(),
  strike_quality: z.string().optional(),
  surface_quality: z.string().optional(),
  grade_numeric: z.coerce.number().optional(),
  designation: z.string().optional(),
  has_star: z.boolean().default(false),
  photo_cert: z.boolean().default(false),
  verification_url: z.string().optional(),
  graded_date: z.string().optional(),
  submitter: z.string().optional(),
  turnaround_days: z.coerce.number().optional(),
  grading_fee: z.coerce.number().optional(),
  notes: z.string().optional(),
  sequence_order: z.coerce.number().default(0),
  is_current: z.boolean().default(false),
})

type GradingHistoryForm = z.infer<typeof GradingHistoryFormSchema>

// Type for create mutation input (excludes auto-generated fields)
type GradingHistoryCreateInput = Omit<GradingHistoryEntry, 'id' | 'coin_id' | 'recorded_at'>

interface GradingHistoryPanelProps {
  coinId: number
  expanded?: boolean
  onExpandChange?: (expanded: boolean) => void
}

const EVENT_TYPE_CONFIG = {
  initial: { label: 'Initial Submission', icon: Award, color: 'bg-green-500' },
  crossover: { label: 'Crossover', icon: ArrowRightLeft, color: 'bg-blue-500' },
  regrade: { label: 'Regrade', icon: RefreshCw, color: 'bg-amber-500' },
  crack_out: { label: 'Crack Out', icon: Scissors, color: 'bg-red-500' },
}

const GRADING_STATES = ['raw', 'slabbed', 'capsule', 'flip']
const GRADE_SERVICES = ['ngc', 'pcgs', 'icg', 'anacs']

// NGC Ancients strike/surface quality scales (1-5)
const QUALITY_SCALE = [
  { value: '5', label: '5 - Superb' },
  { value: '4', label: '4 - Choice' },
  { value: '3', label: '3 - Fine' },
  { value: '2', label: '2 - Fair' },
  { value: '1', label: '1 - Poor' },
]

export function GradingHistoryPanel({
  coinId,
  expanded = false,
  onExpandChange,
}: GradingHistoryPanelProps) {
  const [isExpanded, setIsExpanded] = useState(expanded)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingEntry, setEditingEntry] = useState<GradingHistoryEntry | null>(null)
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [entryToDelete, setEntryToDelete] = useState<number | null>(null)

  const { data, isLoading, error } = useGradingHistory(coinId)
  const createMutation = useCreateGradingHistory(coinId)
  const updateMutation = useUpdateGradingHistory(coinId)
  const deleteMutation = useDeleteGradingHistory(coinId)
  const setCurrentMutation = useSetCurrentGrading(coinId)

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<GradingHistoryForm>({
    resolver: zodResolver(GradingHistoryFormSchema),
    defaultValues: {
      grading_state: 'raw',
      event_type: 'initial',
      has_star: false,
      photo_cert: false,
      is_current: false,
      sequence_order: 0,
    },
  })

  const gradingState = watch('grading_state')
  const gradeService = watch('grade_service')
  const eventType = watch('event_type')
  const strikeQuality = watch('strike_quality')
  const surfaceQuality = watch('surface_quality')

  const handleExpandChange = (newExpanded: boolean) => {
    setIsExpanded(newExpanded)
    onExpandChange?.(newExpanded)
  }

  const openAddDialog = () => {
    setEditingEntry(null)
    reset({
      grading_state: 'raw',
      event_type: 'initial',
      has_star: false,
      photo_cert: false,
      is_current: false,
      sequence_order: data?.entries.length ?? 0,
    })
    setDialogOpen(true)
  }

  const openEditDialog = (entry: GradingHistoryEntry) => {
    setEditingEntry(entry)
    reset({
      grading_state: entry.grading_state || 'raw',
      event_type: entry.event_type,
      grade: entry.grade || '',
      grade_service: entry.grade_service || '',
      certification_number: entry.certification_number || '',
      strike_quality: entry.strike_quality || '',
      surface_quality: entry.surface_quality || '',
      grade_numeric: entry.grade_numeric ?? undefined,
      designation: entry.designation || '',
      has_star: entry.has_star,
      photo_cert: entry.photo_cert,
      verification_url: entry.verification_url || '',
      graded_date: entry.graded_date || '',
      submitter: entry.submitter || '',
      turnaround_days: entry.turnaround_days ?? undefined,
      grading_fee: entry.grading_fee ?? undefined,
      notes: entry.notes || '',
      sequence_order: entry.sequence_order,
      is_current: entry.is_current,
    })
    setDialogOpen(true)
  }

  const onSubmit = async (formData: GradingHistoryForm) => {
    try {
      const entryData: GradingHistoryCreateInput = {
        grading_state: formData.grading_state,
        event_type: formData.event_type,
        grade: formData.grade || undefined,
        grade_service: formData.grade_service || undefined,
        certification_number: formData.certification_number || undefined,
        strike_quality: formData.strike_quality || undefined,
        surface_quality: formData.surface_quality || undefined,
        grade_numeric: formData.grade_numeric || undefined,
        designation: formData.designation || undefined,
        has_star: formData.has_star,
        photo_cert: formData.photo_cert,
        verification_url: formData.verification_url || undefined,
        graded_date: formData.graded_date || undefined,
        submitter: formData.submitter || undefined,
        turnaround_days: formData.turnaround_days || undefined,
        grading_fee: formData.grading_fee || undefined,
        notes: formData.notes || undefined,
        sequence_order: formData.sequence_order,
        is_current: formData.is_current,
      }

      if (editingEntry) {
        await updateMutation.mutateAsync({
          entryId: editingEntry.id,
          entry: entryData,
        })
        toast.success('Grading history updated')
      } else {
        await createMutation.mutateAsync(entryData)
        toast.success('Grading history entry added')
      }
      setDialogOpen(false)
    } catch (e) {
      console.error(e)
      toast.error('Failed to save grading history')
    }
  }

  const handleDeleteClick = (entryId: number) => {
    setEntryToDelete(entryId)
    setDeleteConfirmOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (entryToDelete === null) return
    try {
      await deleteMutation.mutateAsync(entryToDelete)
      toast.success('Entry deleted')
    } catch (e) {
      toast.error('Failed to delete entry')
    } finally {
      setDeleteConfirmOpen(false)
      setEntryToDelete(null)
    }
  }

  const handleSetCurrent = async (entryId: number) => {
    try {
      await setCurrentMutation.mutateAsync(entryId)
      toast.success('Current grading updated')
    } catch (e) {
      toast.error('Failed to set current grading')
    }
  }

  const entries = data?.entries ?? []
  const currentEntry = entries.find((e) => e.is_current)

  return (
    <>
      <Card>
        <Collapsible open={isExpanded} onOpenChange={handleExpandChange}>
          <CollapsibleTrigger asChild>
            <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  <CardTitle className="text-sm font-medium">
                    Grading History
                  </CardTitle>
                  <Badge variant="secondary" className="text-xs">
                    {entries.length}
                  </Badge>
                </div>
                {currentEntry && (
                  <Badge variant="outline" className="text-xs">
                    Current: {currentEntry.grade_service?.toUpperCase()} {currentEntry.grade}
                  </Badge>
                )}
              </div>
            </CardHeader>
          </CollapsibleTrigger>

          <CollapsibleContent>
            <CardContent className="pt-0">
              {isLoading ? (
                <div className="text-sm text-muted-foreground py-4">Loading...</div>
              ) : error ? (
                <div className="text-sm text-destructive py-4">Failed to load grading history</div>
              ) : entries.length === 0 ? (
                <div className="text-sm text-muted-foreground py-4">
                  No grading history recorded.
                </div>
              ) : (
                <div className="space-y-2">
                  {entries.map((entry) => {
                    const config = EVENT_TYPE_CONFIG[entry.event_type as keyof typeof EVENT_TYPE_CONFIG]
                    const Icon = config?.icon ?? Award

                    return (
                      <div
                        key={entry.id}
                        className={`flex items-start gap-3 p-3 rounded-lg border ${
                          entry.is_current ? 'border-primary bg-primary/5' : 'border-border'
                        }`}
                      >
                        <div
                          className={`p-1.5 rounded-full ${config?.color ?? 'bg-gray-500'} text-white`}
                        >
                          <Icon className="h-3 w-3" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium text-sm">
                              {config?.label ?? entry.event_type}
                            </span>
                            {entry.is_current && (
                              <Badge variant="default" className="text-xs">
                                Current
                              </Badge>
                            )}
                            {entry.has_star && (
                              <Star className="h-3 w-3 text-amber-500 fill-amber-500" />
                            )}
                          </div>
                          <div className="text-sm text-muted-foreground mt-1">
                            {entry.grade_service && (
                              <span className="uppercase font-medium">{entry.grade_service}</span>
                            )}
                            {entry.grade && <span className="ml-1">{entry.grade}</span>}
                            {entry.grade_numeric && (
                              <span className="ml-1">({entry.grade_numeric})</span>
                            )}
                            {entry.certification_number && (
                              <span className="ml-2 text-xs">#{entry.certification_number}</span>
                            )}
                          </div>
                          {(entry.strike_quality || entry.surface_quality) && (
                            <div className="text-xs text-muted-foreground mt-1">
                              {entry.strike_quality && <span>Strike: {entry.strike_quality}/5</span>}
                              {entry.strike_quality && entry.surface_quality && <span className="mx-1">•</span>}
                              {entry.surface_quality && <span>Surface: {entry.surface_quality}/5</span>}
                            </div>
                          )}
                          {entry.graded_date && (
                            <div className="text-xs text-muted-foreground mt-1">
                              {entry.graded_date}
                            </div>
                          )}
                          {entry.notes && (
                            <div className="text-xs text-muted-foreground mt-1 italic">
                              {entry.notes}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          {!entry.is_current && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              onClick={() => handleSetCurrent(entry.id)}
                              title="Set as current"
                            >
                              <StarOff className="h-3 w-3" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7"
                            onClick={() => openEditDialog(entry)}
                            title="Edit"
                          >
                            <Pencil className="h-3 w-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 text-destructive"
                            onClick={() => handleDeleteClick(entry.id)}
                            title="Delete"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              <Button
                variant="outline"
                size="sm"
                className="mt-3 w-full"
                onClick={openAddDialog}
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Grading Event
              </Button>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>

        {/* Add/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingEntry ? 'Edit Grading Event' : 'Add Grading Event'}
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-2">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Event Type</Label>
                  <Select
                    onValueChange={(val) => setValue('event_type', val)}
                    value={eventType}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="initial">Initial Submission</SelectItem>
                      <SelectItem value="crossover">Crossover</SelectItem>
                      <SelectItem value="regrade">Regrade</SelectItem>
                      <SelectItem value="crack_out">Crack Out</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.event_type && (
                    <p className="text-xs text-destructive">{errors.event_type.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label>Grading State</Label>
                  <Select
                    onValueChange={(val) => setValue('grading_state', val)}
                    value={gradingState}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {GRADING_STATES.map((state) => (
                        <SelectItem key={state} value={state}>
                          {state.charAt(0).toUpperCase() + state.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.grading_state && (
                    <p className="text-xs text-destructive">{errors.grading_state.message}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Grade Service</Label>
                  <Select
                    onValueChange={(val) => setValue('grade_service', val)}
                    value={gradeService || ''}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select service" />
                    </SelectTrigger>
                    <SelectContent>
                      {GRADE_SERVICES.map((service) => (
                        <SelectItem key={service} value={service}>
                          {service.toUpperCase()}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Grade</Label>
                  <Input {...register('grade')} placeholder="e.g., Ch XF, MS 63" />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Certification #</Label>
                  <Input {...register('certification_number')} placeholder="TPG cert number" />
                </div>

                <div className="space-y-2">
                  <Label>Numeric Grade</Label>
                  <Input
                    type="number"
                    {...register('grade_numeric')}
                    min={1}
                    max={70}
                    placeholder="1-70"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Designation</Label>
                  <Input {...register('designation')} placeholder="Fine Style, Choice" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Strike Quality (NGC 1-5)</Label>
                  <Select
                    onValueChange={(val) => setValue('strike_quality', val)}
                    value={strikeQuality || ''}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select strike quality" />
                    </SelectTrigger>
                    <SelectContent>
                      {QUALITY_SCALE.map((q) => (
                        <SelectItem key={q.value} value={q.value}>
                          {q.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Surface Quality (NGC 1-5)</Label>
                  <Select
                    onValueChange={(val) => setValue('surface_quality', val)}
                    value={surfaceQuality || ''}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select surface quality" />
                    </SelectTrigger>
                    <SelectContent>
                      {QUALITY_SCALE.map((q) => (
                        <SelectItem key={q.value} value={q.value}>
                          {q.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Graded Date</Label>
                  <Input type="date" {...register('graded_date')} />
                </div>

                <div className="space-y-2">
                  <Label>Submitter</Label>
                  <Input {...register('submitter')} placeholder="Who submitted" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Turnaround Days</Label>
                  <Input type="number" {...register('turnaround_days')} min={0} />
                </div>

                <div className="space-y-2">
                  <Label>Grading Fee</Label>
                  <Input type="number" step="0.01" {...register('grading_fee')} min={0} />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Verification URL</Label>
                <Input {...register('verification_url')} placeholder="NGC/PCGS verify link" />
              </div>

              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="has_star"
                    checked={watch('has_star')}
                    onCheckedChange={(checked) => setValue('has_star', !!checked)}
                  />
                  <Label htmlFor="has_star" className="text-sm">
                    Star Designation
                  </Label>
                </div>

                <div className="flex items-center gap-2">
                  <Checkbox
                    id="photo_cert"
                    checked={watch('photo_cert')}
                    onCheckedChange={(checked) => setValue('photo_cert', !!checked)}
                  />
                  <Label htmlFor="photo_cert" className="text-sm">
                    Photo Certificate
                  </Label>
                </div>

                <div className="flex items-center gap-2">
                  <Checkbox
                    id="is_current"
                    checked={watch('is_current')}
                    onCheckedChange={(checked) => setValue('is_current', !!checked)}
                  />
                  <Label htmlFor="is_current" className="text-sm">
                    Current Grading
                  </Label>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  {...register('notes')}
                  placeholder="Additional notes about this grading event"
                  className="resize-none h-16"
                />
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? 'Saving...'
                    : editingEntry
                    ? 'Save Changes'
                    : 'Add Event'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Grading History Entry</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this grading history entry? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
