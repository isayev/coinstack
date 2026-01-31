/**
 * RarityAssessmentPanel - Displays and manages multi-source rarity assessments.
 *
 * Shows rarity data from catalogs, census data, and market analysis
 * with the ability to add, edit, delete, and mark assessments as primary.
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
  StarOff,
  BookOpen,
  BarChart3,
  FileSearch,
  Users,
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
  useRarityAssessments,
  useCreateRarityAssessment,
  useUpdateRarityAssessment,
  useDeleteRarityAssessment,
  useSetPrimaryRarityAssessment,
  type RarityAssessment,
} from '@/hooks/useRarityAssessments'

// Form schema
const RarityAssessmentFormSchema = z.object({
  rarity_code: z.string().min(1, 'Rarity code is required'),
  rarity_system: z.string().min(1, 'Rarity system is required'),
  source_type: z.string().min(1, 'Source type is required'),
  source_name: z.string().optional(),
  source_url: z.string().optional(),
  source_date: z.string().optional(),
  grade_range_low: z.string().optional(),
  grade_range_high: z.string().optional(),
  grade_conditional_notes: z.string().optional(),
  census_total: z.coerce.number().optional(),
  census_this_grade: z.coerce.number().optional(),
  census_finer: z.coerce.number().optional(),
  census_date: z.string().optional(),
  confidence: z.string().default('medium'),
  notes: z.string().optional(),
  is_primary: z.boolean().default(false),
})

type RarityAssessmentForm = z.infer<typeof RarityAssessmentFormSchema>

// Type for create mutation input (excludes auto-generated fields)
type RarityAssessmentCreateInput = Omit<RarityAssessment, 'id' | 'coin_id' | 'created_at'>

interface RarityAssessmentPanelProps {
  coinId: number
  expanded?: boolean
  onExpandChange?: (expanded: boolean) => void
}

// Rarity code color mapping
const RARITY_COLORS: Record<string, string> = {
  C: 'bg-green-500',
  S: 'bg-lime-500',
  R1: 'bg-yellow-500',
  R2: 'bg-amber-500',
  R3: 'bg-orange-500',
  R4: 'bg-red-400',
  R5: 'bg-red-500',
  RR: 'bg-red-600',
  RRR: 'bg-red-700',
  UNIQUE: 'bg-purple-600',
}

const SOURCE_TYPE_CONFIG = {
  catalog: { label: 'Catalog', icon: BookOpen, color: 'bg-blue-500' },
  census_data: { label: 'Census Data', icon: BarChart3, color: 'bg-green-500' },
  auction_analysis: { label: 'Auction Analysis', icon: FileSearch, color: 'bg-amber-500' },
  expert_opinion: { label: 'Expert Opinion', icon: Users, color: 'bg-purple-500' },
}

// Extended rarity systems including RRC (Roman Republican) and RPC (Roman Provincial)
const RARITY_SYSTEMS = [
  { value: 'ric', label: 'RIC (Roman Imperial Coinage)' },
  { value: 'rrc', label: 'RRC (Roman Republican Coinage)' },
  { value: 'rpc', label: 'RPC (Roman Provincial Coinage)' },
  { value: 'catalog', label: 'Catalog' },
  { value: 'census', label: 'Census' },
  { value: 'market_frequency', label: 'Market Frequency' },
]

const CONFIDENCE_LEVELS = [
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
]

export function RarityAssessmentPanel({
  coinId,
  expanded = false,
  onExpandChange,
}: RarityAssessmentPanelProps) {
  const [isExpanded, setIsExpanded] = useState(expanded)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingAssessment, setEditingAssessment] = useState<RarityAssessment | null>(null)
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [assessmentToDelete, setAssessmentToDelete] = useState<number | null>(null)

  const { data, isLoading, error } = useRarityAssessments(coinId)
  const createMutation = useCreateRarityAssessment(coinId)
  const updateMutation = useUpdateRarityAssessment(coinId)
  const deleteMutation = useDeleteRarityAssessment(coinId)
  const setPrimaryMutation = useSetPrimaryRarityAssessment(coinId)

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<RarityAssessmentForm>({
    resolver: zodResolver(RarityAssessmentFormSchema),
    defaultValues: {
      rarity_code: '',
      rarity_system: 'ric',
      source_type: 'catalog',
      confidence: 'medium',
      is_primary: false,
    },
  })

  const sourceType = watch('source_type')
  const raritySystem = watch('rarity_system')
  const confidence = watch('confidence')

  const handleExpandChange = (newExpanded: boolean) => {
    setIsExpanded(newExpanded)
    onExpandChange?.(newExpanded)
  }

  const openAddDialog = () => {
    setEditingAssessment(null)
    reset({
      rarity_code: '',
      rarity_system: 'ric',
      source_type: 'catalog',
      confidence: 'medium',
      is_primary: false,
    })
    setDialogOpen(true)
  }

  const openEditDialog = (assessment: RarityAssessment) => {
    setEditingAssessment(assessment)
    reset({
      rarity_code: assessment.rarity_code,
      rarity_system: assessment.rarity_system,
      source_type: assessment.source_type,
      source_name: assessment.source_name || '',
      source_url: assessment.source_url || '',
      source_date: assessment.source_date || '',
      grade_range_low: assessment.grade_range_low || '',
      grade_range_high: assessment.grade_range_high || '',
      grade_conditional_notes: assessment.grade_conditional_notes || '',
      census_total: assessment.census_total ?? undefined,
      census_this_grade: assessment.census_this_grade ?? undefined,
      census_finer: assessment.census_finer ?? undefined,
      census_date: assessment.census_date || '',
      confidence: assessment.confidence,
      notes: assessment.notes || '',
      is_primary: assessment.is_primary,
    })
    setDialogOpen(true)
  }

  const onSubmit = async (formData: RarityAssessmentForm) => {
    try {
      const assessmentData: RarityAssessmentCreateInput = {
        rarity_code: formData.rarity_code,
        rarity_system: formData.rarity_system,
        source_type: formData.source_type,
        source_name: formData.source_name || undefined,
        source_url: formData.source_url || undefined,
        source_date: formData.source_date || undefined,
        grade_range_low: formData.grade_range_low || undefined,
        grade_range_high: formData.grade_range_high || undefined,
        grade_conditional_notes: formData.grade_conditional_notes || undefined,
        census_total: formData.census_total || undefined,
        census_this_grade: formData.census_this_grade || undefined,
        census_finer: formData.census_finer || undefined,
        census_date: formData.census_date || undefined,
        confidence: formData.confidence,
        notes: formData.notes || undefined,
        is_primary: formData.is_primary,
      }

      if (editingAssessment) {
        await updateMutation.mutateAsync({
          assessmentId: editingAssessment.id,
          assessment: assessmentData,
        })
        toast.success('Rarity assessment updated')
      } else {
        await createMutation.mutateAsync(assessmentData)
        toast.success('Rarity assessment added')
      }
      setDialogOpen(false)
    } catch (e) {
      console.error(e)
      toast.error('Failed to save rarity assessment')
    }
  }

  const handleDeleteClick = (assessmentId: number) => {
    setAssessmentToDelete(assessmentId)
    setDeleteConfirmOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (assessmentToDelete === null) return
    try {
      await deleteMutation.mutateAsync(assessmentToDelete)
      toast.success('Assessment deleted')
    } catch (e) {
      toast.error('Failed to delete assessment')
    } finally {
      setDeleteConfirmOpen(false)
      setAssessmentToDelete(null)
    }
  }

  const handleSetPrimary = async (assessmentId: number) => {
    try {
      await setPrimaryMutation.mutateAsync(assessmentId)
      toast.success('Primary assessment updated')
    } catch (e) {
      toast.error('Failed to set primary assessment')
    }
  }

  const assessments = data?.assessments ?? []
  const primaryAssessment = assessments.find((a) => a.is_primary)

  const getRarityColor = (code: string) => {
    const upperCode = code.toUpperCase()
    return RARITY_COLORS[upperCode] || 'bg-gray-500'
  }

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
                  <CardTitle className="text-sm font-medium">Rarity Assessments</CardTitle>
                  <Badge variant="secondary" className="text-xs">
                    {assessments.length}
                  </Badge>
                </div>
                {primaryAssessment && (
                  <Badge className={`${getRarityColor(primaryAssessment.rarity_code)} text-white text-xs`}>
                    {primaryAssessment.rarity_code}
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
                <div className="text-sm text-destructive py-4">
                  Failed to load rarity assessments
                </div>
              ) : assessments.length === 0 ? (
                <div className="text-sm text-muted-foreground py-4">
                  No rarity assessments recorded.
                </div>
              ) : (
                <div className="space-y-2">
                  {assessments.map((assessment) => {
                    const sourceConfig =
                      SOURCE_TYPE_CONFIG[assessment.source_type as keyof typeof SOURCE_TYPE_CONFIG]
                    const Icon = sourceConfig?.icon ?? BookOpen

                    return (
                      <div
                        key={assessment.id}
                        className={`flex items-start gap-3 p-3 rounded-lg border ${
                          assessment.is_primary ? 'border-primary bg-primary/5' : 'border-border'
                        }`}
                      >
                        <div className="flex flex-col items-center gap-1">
                          <Badge
                            className={`${getRarityColor(assessment.rarity_code)} text-white font-bold`}
                          >
                            {assessment.rarity_code}
                          </Badge>
                          <div
                            className={`p-1 rounded-full ${sourceConfig?.color ?? 'bg-gray-500'} text-white`}
                          >
                            <Icon className="h-3 w-3" />
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium text-sm">
                              {sourceConfig?.label ?? assessment.source_type}
                            </span>
                            {assessment.is_primary && (
                              <Badge variant="default" className="text-xs">
                                Primary
                              </Badge>
                            )}
                            <Badge variant="outline" className="text-xs">
                              {assessment.confidence}
                            </Badge>
                          </div>
                          {assessment.source_name && (
                            <div className="text-sm text-muted-foreground mt-1">
                              {assessment.source_name}
                            </div>
                          )}
                          {assessment.grade_conditional_notes && (
                            <div className="text-xs text-muted-foreground mt-1 italic">
                              {assessment.grade_conditional_notes}
                            </div>
                          )}
                          {(assessment.census_total || assessment.census_this_grade) && (
                            <div className="text-xs text-muted-foreground mt-1">
                              Census: {assessment.census_this_grade ?? '?'} at grade
                              {assessment.census_total && ` / ${assessment.census_total} total`}
                              {assessment.census_finer && ` (${assessment.census_finer} finer)`}
                            </div>
                          )}
                          {assessment.notes && (
                            <div className="text-xs text-muted-foreground mt-1 italic">
                              {assessment.notes}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          {!assessment.is_primary && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              onClick={() => handleSetPrimary(assessment.id)}
                              title="Set as primary"
                            >
                              <StarOff className="h-3 w-3" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7"
                            onClick={() => openEditDialog(assessment)}
                            title="Edit"
                          >
                            <Pencil className="h-3 w-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 text-destructive"
                            onClick={() => handleDeleteClick(assessment.id)}
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

              <Button variant="outline" size="sm" className="mt-3 w-full" onClick={openAddDialog}>
                <Plus className="h-4 w-4 mr-1" />
                Add Rarity Assessment
              </Button>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>

        {/* Add/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingAssessment ? 'Edit Rarity Assessment' : 'Add Rarity Assessment'}
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-2">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Rarity Code</Label>
                  <Input
                    {...register('rarity_code')}
                    placeholder="C, S, R1-R5, RR, RRR, UNIQUE"
                    className="uppercase"
                  />
                  {errors.rarity_code && (
                    <p className="text-xs text-destructive">{errors.rarity_code.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label>Rarity System</Label>
                  <Select
                    onValueChange={(val) => setValue('rarity_system', val)}
                    value={raritySystem}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {RARITY_SYSTEMS.map((system) => (
                        <SelectItem key={system.value} value={system.value}>
                          {system.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.rarity_system && (
                    <p className="text-xs text-destructive">{errors.rarity_system.message}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Source Type</Label>
                  <Select
                    onValueChange={(val) => setValue('source_type', val)}
                    value={sourceType}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="catalog">Catalog</SelectItem>
                      <SelectItem value="census_data">Census Data</SelectItem>
                      <SelectItem value="auction_analysis">Auction Analysis</SelectItem>
                      <SelectItem value="expert_opinion">Expert Opinion</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.source_type && (
                    <p className="text-xs text-destructive">{errors.source_type.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label>Confidence</Label>
                  <Select
                    onValueChange={(val) => setValue('confidence', val)}
                    value={confidence}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CONFIDENCE_LEVELS.map((level) => (
                        <SelectItem key={level.value} value={level.value}>
                          {level.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Source Name</Label>
                  <Input
                    {...register('source_name')}
                    placeholder="e.g., RIC II.1, NGC Census"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Source Date</Label>
                  <Input type="date" {...register('source_date')} />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Source URL</Label>
                <Input {...register('source_url')} placeholder="Link to source" />
              </div>

              {/* Grade-conditional section */}
              <div className="border rounded-lg p-3 space-y-3">
                <Label className="text-sm font-medium">Grade-Conditional Rarity</Label>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-xs">Grade Range Low</Label>
                    <Input {...register('grade_range_low')} placeholder="e.g., VF" />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs">Grade Range High</Label>
                    <Input {...register('grade_range_high')} placeholder="e.g., MS" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Grade Conditional Notes</Label>
                  <Input
                    {...register('grade_conditional_notes')}
                    placeholder="e.g., R3 in XF+, R5 in MS"
                  />
                </div>
              </div>

              {/* Census data section */}
              {(sourceType === 'census_data' || sourceType === 'census') && (
                <div className="border rounded-lg p-3 space-y-3">
                  <Label className="text-sm font-medium">Census Data</Label>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label className="text-xs">Total Graded</Label>
                      <Input type="number" {...register('census_total')} min={0} />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs">At This Grade</Label>
                      <Input type="number" {...register('census_this_grade')} min={0} />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs">Finer</Label>
                      <Input type="number" {...register('census_finer')} min={0} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs">Census Date</Label>
                    <Input type="date" {...register('census_date')} />
                  </div>
                </div>
              )}

              <div className="flex items-center gap-2">
                <Checkbox
                  id="is_primary"
                  checked={watch('is_primary')}
                  onCheckedChange={(checked) => setValue('is_primary', !!checked)}
                />
                <Label htmlFor="is_primary" className="text-sm">
                  Primary Assessment
                </Label>
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  {...register('notes')}
                  placeholder="Additional notes about this rarity assessment"
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
                    : editingAssessment
                    ? 'Save Changes'
                    : 'Add Assessment'}
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
            <AlertDialogTitle>Delete Rarity Assessment</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this rarity assessment? This action cannot be undone.
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
