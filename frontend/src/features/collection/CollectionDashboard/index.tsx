/**
 * CollectionDashboard - Left sidebar with all dashboard widgets
 * 
 * Assembles:
 * - CollectionHealthWidget
 * - RulerTimeline
 * - CategoryDonut
 * - MetalBadgeGroup
 * - GradeSpectrum
 * - CertificationSummary
 */

import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { useCollectionStats } from "@/hooks/useCollectionStats";
import { useFilterStore } from "@/stores/filterStore";

// Dashboard widgets
import { CollectionHealthWidget } from "@/components/dashboard/CollectionHealthWidget";
import { RulerTimeline } from "@/components/dashboard/RulerTimeline";
import { CategoryDonut } from "@/components/dashboard/CategoryDonut";
import { MetalBadgeGroup } from "@/components/ui/badges/MetalBadge";
import { GradeSpectrum } from "@/components/ui/badges/GradeBadge";
import { CertificationSummary } from "@/components/ui/badges/CertBadge";

interface CollectionDashboardProps {
  className?: string;
}

export function CollectionDashboard({ className }: CollectionDashboardProps) {
  const navigate = useNavigate();
  const [advancedOpen, setAdvancedOpen] = useState(false);
  
  // Get filter state
  const { category, metal, setCategory, setMetal, reset } = useFilterStore();
  
  // Fetch stats
  const { data: stats, isLoading } = useCollectionStats();

  // Handlers
  const handleCategoryClick = (cat: string) => {
    if (category === cat) {
      setCategory(null);
    } else {
      setCategory(cat);
    }
  };

  const handleMetalClick = (m: string) => {
    if (metal === m.toLowerCase()) {
      setMetal(null);
    } else {
      setMetal(m.toLowerCase());
    }
  };

  const handleRulerClick = (ruler: string) => {
    // Navigate to collection with ruler filter
    navigate(`/?issuer=${encodeURIComponent(ruler)}`);
  };

  const handleRunAudit = () => {
    navigate('/audit');
  };

  const handleEnrichAll = () => {
    navigate('/bulk-enrich');
  };

  // Loading skeleton
  if (isLoading || !stats) {
    return (
      <div className={cn("space-y-4 p-4", className)}>
        {[...Array(4)].map((_, i) => (
          <div 
            key={i}
            className="h-40 rounded-lg animate-pulse"
            style={{ background: 'var(--bg-card)' }}
          />
        ))}
      </div>
    );
  }

  // Prepare metal data for badges
  const metalData = stats.by_metal.map(m => ({
    metal: m.metal,
    count: m.count,
  }));

  // Prepare grade data for spectrum
  const gradeData = stats.by_grade.map(g => ({
    grade: g.grade,
    count: g.count,
  }));

  // Prepare certification data
  const certData = stats.by_certification.map(c => ({
    service: c.service,
    count: c.count,
  }));

  return (
    <div 
      className={cn(
        "h-full overflow-y-auto space-y-4 p-4",
        className
      )}
      style={{
        background: 'var(--bg-app)',
        scrollbarWidth: 'thin',
        scrollbarColor: 'var(--border-subtle) transparent',
      }}
    >
      {/* Collection Health */}
      <CollectionHealthWidget
        overallPct={stats.health.overall_pct}
        totalCoins={stats.health.total_coins}
        withImages={stats.health.with_images}
        withAttribution={stats.health.with_attribution}
        withReferences={stats.health.with_references}
        withProvenance={stats.health.with_provenance}
        withValues={stats.health.with_values}
        onRunAudit={handleRunAudit}
        onEnrichAll={handleEnrichAll}
      />

      {/* Metal Badges - MOVED UP */}
      <div
        className="rounded-lg p-4"
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <h3 
          className="text-sm font-semibold uppercase tracking-wide mb-3"
          style={{ color: 'var(--text-muted)' }}
        >
          Metal
        </h3>
        <MetalBadgeGroup
          metals={metalData}
          activeMetals={metal ? [metal] : []}
          onMetalClick={handleMetalClick}
          size="md"
        />
      </div>

      {/* Grade Spectrum - MOVED UP */}
      <div
        className="rounded-lg p-4"
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <h3 
          className="text-sm font-semibold uppercase tracking-wide mb-3"
          style={{ color: 'var(--text-muted)' }}
        >
          Grade
        </h3>
        <GradeSpectrum
          grades={gradeData}
          showCounts
        />
      </div>

      {/* Ruler Timeline */}
      <RulerTimeline
        data={stats.by_ruler.map(r => ({
          ruler: r.ruler,
          rulerId: r.ruler_id,
          count: r.count,
          reignStart: r.reign_start,
        }))}
        onRulerClick={handleRulerClick}
        maxVisible={6}
      />

      {/* Category Donut */}
      <CategoryDonut
        data={stats.by_category}
        totalCoins={stats.total_coins}
        onCategoryClick={handleCategoryClick}
        activeCategory={category}
      />

      {/* Certification Summary */}
      <div
        className="rounded-lg p-4"
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <h3 
          className="text-sm font-semibold uppercase tracking-wide mb-3"
          style={{ color: 'var(--text-muted)' }}
        >
          Certification
        </h3>
        <CertificationSummary
          certifications={certData}
          totalCoins={stats.total_coins}
        />
      </div>

      {/* Advanced Filters (Collapsible) */}
      <div
        className="rounded-lg overflow-hidden"
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <button
          onClick={() => setAdvancedOpen(!advancedOpen)}
          className="w-full flex items-center justify-between p-4 hover:bg-[var(--bg-hover)] transition-colors"
        >
          <span 
            className="text-sm font-semibold uppercase tracking-wide"
            style={{ color: 'var(--text-muted)' }}
          >
            Advanced Filters
          </span>
          {advancedOpen ? (
            <ChevronUp className="w-4 h-4" style={{ color: 'var(--text-ghost)' }} />
          ) : (
            <ChevronDown className="w-4 h-4" style={{ color: 'var(--text-ghost)' }} />
          )}
        </button>
        
        {advancedOpen && (
          <div className="p-4 pt-0 space-y-4">
            {/* Year Range */}
            <div>
              <label 
                className="block text-xs font-medium mb-2"
                style={{ color: 'var(--text-secondary)' }}
              >
                Year Range
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="From"
                  className="flex-1 h-8 px-2 text-sm rounded border"
                  style={{
                    background: 'var(--bg-elevated)',
                    borderColor: 'var(--border-subtle)',
                    color: 'var(--text-primary)',
                  }}
                />
                <span style={{ color: 'var(--text-ghost)' }}>—</span>
                <input
                  type="number"
                  placeholder="To"
                  className="flex-1 h-8 px-2 text-sm rounded border"
                  style={{
                    background: 'var(--bg-elevated)',
                    borderColor: 'var(--border-subtle)',
                    color: 'var(--text-primary)',
                  }}
                />
              </div>
            </div>

            {/* Price Range */}
            <div>
              <label 
                className="block text-xs font-medium mb-2"
                style={{ color: 'var(--text-secondary)' }}
              >
                Price Range
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Min $"
                  className="flex-1 h-8 px-2 text-sm rounded border"
                  style={{
                    background: 'var(--bg-elevated)',
                    borderColor: 'var(--border-subtle)',
                    color: 'var(--text-primary)',
                  }}
                />
                <span style={{ color: 'var(--text-ghost)' }}>—</span>
                <input
                  type="number"
                  placeholder="Max $"
                  className="flex-1 h-8 px-2 text-sm rounded border"
                  style={{
                    background: 'var(--bg-elevated)',
                    borderColor: 'var(--border-subtle)',
                    color: 'var(--text-primary)',
                  }}
                />
              </div>
            </div>

            {/* Reset button */}
            <button
              onClick={() => reset()}
              className="w-full h-8 text-sm font-medium rounded border transition-colors hover:bg-[var(--bg-hover)]"
              style={{
                borderColor: 'var(--border-subtle)',
                color: 'var(--text-muted)',
              }}
            >
              Reset All Filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
