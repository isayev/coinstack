import { useNavigate } from "react-router-dom";
import { useCreateCoin } from "@/hooks/useCoins";
import { CoinForm } from "@/components/coins/CoinForm";
import { CoinCreate } from "@/types/coin";
import { toast } from "sonner";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export function AddCoinPage() {
  const navigate = useNavigate();
  const createMutation = useCreateCoin();

  const handleSubmit = (data: CoinCreate) => {
    createMutation.mutate(data, {
      onSuccess: (coin) => {
        toast.success("Coin added successfully");
        navigate(`/coins/${coin.id}`);
      },
      onError: (error) => {
        toast.error("Failed to add coin");
        console.error(error);
      },
    });
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Add New Coin</h1>
          <p className="text-muted-foreground">Enter the details of your coin</p>
        </div>
      </div>

      <CoinForm onSubmit={handleSubmit} isSubmitting={createMutation.isPending} />
    </div>
  );
}
