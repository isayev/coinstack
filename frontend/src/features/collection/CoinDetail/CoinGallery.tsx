
import { useState } from 'react';
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Maximize2, X, ChevronLeft, ChevronRight, Grid } from 'lucide-react';
import { Coin, Image } from '@/domain/schemas';
import { cn } from '@/lib/utils';
import { AnimatePresence, motion } from 'framer-motion';

interface CoinGalleryProps {
    images: Image[];
    trigger?: React.ReactNode;
    initialIndex?: number;
}

export function CoinGallery({ images, trigger, initialIndex = 0 }: CoinGalleryProps) {
    const [open, setOpen] = useState(false);
    const [currentIndex, setCurrentIndex] = useState(initialIndex);

    if (!images || images.length === 0) return null;

    const currentImage = images[currentIndex];

    const handleNext = () => {
        setCurrentIndex((prev) => (prev + 1) % images.length);
    };

    const handlePrev = () => {
        setCurrentIndex((prev) => (prev - 1 + images.length) % images.length);
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                {trigger || (
                    <Button variant="outline" size="sm" className="gap-2">
                        <Grid className="w-4 h-4" />
                        View Gallery ({images.length})
                    </Button>
                )}
            </DialogTrigger>
            <DialogContent className="max-w-[95vw] h-[90vh] bg-background/95 backdrop-blur-md border-none p-0 flex flex-col overflow-hidden">

                {/* Header / Controls */}
                <div className="flex items-center justify-between p-4 absolute top-0 left-0 right-0 z-50 bg-gradient-to-b from-black/50 to-transparent">
                    <span className="text-white/80 font-medium">
                        {currentIndex + 1} / {images.length}
                    </span>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="text-white hover:bg-white/20 rounded-full"
                        onClick={() => setOpen(false)}
                    >
                        <X className="w-5 h-5" />
                    </Button>
                </div>

                {/* Main Image Stage */}
                <div className="flex-1 relative flex items-center justify-center bg-black/40 p-4">
                    <AnimatePresence mode="wait">
                        <motion.img
                            key={currentImage.url || currentImage.file_path}
                            src={currentImage.url || currentImage.file_path}
                            alt={currentImage.image_type || "Coin Image"}
                            className="max-h-full max-w-full object-contain shadow-2xl rounded-sm"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 1.05 }}
                            transition={{ duration: 0.2 }}
                        />
                    </AnimatePresence>

                    {/* Navigation Arrows */}
                    {images.length > 1 && (
                        <>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="absolute left-4 top-1/2 -translate-y-1/2 bg-black/20 text-white hover:bg-white/20 rounded-full h-12 w-12"
                                onClick={(e) => { e.stopPropagation(); handlePrev(); }}
                            >
                                <ChevronLeft className="w-6 h-6" />
                            </Button>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="absolute right-4 top-1/2 -translate-y-1/2 bg-black/20 text-white hover:bg-white/20 rounded-full h-12 w-12"
                                onClick={(e) => { e.stopPropagation(); handleNext(); }}
                            >
                                <ChevronRight className="w-6 h-6" />
                            </Button>
                        </>
                    )}
                </div>

                {/* Thumbnails Footer */}
                {images.length > 1 && (
                    <div className="h-24 bg-background/80 flex items-center gap-2 px-4 overflow-x-auto border-t border-border/10">
                        {images.map((img, idx) => (
                            <button
                                key={idx}
                                onClick={() => setCurrentIndex(idx)}
                                className={cn(
                                    "relative h-16 w-16 min-w-[4rem] rounded-md overflow-hidden border-2 transition-all",
                                    currentIndex === idx
                                        ? "border-primary ring-2 ring-primary/20 brightness-110"
                                        : "border-transparent opacity-60 hover:opacity-100"
                                )}
                            >
                                <img
                                    src={img.url || img.file_path}
                                    className="h-full w-full object-cover"
                                    alt={`Thumbnail ${idx}`}
                                />
                            </button>
                        ))}
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
}
