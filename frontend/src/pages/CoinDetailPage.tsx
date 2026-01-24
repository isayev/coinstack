import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useCoin, useDeleteCoin, useCoinNavigation } from "@/hooks/useCoins";
import { useEnrichCoin, useLookupReference } from "@/hooks/useCatalog";
import { useExpandLegend } from "@/hooks/useLegend";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ImageGallery } from "@/components/coins/ImageZoom";
import { ImageManager } from "@/components/coins/ImageManager";
import { 
  ArrowLeft, Edit, Trash2, ExternalLink, 
  Scale, Ruler, CircleDot, Calendar,
  RefreshCw, Sparkles, Loader2, CheckCircle, XCircle, AlertCircle,
  ChevronLeft, ChevronRight, Home, Coins, Gavel, Image as ImageIcon
} from "lucide-react";
import { cn } from "@/lib/utils";
import { CoinDetail } from "@/types/coin";
import { ScrapeDialog } from "@/components/auctions/ScrapeDialog";

export function CoinDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const coinId = Number(id);
  const { data: coin, isLoading, refetch } = useCoin(coinId);
  const { data: navigation } = useCoinNavigation(coinId);
  const deleteMutation = useDeleteCoin();
  
  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle if not in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      
      if (e.key === "ArrowLeft" && navigation?.prev_id) {
        navigate(`/coins/${navigation.prev_id}`);
      } else if (e.key === "ArrowRight" && navigation?.next_id) {
        navigate(`/coins/${navigation.next_id}`);
      } else if (e.key === "Escape") {
        navigate("/");
      }
    };
    
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [navigation, navigate]);
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-muted-foreground">Loading coin details...</span>
        </div>
      </div>
    );
  }
  
  if (!coin) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
          <Coins className="w-8 h-8 text-muted-foreground" />
        </div>
        <h2 className="text-xl font-semibold">Coin not found</h2>
        <p className="text-muted-foreground">The coin you're looking for doesn't exist or has been removed.</p>
        <Button onClick={() => navigate("/")}>
          <Home className="w-4 h-4 mr-2" />
          Back to Collection
        </Button>
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

  // Format year display
  const formatYear = (year: number | null | undefined) => {
    if (!year) return null;
    return year < 0 ? `${Math.abs(year)} BCE` : `${year} CE`;
  };

  const yearDisplay = coin.mint_year_start && coin.mint_year_end 
    ? `${formatYear(coin.mint_year_start)} – ${formatYear(coin.mint_year_end)}`
    : formatYear(coin.mint_year_start) || "—";
  
  return (
    <div className="min-h-screen bg-background">
      {/* Sticky Header with Navigation */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            {/* Left: Back + Title */}
            <div className="flex items-center gap-3 min-w-0">
              <Button variant="ghost" size="icon" onClick={() => navigate("/")} className="shrink-0">
                <ArrowLeft className="w-5 h-5" />
              </Button>
              <div className="min-w-0">
                <h1 className="text-lg font-semibold truncate">{coin.issuing_authority}</h1>
                <p className="text-xs text-muted-foreground truncate">
                  {coin.denomination} • {coin.mint_name || "Unknown mint"}
                </p>
              </div>
            </div>
            
            {/* Center: Navigation */}
            <div className="hidden sm:flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                disabled={!navigation?.prev_id}
                onClick={() => navigation?.prev_id && navigate(`/coins/${navigation.prev_id}`)}
                className="gap-1"
              >
                <ChevronLeft className="w-4 h-4" />
                <span className="hidden md:inline">Previous</span>
              </Button>
              
              {navigation && navigation.current_index && (
                <div className="px-3 py-1 text-sm text-muted-foreground tabular-nums">
                  {navigation.current_index} / {navigation.total}
                </div>
              )}
              
              <Button
                variant="ghost"
                size="sm"
                disabled={!navigation?.next_id}
                onClick={() => navigation?.next_id && navigate(`/coins/${navigation.next_id}`)}
                className="gap-1"
              >
                <span className="hidden md:inline">Next</span>
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
            
            {/* Right: Actions */}
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => navigate(`/coins/${id}/edit`)}>
                <Edit className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">Edit</span>
              </Button>
              <Button variant="ghost" size="sm" onClick={handleDelete} className="text-destructive hover:text-destructive">
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Mobile Navigation Bar */}
      <div className="sm:hidden sticky top-14 z-10 bg-muted/50 backdrop-blur border-b">
        <div className="flex items-center justify-between px-4 py-2">
          <Button
            variant="ghost"
            size="sm"
            disabled={!navigation?.prev_id}
            onClick={() => navigation?.prev_id && navigate(`/coins/${navigation.prev_id}`)}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Prev
          </Button>
          
          {navigation && navigation.current_index && (
            <span className="text-sm text-muted-foreground tabular-nums">
              {navigation.current_index} of {navigation.total}
            </span>
          )}
          
          <Button
            variant="ghost"
            size="sm"
            disabled={!navigation?.next_id}
            onClick={() => navigation?.next_id && navigate(`/coins/${navigation.next_id}`)}
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="max-w-6xl mx-auto p-4 sm:p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
          {/* Image Section */}
          <div className="space-y-4">
            {coin.images && coin.images.length > 0 ? (
              <ImageGallery
                images={coin.images.map((img) => ({
                  src: `/api${img.file_path}`,
                  alt: `${coin.issuing_authority} - ${img.image_type}`,
                  isPrimary: img.is_primary,
                }))}
              />
            ) : (
              <div className="aspect-square bg-muted rounded-xl flex flex-col items-center justify-center gap-2 text-muted-foreground">
                <Coins className="w-12 h-12" />
                <span>No Image</span>
              </div>
            )}
            
            {/* Quick Stats - Mobile */}
            <div className="lg:hidden grid grid-cols-4 gap-2">
              <QuickStat icon={Scale} value={coin.weight_g ? `${coin.weight_g}g` : "—"} label="Weight" />
              <QuickStat icon={Ruler} value={coin.diameter_mm ? `${coin.diameter_mm}mm` : "—"} label="Diameter" />
              <QuickStat icon={CircleDot} value={coin.die_axis ? `${coin.die_axis}h` : "—"} label="Die Axis" />
              <QuickStat icon={Calendar} value={yearDisplay} label="Minted" small />
            </div>
          </div>
          
          {/* Details Section */}
          <div className="space-y-6">
            {/* Quick Stats - Desktop */}
            <div className="hidden lg:grid grid-cols-4 gap-3">
              <QuickStat icon={Scale} value={coin.weight_g ? `${coin.weight_g}g` : "—"} label="Weight" />
              <QuickStat icon={Ruler} value={coin.diameter_mm ? `${coin.diameter_mm}mm` : "—"} label="Diameter" />
              <QuickStat icon={CircleDot} value={coin.die_axis ? `${coin.die_axis}h` : "—"} label="Die Axis" />
              <QuickStat icon={Calendar} value={yearDisplay} label="Minted" small />
            </div>
            
            {/* Badges */}
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className="capitalize">{coin.category}</Badge>
              {coin.sub_category && (
                <Badge variant="outline" className="capitalize">{coin.sub_category}</Badge>
              )}
              <Badge variant="outline" className="capitalize">{coin.metal}</Badge>
              {coin.grade && <Badge>{coin.grade}</Badge>}
              {coin.is_circa && (
                <Badge variant="secondary" className="text-xs">circa</Badge>
              )}
              {coin.is_test_cut && (
                <Badge variant="destructive" className="text-xs">Test Cut</Badge>
              )}
              {coin.rarity && <Badge variant="secondary" className="capitalize">{coin.rarity.replace("_", " ")}</Badge>}
              {coin.acquisition_price && (
                <Badge variant="secondary" className="bg-green-500/10 text-green-600 border-green-500/20">
                  ${Number(coin.acquisition_price).toLocaleString()}
                </Badge>
              )}
              {coin.estimated_value_usd && (
                <Badge variant="secondary" className="bg-blue-500/10 text-blue-600 border-blue-500/20">
                  Est. ${Number(coin.estimated_value_usd).toLocaleString()}
                </Badge>
              )}
            </div>
            
            {/* Tabs */}
            <Tabs defaultValue="design" className="w-full">
              <TabsList className="grid w-full grid-cols-5 h-10">
                <TabsTrigger value="design" className="text-sm">Design</TabsTrigger>
                <TabsTrigger value="images" className="text-sm">
                  <ImageIcon className="w-3 h-3 mr-1" />
                  Images
                </TabsTrigger>
                <TabsTrigger value="references" className="text-sm">References</TabsTrigger>
                <TabsTrigger value="provenance" className="text-sm">Provenance</TabsTrigger>
                <TabsTrigger value="notes" className="text-sm">Notes</TabsTrigger>
              </TabsList>
              
              <TabsContent value="design" className="space-y-6 mt-6">
                <DesignSection 
                  title="Obverse" 
                  legend={coin.obverse_legend}
                  legendExpanded={coin.obverse_legend_expanded}
                  description={coin.obverse_description}
                />
                <DesignSection 
                  title="Reverse" 
                  legend={coin.reverse_legend}
                  legendExpanded={coin.reverse_legend_expanded}
                  description={coin.reverse_description}
                  exergue={coin.exergue}
                />
              </TabsContent>
              
              <TabsContent value="images" className="mt-6">
                <ImageManager
                  coinId={coin.id}
                  auctionData={coin.auction_data || []}
                  existingImages={coin.images || []}
                  onImagesUpdated={() => refetch()}
                />
              </TabsContent>
              
              <TabsContent value="references" className="mt-6">
                <CatalogReferences coin={coin} />
              </TabsContent>
              
              <TabsContent value="provenance" className="mt-6 space-y-6">
                <ProvenanceSection coin={coin} />
                <AuctionDataSection 
                  auctionData={coin.auction_data} 
                  coinId={coin.id}
                />
              </TabsContent>
              
              <TabsContent value="notes" className="mt-6 space-y-4">
                {coin.historical_significance && (
                  <div className="space-y-2">
                    <h3 className="font-medium">Historical Significance</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">{coin.historical_significance}</p>
                  </div>
                )}
                {coin.personal_notes && (
                  <div className="space-y-2">
                    <h3 className="font-medium">Personal Notes</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">{coin.personal_notes}</p>
                  </div>
                )}
                {!coin.historical_significance && !coin.personal_notes && (
                  <p className="text-sm text-muted-foreground">No notes added yet.</p>
                )}
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
      
      {/* Fixed Bottom Navigation - Mobile */}
      <div className="fixed bottom-0 left-0 right-0 sm:hidden bg-background border-t p-2 safe-area-inset-bottom">
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            className="flex-1"
            disabled={!navigation?.prev_id}
            onClick={() => navigation?.prev_id && navigate(`/coins/${navigation.prev_id}`)}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </Button>
          <Button 
            variant="outline"
            className="flex-1"
            disabled={!navigation?.next_id}
            onClick={() => navigation?.next_id && navigate(`/coins/${navigation.next_id}`)}
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </div>
    </div>
  );
}

