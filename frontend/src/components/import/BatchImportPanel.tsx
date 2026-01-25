/**
 * BatchImportPanel - Import multiple coins from URL list.
 * 
 * Features:
 * - Textarea for pasting multiple URLs
 * - Progress indicator during batch fetch
 * - Grid preview of all results
 * - Select coins to import
 * - Batch import action
 */
import { useState, useMemo } from "react";
import {
  Link,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Trash2,
  ExternalLink,
  Eye,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import {
  useBatchUrlImport,
  BatchPreviewItem,
  ImportPreviewResponse,
  SOURCE_CONFIG,
} from "@/hooks/useImport";
import { cn } from "@/lib/utils";

interface BatchImportPanelProps {
  onSelectItem: (preview: ImportPreviewResponse) => void;
  onBatchImport?: (items: BatchPreviewItem[]) => void;
}

export function BatchImportPanel({
  onSelectItem,
  onBatchImport,
}: BatchImportPanelProps) {
  const [urlText, setUrlText] = useState("");
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  
  const { mutate: fetchBatch, isPending, data, reset } = useBatchUrlImport();
  
  // Parse URLs from textarea
  const urls = useMemo(() => {
    return urlText
      .split(/[\n,]+/)
      .map((url) => url.trim())
      .filter((url) => url.startsWith("http://") || url.startsWith("https://"));
  }, [urlText]);
  
  const handleFetch = () => {
    if (urls.length > 0) {
      fetchBatch(urls);
    }
  };
  
  const handleToggleItem = (url: string) => {
    setSelectedItems((prev) => {
      const next = new Set(prev);
      if (next.has(url)) {
        next.delete(url);
      } else {
        next.add(url);
      }
      return next;
    });
  };
  
  const handleSelectAllSuccessful = () => {
    if (data?.items) {
      const successful = data.items
        .filter((item: any) => item.success && !item.preview?.similar_coins?.length)
        .map((item: any) => item.url);
      setSelectedItems(new Set(successful));
    }
  };
  
  const handleReset = () => {
    reset();
    setSelectedItems(new Set());
  };
  
  const successfulItems = data?.items.filter((item: any) => item.success) || [];
  const failedItems = data?.items.filter((item: any) => !item.success) || [];
  const duplicateItems = data?.items.filter(
    (item: any) => item.success && (item.preview?.similar_coins?.length ?? 0) > 0
  ) || [];
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Link className="h-5 w-5" />
          Batch Import from URLs
        </CardTitle>
        <CardDescription>
          Paste multiple auction URLs (one per line) to import several coins at once
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!data ? (
          <>
            {/* URL textarea */}
            <Textarea
              placeholder={`Paste URLs here, one per line:\nhttps://coins.ha.com/itm/...\nhttps://cngcoins.com/coin/...\nhttps://www.ebay.com/itm/...`}
              value={urlText}
              onChange={(e) => setUrlText(e.target.value)}
              rows={6}
              className="font-mono text-sm"
            />
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                {urls.length} URL{urls.length !== 1 ? "s" : ""} detected
                {urls.length > 10 && " (max 10 will be processed)"}
              </span>
              <Button
                onClick={handleFetch}
                disabled={urls.length === 0 || isPending}
              >
                {isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Fetching...
                  </>
                ) : (
                  <>Fetch All ({Math.min(urls.length, 10)})</>
                )}
              </Button>
            </div>
            
            {/* Loading progress */}
            {isPending && (
              <div className="space-y-2">
                <Progress value={undefined} className="h-2" />
                <p className="text-sm text-center text-muted-foreground">
                  Fetching {Math.min(urls.length, 10)} URLs...
                  <br />
                  <span className="text-xs">This may take a minute due to rate limiting</span>
                </p>
              </div>
            )}
          </>
        ) : (
          <>
            {/* Results summary */}
            <div className="flex items-center gap-4">
              <Badge variant="outline" className="gap-1 text-green-600 bg-green-500/10 border-green-500/30">
                <CheckCircle2 className="h-3 w-3" />
                {successfulItems.length} successful
              </Badge>
              {duplicateItems.length > 0 && (
                <Badge variant="outline" className="gap-1 text-yellow-600 bg-yellow-500/10 border-yellow-500/30">
                  <AlertTriangle className="h-3 w-3" />
                  {duplicateItems.length} possible duplicates
                </Badge>
              )}
              {failedItems.length > 0 && (
                <Badge variant="outline" className="gap-1 text-red-500 bg-red-500/10 border-red-500/30">
                  <XCircle className="h-3 w-3" />
                  {failedItems.length} failed
                </Badge>
              )}
            </div>
            
            {/* Selection actions */}
            {successfulItems.length > 0 && (
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSelectAllSuccessful}
                >
                  Select All ({successfulItems.length - duplicateItems.length})
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedItems(new Set())}
                >
                  Clear Selection
                </Button>
                <span className="text-sm text-muted-foreground ml-auto">
                  {selectedItems.size} selected
                </span>
              </div>
            )}
            
            {/* Results grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[400px] overflow-y-auto">
              {data.items.map((item: any) => {
                const sourceConfig = item.source_type
                  ? SOURCE_CONFIG[item.source_type]
                  : null;
                const hasDuplicates = (item.preview?.similar_coins?.length ?? 0) > 0;
                
                return (
                  <div
                    key={item.url}
                    className={cn(
                      "border rounded-lg p-3 flex gap-3",
                      item.success && "hover:border-primary/50",
                      !item.success && "opacity-60 bg-muted/50",
                      selectedItems.has(item.url) && "border-primary ring-1 ring-primary"
                    )}
                  >
                    {/* Checkbox */}
                    {item.success && (
                      <Checkbox
                        checked={selectedItems.has(item.url)}
                        onCheckedChange={() => handleToggleItem(item.url)}
                        className="mt-1"
                      />
                    )}
                    
                    {/* Thumbnail */}
                    {item.thumbnail ? (
                      <img
                        src={item.thumbnail}
                        alt=""
                        className="w-14 h-14 rounded object-cover bg-muted shrink-0"
                      />
                    ) : (
                      <div className="w-14 h-14 rounded bg-muted flex items-center justify-center shrink-0">
                        {item.success ? (
                          <span className="text-2xl">🪙</span>
                        ) : (
                          <XCircle className="h-6 w-6 text-muted-foreground" />
                        )}
                      </div>
                    )}
                    
                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      {item.success ? (
                        <>
                          <p className="font-medium text-sm truncate">
                            {item.title || "Untitled"}
                          </p>
                          <div className="flex items-center gap-1.5 mt-1">
                            {sourceConfig && (
                              <Badge
                                variant="outline"
                                className={cn(
                                  "text-xs py-0",
                                  sourceConfig.color,
                                  sourceConfig.bgColor,
                                  sourceConfig.borderColor
                                )}
                              >
                                {sourceConfig.label}
                              </Badge>
                            )}
                            {hasDuplicates && (
                              <Badge
                                variant="outline"
                                className="text-xs py-0 text-yellow-600 bg-yellow-500/10 border-yellow-500/30"
                              >
                                Duplicate?
                              </Badge>
                            )}
                          </div>
                        </>
                      ) : (
                        <>
                          <p className="text-sm text-destructive font-medium">
                            Failed
                          </p>
                          <p className="text-xs text-muted-foreground truncate">
                            {item.error}
                          </p>
                        </>
                      )}
                      
                      {/* Actions */}
                      <div className="flex items-center gap-1 mt-2">
                        {item.success && item.preview && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 text-xs px-2"
                            onClick={() => onSelectItem(item.preview!)}
                          >
                            <Eye className="h-3 w-3 mr-1" />
                            Preview
                          </Button>
                        )}
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center h-6 px-2 text-xs text-muted-foreground hover:text-foreground"
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            
            {/* Actions */}
            <div className="flex gap-2 pt-2 border-t">
              <Button variant="outline" onClick={handleReset}>
                <Trash2 className="h-4 w-4 mr-2" />
                Start Over
              </Button>
              {selectedItems.size > 0 && onBatchImport && (
                <Button
                  onClick={() => {
                    const selected = data.items.filter((item: any) =>
                      selectedItems.has(item.url) && item.success
                    );
                    onBatchImport(selected);
                  }}
                  className="ml-auto"
                >
                  Import {selectedItems.size} Coin{selectedItems.size > 1 ? "s" : ""}
                </Button>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
