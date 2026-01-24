import { useState, useRef, useCallback } from "react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ZoomIn, ZoomOut, RotateCw, X, Maximize2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ImageZoomProps {
  src: string;
  alt?: string;
  className?: string;
}

export function ImageZoom({ src, alt = "Coin image", className }: ImageZoomProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [scale, setScale] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const imageRef = useRef<HTMLImageElement>(null);

  const handleZoomIn = useCallback(() => {
    setScale((s) => Math.min(s + 0.5, 5));
  }, []);

  const handleZoomOut = useCallback(() => {
    setScale((s) => Math.max(s - 0.5, 0.5));
  }, []);

  const handleRotate = useCallback(() => {
    setRotation((r) => (r + 90) % 360);
  }, []);

  const handleReset = useCallback(() => {
    setScale(1);
    setRotation(0);
    setPosition({ x: 0, y: 0 });
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (scale > 1) {
      setIsDragging(true);
      dragStart.current = { x: e.clientX - position.x, y: e.clientY - position.y };
    }
  }, [scale, position]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDragging && scale > 1) {
      setPosition({
        x: e.clientX - dragStart.current.x,
        y: e.clientY - dragStart.current.y,
      });
    }
  }, [isDragging, scale]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.25 : 0.25;
    setScale((s) => Math.min(Math.max(s + delta, 0.5), 5));
  }, []);

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open);
    if (!open) {
      handleReset();
    }
  };

  return (
    <>
      {/* Thumbnail with zoom icon */}
      <div 
        className={cn(
          "relative group cursor-pointer overflow-hidden rounded-lg",
          className
        )}
        onClick={() => setIsOpen(true)}
      >
        <img
          src={src}
          alt={alt}
          className="w-full h-full object-cover transition-transform group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
          <Maximize2 className="w-8 h-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      </div>

      {/* Fullscreen dialog */}
      <Dialog open={isOpen} onOpenChange={handleOpenChange}>
        <DialogContent className="max-w-[95vw] max-h-[95vh] p-0 overflow-hidden bg-black/95">
          <DialogTitle className="sr-only">{alt}</DialogTitle>
          
          {/* Toolbar */}
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 bg-background/80 backdrop-blur-sm rounded-lg p-2 shadow-lg">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleZoomOut}
              disabled={scale <= 0.5}
              title="Zoom out"
            >
              <ZoomOut className="w-4 h-4" />
            </Button>
            <span className="text-sm font-medium min-w-[4rem] text-center">
              {Math.round(scale * 100)}%
            </span>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleZoomIn}
              disabled={scale >= 5}
              title="Zoom in"
            >
              <ZoomIn className="w-4 h-4" />
            </Button>
            <div className="w-px h-6 bg-border" />
            <Button
              variant="ghost"
              size="icon"
              onClick={handleRotate}
              title="Rotate 90°"
            >
              <RotateCw className="w-4 h-4" />
            </Button>
            <div className="w-px h-6 bg-border" />
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              title="Reset"
            >
              Reset
            </Button>
          </div>

          {/* Close button */}
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-4 right-4 z-50 bg-background/80 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          >
            <X className="w-4 h-4" />
          </Button>

          {/* Image container */}
          <div
            className="w-full h-[90vh] flex items-center justify-center overflow-hidden select-none"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onWheel={handleWheel}
            style={{ cursor: scale > 1 ? (isDragging ? "grabbing" : "grab") : "default" }}
          >
            <img
              ref={imageRef}
              src={src}
              alt={alt}
              className="max-w-full max-h-full object-contain transition-transform duration-100"
              style={{
                transform: `translate(${position.x}px, ${position.y}px) scale(${scale}) rotate(${rotation}deg)`,
                transformOrigin: "center center",
              }}
              draggable={false}
            />
          </div>

          {/* Zoom hint */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-xs text-muted-foreground bg-background/80 backdrop-blur-sm px-3 py-1 rounded-full">
            Scroll to zoom • Drag to pan • Click toolbar to rotate
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}


// Simple image gallery for multiple images
interface ImageGalleryProps {
  images: Array<{ src: string; alt?: string; isPrimary?: boolean }>;
  className?: string;
}

export function ImageGallery({ images, className }: ImageGalleryProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  if (!images.length) {
    return (
      <div className={cn("flex items-center justify-center bg-muted rounded-lg aspect-square", className)}>
        <span className="text-muted-foreground text-sm">No images</span>
      </div>
    );
  }

  const primaryImage = images[selectedIndex];

  return (
    <div className={cn("space-y-2", className)}>
      {/* Main image with zoom */}
      <ImageZoom
        src={primaryImage.src}
        alt={primaryImage.alt || `Image ${selectedIndex + 1}`}
        className="aspect-square"
      />

      {/* Thumbnail strip */}
      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {images.map((img, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedIndex(idx)}
              className={cn(
                "w-16 h-16 rounded-md overflow-hidden flex-shrink-0 border-2 transition-colors",
                idx === selectedIndex
                  ? "border-primary"
                  : "border-transparent hover:border-muted-foreground/50"
              )}
            >
              <img
                src={img.src}
                alt={img.alt || `Thumbnail ${idx + 1}`}
                className="w-full h-full object-cover"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