// Quick stat component
function QuickStat({ 
  icon: Icon, 
  value, 
  label, 
  small = false 
}: { 
  icon: React.ElementType; 
  value: string; 
  label: string;
  small?: boolean;
}) {
  return (
    <div className="text-center p-3 bg-muted/50 rounded-lg">
      <Icon className="w-4 h-4 mx-auto mb-1 text-muted-foreground" />
      <div className={cn("font-semibold truncate", small && "text-sm")}>{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

// Design section component with legend expansion
function DesignSection({ 
  title, 
  legend,
  legendExpanded, 
  description, 
  exergue 
}: { 
  title: string; 
  legend?: string | null;
  legendExpanded?: string | null;
  description?: string | null;
  exergue?: string | null;
}) {
  const [showExpansion, setShowExpansion] = useState(false);
  const [localExpansion, setLocalExpansion] = useState<string | null>(null);
  const expandMutation = useExpandLegend();
  
  const handleExpand = async () => {
    if (!legend) return;
    
    try {
      const result = await expandMutation.mutateAsync({
        legend,
        use_llm_fallback: true,
      });
      setLocalExpansion(result.expanded);
      setShowExpansion(true);
    } catch (error) {
      console.error("Failed to expand legend:", error);
    }
  };
  
  const displayedExpansion = legendExpanded || localExpansion;
  
  return (
    <div className="space-y-2">
      <h3 className="font-medium">{title}</h3>
      {legend && (
        <div className="space-y-1">
          <div className="px-3 py-2 bg-muted rounded-md font-mono text-sm tracking-wide flex items-center justify-between gap-2">
            <span className="break-all">{legend}</span>
            {!displayedExpansion && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleExpand}
                disabled={expandMutation.isPending}
                className="shrink-0"
              >
                {expandMutation.isPending ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Sparkles className="w-3 h-3" />
                )}
              </Button>
            )}
          </div>
          {displayedExpansion && (
            <div className="px-3 py-1.5 bg-green-500/10 rounded-md text-sm text-green-700 dark:text-green-400">
              {displayedExpansion}
            </div>
          )}
          {showExpansion && expandMutation.data && !legendExpanded && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Badge variant="outline" className="text-xs">
                {Math.round(expandMutation.data.confidence * 100)}% confidence
              </Badge>
              {expandMutation.data.unknown_terms.length > 0 && (
                <span>Unknown: {expandMutation.data.unknown_terms.join(", ")}</span>
              )}
            </div>
          )}
        </div>
      )}
      <p className="text-sm text-muted-foreground leading-relaxed">
        {description || "No description available"}
      </p>
      {exergue && (
        <p className="text-sm">
          <span className="text-muted-foreground">Exergue:</span>{" "}
          <span className="font-mono">{exergue}</span>
        </p>
      )}
    </div>
  );
}

