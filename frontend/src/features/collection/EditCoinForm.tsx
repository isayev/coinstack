import { Coin } from "@/domain/schemas"

interface EditCoinFormProps {
  coin: Coin
  onSubmit: (data: any) => void
  isSubmitting: boolean
}

export function EditCoinForm({ coin: _coin, onSubmit: _onSubmit, isSubmitting: _isSubmitting }: EditCoinFormProps) {
  // This component seems unused or a placeholder
  return null 
}