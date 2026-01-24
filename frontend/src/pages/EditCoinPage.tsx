import { useNavigate, useParams } from "react-router-dom";
import { useCoin, useUpdateCoin } from "@/hooks/useCoins";
import { CoinForm } from "@/components/coins/CoinForm";
import { CoinCreate } from "@/types/coin";
import { toast } from "sonner";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export function EditCoinPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: coin, isLoading } = useCoin(Number(id));
  const updateMutation = useUpdateCoin();

  const handleSubmit = (data: CoinCreate) => {
    updateMutation.mutate(
      { id: Number(id), data },
      {
        onSuccess: () => {
          toast.success("Coin updated successfully");
          navigate(`/coins/${id}`);
        },
        onError: (error) => {
          toast.error("Failed to update coin");
          console.error(error);
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading coin...</div>
        </div>
      </div>
    );
  }

  if (!coin) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-destructive">Coin not found</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Edit Coin</h1>
          <p className="text-muted-foreground">
            {coin.issuing_authority} - {coin.denomination}
          </p>
        </div>
      </div>

      <CoinForm coin={coin} onSubmit={handleSubmit} isSubmitting={updateMutation.isPending} />
    </div>
  );
}