// Provenance section component
function ProvenanceSection({ coin }: { coin: any }) {
  const hasProvenance = coin.acquisition_source || coin.acquisition_date || coin.acquisition_url;
  
  if (!hasProvenance) {
    return <p className="text-sm text-muted-foreground">No provenance information available.</p>;
  }
  
  return (
    <div className="space-y-3">
      {coin.acquisition_source && (
        <div className="flex justify-between items-center py-2 border-b">
          <span className="text-sm text-muted-foreground">Source</span>
          <span className="text-sm font-medium">{coin.acquisition_source}</span>
        </div>
      )}
      {coin.acquisition_date && (
        <div className="flex justify-between items-center py-2 border-b">
          <span className="text-sm text-muted-foreground">Acquired</span>
          <span className="text-sm font-medium">
            {new Date(coin.acquisition_date).toLocaleDateString()}
          </span>
        </div>
      )}
      {coin.acquisition_price && (
        <div className="flex justify-between items-center py-2 border-b">
          <span className="text-sm text-muted-foreground">Price</span>
          <span className="text-sm font-medium text-green-600">
            ${Number(coin.acquisition_price).toLocaleString()}
          </span>
        </div>
      )}
      {coin.storage_location && (
        <div className="flex justify-between items-center py-2 border-b">
          <span className="text-sm text-muted-foreground">Storage</span>
          <span className="text-sm font-medium">{coin.storage_location}</span>
        </div>
      )}
      {coin.acquisition_url && (
        <Button variant="outline" size="sm" className="w-full mt-2" asChild>
          <a href={coin.acquisition_url} target="_blank" rel="noopener noreferrer">
            View Original Listing
            <ExternalLink className="w-4 h-4 ml-2" />
          </a>
        </Button>
      )}
    </div>
  );
}

