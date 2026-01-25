/**
 * CategoryDonut - Donut chart showing coin distribution by category
 * 
 * Features:
 * - Interactive segments (click to filter)
 * - Center shows total count
 * - Quick filter buttons below
 */

import { useMemo } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { cn } from "@/lib/utils";

interface CategoryData {
  category: string;
  count: number;
  color?: string;
}

// Category colors - actual hex values for Recharts compatibility
const CATEGORY_COLORS: Record<string, string> = {
  imperial: '#C9A227',      // Gold
  republic: '#8B4513',      // Brown
  provincial: '#6B8E23',    // Olive
  greek: '#4682B4',         // Steel blue
  byzantine: '#9370DB',     // Medium purple
  celtic: '#228B22',        // Forest green
  judaean: '#B8860B',       // Dark goldenrod
  judaea: '#B8860B',        // Dark goldenrod
  eastern: '#CD853F',       // Peru
  late: '#708090',          // Slate gray
  other: '#696969',         // Dim gray
};

function getCategoryColor(category: string): string {
  const normalized = category.toLowerCase().replace(/[_\s-]/g, '');
  return CATEGORY_COLORS[normalized] || CATEGORY_COLORS.other;
}

interface CategoryDonutProps {
  data: CategoryData[];
  totalCoins: number;
  onCategoryClick?: (category: string) => void;
  activeCategory?: string | null;
  className?: string;
}

export function CategoryDonut({
  data,
  totalCoins,
  onCategoryClick,
  activeCategory,
  className,
}: CategoryDonutProps) {
  // Prepare chart data with colors
  const chartData = useMemo(() => {
    return data.map(item => ({
      ...item,
      color: item.color || getCategoryColor(item.category),
    }));
  }, [data]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      const pct = totalCoins > 0 ? ((item.count / totalCoins) * 100).toFixed(1) : 0;
      return (
        <div
          className="px-3 py-2 rounded shadow-lg"
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <p 
            className="font-semibold capitalize"
            style={{ color: item.color }}
          >
            {item.category}
          </p>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            {item.count} coins ({pct}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div
      className={cn('rounded-lg p-4', className)}
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Header */}
      <h3 
        className="text-sm font-semibold uppercase tracking-wide mb-4"
        style={{ color: 'var(--text-muted)' }}
      >
        Category
      </h3>

      {/* Chart */}
      <div className="relative" style={{ height: '160px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={45}
              outerRadius={70}
              paddingAngle={2}
              dataKey="count"
              onClick={(_, index) => onCategoryClick?.(chartData[index].category)}
              style={{ cursor: onCategoryClick ? 'pointer' : 'default' }}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color}
                  stroke={activeCategory === entry.category ? '#fff' : 'transparent'}
                  strokeWidth={activeCategory === entry.category ? 2 : 0}
                  opacity={activeCategory && activeCategory !== entry.category ? 0.4 : 1}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>

        {/* Center Label */}
        <div 
          className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
        >
          <span 
            className="text-2xl font-bold"
            style={{ color: 'var(--text-primary)' }}
          >
            {totalCoins}
          </span>
          <span 
            className="text-xs"
            style={{ color: 'var(--text-muted)' }}
          >
            coins
          </span>
        </div>
      </div>

      {/* Quick Filter Buttons */}
      <div className="flex flex-wrap gap-1.5 mt-4">
        {chartData.slice(0, 4).map(({ category, count, color }) => (
          <button
            key={category}
            onClick={() => onCategoryClick?.(category)}
            className={cn(
              'px-2 py-1 rounded text-xs font-medium capitalize transition-all',
              activeCategory === category && 'ring-2 ring-offset-1 ring-offset-[var(--bg-card)]'
            )}
            style={{
              background: activeCategory === category ? color : `${color}30`,
              color: activeCategory === category ? '#fff' : color,
              ringColor: color,
            }}
          >
            {category.replace('_', ' ')}
          </button>
        ))}
        {chartData.length > 4 && (
          <span 
            className="px-2 py-1 text-xs"
            style={{ color: 'var(--text-ghost)' }}
          >
            +{chartData.length - 4}
          </span>
        )}
      </div>
    </div>
  );
}
