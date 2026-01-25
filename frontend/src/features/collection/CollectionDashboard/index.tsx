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
import { useState, useMemo } from "react";
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
  
  // Get filter state - include grade and issuing_authority for selectable widgets
  const { 
    category, 
    metal, 
    grade,
    issuing_authority,
    mint_year_gte,
    mint_year_lte,
    priceRange,
    setCategory, 
    setMetal, 
    setGrade,
    setIssuingAuthority,
    setMintYearGte,
    setMintYearLte,
    setPriceRange,
    reset 
  } = useFilterStore();
  
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
    // Toggle ruler filter
    if (issuing_authority === ruler) {
      setIssuingAuthority(null);
    } else {
      setIssuingAuthority(ruler);
    }
  };

  const handleGradeClick = (g: string) => {
    // Toggle grade filter
    if (grade === g.toLowerCase()) {
      setGrade(null);
    } else {
      setGrade(g.toLowerCase());
    }
  };

  const handleCertClick = (service: string) => {
    // TODO: Implement grading_service filter when filterStore supports it
    // For now, this is a no-op placeholder
    void service;
  };

  const handleRunAudit = () => {
    navigate('/audit');
  };

  const handleEnrichAll = () => {
    navigate('/bulk-enrich');
  };

  // Prepare metal data for badges (memoized) - MUST be before any early returns
  const metalData = useMemo(() => 
    stats?.by_metal?.map(m => ({ metal: m.metal, count: m.count })) ?? [],
    [stats?.by_metal]
  );

  // Prepare grade data for spectrum (memoized)
  const gradeData = useMemo(() => 
    stats?.by_grade?.map(g => ({ grade: g.grade, count: g.count })) ?? [],
    [stats?.by_grade]
  );

  // Prepare certification data (memoized)
  const certData = useMemo(() => 
    stats?.by_certification?.map(c => ({ service: c.service, count: c.count })) ?? [],
    [stats?.by_certification]
  );

  // Loading skeleton - after all hooks
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
          activeGrades={grade ? [grade] : []}
          onGradeClick={handleGradeClick}
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
        activeRuler={issuing_authority}
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
          onServiceClick={handleCertClick}
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
          <div className="p-4 pt-2 space-y-4">
            {/* Reset button - at TOP for quick access */}
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

            {/* Year Range */}
            <div>
              <label 
                className="block text-xs font-medium mb-2"
                style={{ color: 'var(--text-secondary)' }}
              >
                Year Range (negative for BC)
              </label>
              <div className="flex gap-2 items-center">
                <input
                  type="number"
                  placeholder="From"
                  value={mint_year_gte ?? ''}
                  onChange={(e) => setMintYearGte(e.target.value ? Number(e.target.value) : null)}
                  className="h-8 px-2 text-sm rounded border"
                  style={{
                    width: '70px',
                    minWidth: 0,
                    background: 'var(--bg-elevated)',
                    borderColor: 'var(--border-subtle)',
                    color: 'var(--text-primary)',
                  }}
                />
                <span style={{ color: 'var(--text-ghost)', flexShrink: 0 }}>—</span>
                <input
                  type="number"
                  placeholder="To"
                  value={mint_year_lte ?? ''}
                  onChange={(e) => setMintYearLte(e.target.value ? Number(e.target.value) : null)}
                  className="h-8 px-2 text-sm rounded border"
                  style={{
                    width: '70px',
                    minWidth: 0,
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
                Price Paid ($)
              </label>
              <div className="flex gap-2 items-center">
                <input
                  type="number"
                  placeholder="Min"
                  value={priceRange[0] || ''}
                  onChange={(e) => {
                    const val = e.target.value ? Number(e.target.value) : 0;
                    setPriceRange([val, priceRange[1]]);
                  }}
                  className="h-8 px-2 text-sm rounded border"
                  style={{
                    width: '70px',
                    minWidth: 0,
                    background: 'var(--bg-elevated)',
                    borderColor: 'var(--border-subtle)',
                    color: 'var(--text-primary)',
                  }}
                />
                <span style={{ color: 'var(--text-ghost)', flexShrink: 0 }}>—</span>
                <input
                  type="number"
                  placeholder="Max"
                  value={priceRange[1] || ''}
                  onChange={(e) => {
                    const val = e.target.value ? Number(e.target.value) : 0;
                    setPriceRange([priceRange[0], val]);
                  }}
                  className="h-8 px-2 text-sm rounded border"
                  style={{
                    width: '70px',
                    minWidth: 0,
                    background: 'var(--bg-elevated)',
                    borderColor: 'var(--border-subtle)',
                    color: 'var(--text-primary)',
                  }}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
