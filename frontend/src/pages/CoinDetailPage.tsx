import { useParams, useNavigate } from "react-router-dom";
import { useCoin, useDeleteCoin } from "@/hooks/useCoins";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  ArrowLeft, Edit, Trash2, ExternalLink, 
  Scale, Ruler, CircleDot, Calendar 
} from "lucide-react";

export function CoinDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: coin, isLoading } = useCoin(Number(id));
  const deleteMutation = useDeleteCoin();
  
  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div>Loading...</div>
      </div>
    );
  }
  
  if (!coin) {
    return (
      <div className="container mx-auto p-6">
        <div>Coin not found</div>
      </div>
    );
  }
  
  const handleDelete = () => {
    if (confirm("Delete this coin? This cannot be undone.")) {
      deleteMutation.mutate(coin.id, {
        onSuccess: () => navigate("/")
      });
    }
  };
  
  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{coin.issuing_authority}</h1>
            <p className="text-muted-foreground">
              {coin.denomination} • {coin.mint_name || "Unknown mint"}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => navigate(`/coins/${id}/edit`)}>
            <Edit className="w-4 h-4 mr-2" />
            Edit
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            <Trash2 className="w-4 h-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <div className="aspect-square bg-muted rounded-lg flex items-center justify-center">
            {coin.images && coin.images.length > 0 ? (
              <img 
                src={`/api${coin.images[0].file_path}`}
                alt={coin.issuing_authority}
                className="rounded-lg"
              />
            ) : (
              <div className="text-muted-foreground">No Image</div>
            )}
          </div>
        </div>
        
        <div>
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="text-center p-3 bg-muted rounded-lg">
              <Scale className="w-5 h-5 mx-auto mb-1 text-muted-foreground" />
              <div className="font-semibold">{coin.weight_g || "—"}g</div>
              <div className="text-xs text-muted-foreground">Weight</div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <Ruler className="w-5 h-5 mx-auto mb-1 text-muted-foreground" />
              <div className="font-semibold">{coin.diameter_mm || "—"}mm</div>
              <div className="text-xs text-muted-foreground">Diameter</div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <CircleDot className="w-5 h-5 mx-auto mb-1 text-muted-foreground" />
              <div className="font-semibold">{coin.die_axis || "—"}h</div>
              <div className="text-xs text-muted-foreground">Die Axis</div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <Calendar className="w-5 h-5 mx-auto mb-1 text-muted-foreground" />
              <div className="font-semibold">
                {coin.mint_year_start && coin.mint_year_end 
                  ? `${coin.mint_year_start}-${coin.mint_year_end}`
                  : coin.mint_year_start || "—"
                }
              </div>
              <div className="text-xs text-muted-foreground">Minted</div>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-2 mb-6">
            <Badge variant="outline">{coin.category}</Badge>
            <Badge variant="outline">{coin.metal}</Badge>
            {coin.grade && <Badge>{coin.grade}</Badge>}
            {coin.rarity && <Badge variant="secondary">{coin.rarity}</Badge>}
          </div>
          
          <Tabs defaultValue="design" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="design">Design</TabsTrigger>
              <TabsTrigger value="references">References</TabsTrigger>
              <TabsTrigger value="provenance">Provenance</TabsTrigger>
              <TabsTrigger value="notes">Notes</TabsTrigger>
            </TabsList>
            
            <TabsContent value="design" className="space-y-4 mt-4">
              <div>
                <h3 className="font-semibold mb-2">Obverse</h3>
                {coin.obverse_legend && (
                  <div className="mb-2 font-mono text-sm">{coin.obverse_legend}</div>
                )}
                <p className="text-sm text-muted-foreground">
                  {coin.obverse_description || "No description"}
                </p>
              </div>
              
              <div>
                <h3 className="font-semibold mb-2">Reverse</h3>
                {coin.reverse_legend && (
                  <div className="mb-2 font-mono text-sm">{coin.reverse_legend}</div>
                )}
                <p className="text-sm text-muted-foreground">
                  {coin.reverse_description || "No description"}
                </p>
                {coin.exergue && (
                  <p className="text-sm mt-1">
                    <span className="text-muted-foreground">Exergue:</span> {coin.exergue}
                  </p>
                )}
              </div>
            </TabsContent>
            
            <TabsContent value="references" className="mt-4">
              {coin.references && coin.references.length > 0 ? (
                <div className="space-y-2">
                  {coin.references.map((ref) => (
                    <div key={ref.id} className="flex items-center gap-2">
                      <Badge variant={ref.is_primary ? "default" : "outline"}>
                        {ref.system.toUpperCase()}
                      </Badge>
                      <span>
                        {ref.volume && `${ref.volume} `}
                        {ref.number}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No references</p>
              )}
            </TabsContent>
            
            <TabsContent value="provenance" className="mt-4">
              {coin.acquisition_url && (
                <Button variant="link" className="p-0" asChild>
                  <a href={coin.acquisition_url} target="_blank" rel="noopener">
                    View Original Listing
                    <ExternalLink className="w-4 h-4 ml-1" />
                  </a>
                </Button>
              )}
            </TabsContent>
            
            <TabsContent value="notes" className="mt-4 space-y-4">
              {coin.historical_significance && (
                <div>
                  <h3 className="font-semibold mb-1">Historical Significance</h3>
                  <p className="text-sm text-muted-foreground">{coin.historical_significance}</p>
                </div>
              )}
              {coin.personal_notes && (
                <div>
                  <h3 className="font-semibold mb-1">Personal Notes</h3>
                  <p className="text-sm text-muted-foreground">{coin.personal_notes}</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