// Auction data section component with scrape functionality
function AuctionDataSection({ 
  auctionData, 
  coinId,
  onRefresh 
}: { 
  auctionData: CoinDetail["auction_data"]; 
  coinId: number;
  onRefresh?: () => void;
}) {
  const [scrapeDialogOpen, setScrapeDialogOpen] = useState(false);
  
  const handleScrapeComplete = () => {
    setScrapeDialogOpen(false);
    onRefresh?.();
  };
  
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-medium flex items-center gap-2">
          <Gavel className="w-4 h-4" />
          Auction History
        </h3>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => setScrapeDialogOpen(true)}
          className="gap-1"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Add Auction
        </Button>
      </div>
      
      {(!auctionData || auctionData.length === 0) ? (
        <Card>
          <CardContent className="p-6 text-center text-muted-foreground">
            <Gavel className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No auction records yet</p>
            <p className="text-sm">Click "Add Auction" to scrape an auction URL</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {auctionData.map((auction) => (
            <Card key={auction.id} className="overflow-hidden">
              <CardContent className="p-4">
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1 min-w-0">
                    <div className="font-medium truncate">
                      {auction.auction_house}
                      {auction.sale_name && ` - ${auction.sale_name}`}
                    </div>
                    {auction.lot_number && (
                      <div className="text-sm text-muted-foreground">
                        Lot {auction.lot_number}
                      </div>
                    )}
                    {auction.auction_date && (
                      <div className="text-sm text-muted-foreground">
                        {new Date(auction.auction_date).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                  
                  <div className="text-right shrink-0">
                    {auction.hammer_price && (
                      <div className="font-semibold text-green-600">
                        ${Number(auction.hammer_price).toLocaleString()}
                        {auction.total_price && auction.total_price !== auction.hammer_price && (
                          <span className="text-xs text-muted-foreground ml-1">
                            (${Number(auction.total_price).toLocaleString()} total)
                          </span>
                        )}
                      </div>
                    )}
                    {auction.estimate_low && auction.estimate_high && (
                      <div className="text-xs text-muted-foreground">
                        Est. ${Number(auction.estimate_low).toLocaleString()} - ${Number(auction.estimate_high).toLocaleString()}
                      </div>
                    )}
                    {auction.grade && (
                      <Badge variant="outline" className="mt-1 text-xs">
                        {auction.grade}
                      </Badge>
                    )}
                  </div>
                </div>
                
                {auction.url && (
                  <Button variant="ghost" size="sm" className="mt-2 -ml-2" asChild>
                    <a href={auction.url} target="_blank" rel="noopener noreferrer">
                      View Listing
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      
      <ScrapeDialog
        open={scrapeDialogOpen}
        onOpenChange={setScrapeDialogOpen}
        coinId={coinId}
        onComplete={handleScrapeComplete}
      />
    </div>
  );
}

// Status icon component
function StatusIcon({ status }: { status: string | null | undefined }) {
  switch (status) {
    case "success":
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case "not_found":
      return <XCircle className="w-4 h-4 text-red-500" />;
    case "ambiguous":
    case "deferred":
      return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    case "error":
      return <XCircle className="w-4 h-4 text-red-500" />;
    default:
      return <CircleDot className="w-4 h-4 text-muted-foreground" />;
  }
}

// Confidence badge component
function ConfidenceBadge({ confidence }: { confidence: number | null | undefined }) {
  if (!confidence) return null;
  
  const percent = Math.round(confidence * 100);
  const variant = percent >= 80 ? "default" : percent >= 50 ? "secondary" : "outline";
  
  return (
    <Badge variant={variant} className="text-xs">
      {percent}% match
    </Badge>
  );
}

// Catalog references component
function CatalogReferences({ 
  coin
}: { 
  coin: any; 
}) {
  const [refreshingRef, setRefreshingRef] = useState<number | null>(null);
  const lookupMutation = useLookupReference();
  const enrichMutation = useEnrichCoin();
  const [enrichDiff, setEnrichDiff] = useState<any>(null);
  const [showEnrichPreview, setShowEnrichPreview] = useState(false);
  
  const handleRefreshLookup = async (ref: any) => {
    setRefreshingRef(ref.id);
    try {
      const refString = ref.reference_type?.local_ref || 
        (ref.system ? `${ref.system.toUpperCase()}${ref.volume ? ` ${ref.volume}` : ''} ${ref.number}` : ref.raw_reference);
      
      await lookupMutation.mutateAsync({
        raw_reference: refString,
        context: {
          ruler: coin.issuing_authority,
          denomination: coin.denomination,
          mint: coin.mint_name,
        }
      });
    } finally {
      setRefreshingRef(null);
    }
  };
  
  const handleEnrichPreview = async () => {
    const result = await enrichMutation.mutateAsync({
      coinId: coin.id,
      dryRun: true,
    });
    setEnrichDiff(result.diff);
    setShowEnrichPreview(true);
  };
  
  const handleApplyEnrichment = async () => {
    await enrichMutation.mutateAsync({
      coinId: coin.id,
      dryRun: false,
    });
    setShowEnrichPreview(false);
    setEnrichDiff(null);
    // Refetch coin data
    window.location.reload();
  };
  
  if (!coin.references || coin.references.length === 0) {
    return (
      <div className="text-muted-foreground">
        No catalog references for this coin.
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      {/* References list */}
      <div className="space-y-3">
        {coin.references.map((ref: any) => (
          <div 
            key={ref.id} 
            className="flex items-center justify-between p-3 rounded-lg border bg-card"
          >
            <div className="flex items-center gap-3">
              <StatusIcon status={ref.reference_type?.lookup_status || ref.lookup_status} />
              
              <Badge variant={ref.is_primary ? "default" : "secondary"}>
                {(ref.reference_type?.system || ref.system || "").toUpperCase()}
              </Badge>
              
              <span className="font-medium">
                {ref.reference_type?.local_ref || 
                  (ref.volume ? `${ref.volume} ` : "") + (ref.number || ref.raw_reference || "Unknown")}
              </span>
              
              <ConfidenceBadge 
                confidence={ref.reference_type?.lookup_confidence || ref.lookup_confidence} 
              />
              
              {ref.variant_notes && (
                <span className="text-sm text-muted-foreground">
                  ({ref.variant_notes})
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              {/* External link */}
              {(ref.reference_type?.external_url || ref.external_url) && (
                <Button
                  variant="ghost"
                  size="sm"
                  asChild
                >
                  <a 
                    href={ref.reference_type?.external_url || ref.external_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </Button>
              )}
              
              {/* Refresh lookup button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleRefreshLookup(ref)}
                disabled={refreshingRef === ref.id}
              >
                {refreshingRef === ref.id ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        ))}
      </div>
      
      {/* Enrich button */}
      <div className="pt-4 border-t">
        <Button 
          onClick={handleEnrichPreview}
          disabled={enrichMutation.isPending}
          className="w-full"
        >
          {enrichMutation.isPending ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Sparkles className="w-4 h-4 mr-2" />
          )}
          Enrich from Catalogs
        </Button>
      </div>
      
      {/* Enrichment preview */}
      {showEnrichPreview && enrichDiff && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle className="text-lg">Enrichment Preview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {enrichDiff.fill_count > 0 && (
              <div>
                <h4 className="font-medium text-green-600 mb-2">
                  Fields to fill ({enrichDiff.fill_count})
                </h4>
                <div className="space-y-1">
                  {Object.entries(enrichDiff.fills).map(([field, value]) => (
                    <div key={field} className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{field}:</span>
                      <span className="text-green-600">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {enrichDiff.conflict_count > 0 && (
              <div>
                <h4 className="font-medium text-yellow-600 mb-2">
                  Conflicts ({enrichDiff.conflict_count})
                </h4>
                <div className="space-y-2">
                  {Object.entries(enrichDiff.conflicts).map(([field, conflict]: [string, any]) => (
                    <div key={field} className="text-sm p-2 rounded bg-yellow-50 dark:bg-yellow-950">
                      <div className="font-medium">{field}</div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Current: {String(conflict.current)}</span>
                        <span className="text-yellow-600">Catalog: {String(conflict.catalog)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {!enrichDiff.has_changes && (
              <p className="text-muted-foreground">
                No changes to apply. Your data matches the catalog.
              </p>
            )}
            
            <div className="flex gap-2 pt-2">
              <Button
                variant="outline"
                onClick={() => setShowEnrichPreview(false)}
              >
                Cancel
              </Button>
              {enrichDiff.fill_count > 0 && (
                <Button onClick={handleApplyEnrichment}>
                  Apply {enrichDiff.fill_count} fills
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
