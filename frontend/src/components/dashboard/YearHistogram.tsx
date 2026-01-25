/**
 * YearHistogram - Timeline distribution of coins by mint year
 * 
 * Features:
 * - Bar chart showing coin count by year
 * - Brush selection for filtering date range
 * - Smart era labels (BC/AD divider)
 * - Click bar to filter by year
 */

import { useMemo, useState, useCallback } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Brush,
  ReferenceLine,
  Cell,
} from "recharts";
import { cn } from "@/lib/utils";
import { Calendar } from "lucide-react";

interface YearData {
  year: number;
  count: number;
}

interface YearHistogramProps {
  data: YearData[];
  onYearClick?: (year: number) => void;
  onRangeSelect?: (startYear: number, endYear: number) => void;
  selectedRange?: { start: number; end: number } | null;
  height?: number;
  showBrush?: boolean;
  className?: string;
}

// Format year with BC/AD suffix
function formatYear(year: number): string {
  if (year < 0) {
    return `${Math.abs(year)} BC`;
  }
  if (year === 0) {
    return '1 BC'; // There's no year 0
  }
  return `${year} AD`;
}

// Custom tooltip
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div
        className="px-3 py-2 rounded shadow-lg"
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <p 
          className="font-semibold"
          style={{ color: 'var(--text-primary)' }}
        >
          {formatYear(data.year)}
        </p>
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          {data.count} {data.count === 1 ? 'coin' : 'coins'}
        </p>
      </div>
    );
  }
  return null;
};

export function YearHistogram({
  data,
  onYearClick,
  onRangeSelect,
  selectedRange,
  height = 150,
  showBrush = true,
  className,
}: YearHistogramProps) {
  const [brushRange, setBrushRange] = useState<{ startIndex: number; endIndex: number } | null>(null);

  // Sort data by year and fill gaps
  const chartData = useMemo(() => {
    if (data.length === 0) return [];
    
    const sorted = [...data].sort((a, b) => a.year - b.year);
    return sorted;
  }, [data]);

  // Find BC/AD divider position
  const bcAdDividerIndex = useMemo(() => {
    const index = chartData.findIndex(d => d.year >= 0);
    return index > 0 ? index : null;
  }, [chartData]);

  // Compute statistics
  const stats = useMemo(() => {
    if (chartData.length === 0) return null;
    const years = chartData.map(d => d.year);
    const counts = chartData.map(d => d.count);
    return {
      minYear: Math.min(...years),
      maxYear: Math.max(...years),
      totalCoins: counts.reduce((a, b) => a + b, 0),
    };
  }, [chartData]);

  // Handle brush change
  const handleBrushChange = useCallback((brushData: any) => {
    if (!brushData || brushData.startIndex === undefined) return;
    
    setBrushRange({
      startIndex: brushData.startIndex,
      endIndex: brushData.endIndex,
    });

    if (onRangeSelect && chartData.length > 0) {
      const startYear = chartData[brushData.startIndex]?.year;
      const endYear = chartData[brushData.endIndex]?.year;
      if (startYear !== undefined && endYear !== undefined) {
        onRangeSelect(startYear, endYear);
      }
    }
  }, [chartData, onRangeSelect]);

  // Handle bar click
  const handleBarClick = useCallback((data: any) => {
    if (onYearClick && data?.year !== undefined) {
      onYearClick(data.year);
    }
  }, [onYearClick]);

  if (chartData.length === 0) {
    return (
      <div 
        className={cn("flex items-center justify-center", className)}
        style={{ height, color: 'var(--text-muted)' }}
      >
        <div className="text-center">
          <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No year data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
          <span 
            className="text-xs font-medium"
            style={{ color: 'var(--text-muted)' }}
          >
            Year Distribution
          </span>
        </div>
        {stats && (
          <span 
            className="text-xs"
            style={{ color: 'var(--text-ghost)' }}
          >
            {formatYear(stats.minYear)} — {formatYear(stats.maxYear)}
          </span>
        )}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          margin={{ top: 5, right: 5, left: 5, bottom: showBrush ? 30 : 5 }}
        >
          <XAxis 
            dataKey="year" 
            tickFormatter={formatYear}
            tick={{ fontSize: 10, fill: 'var(--text-ghost)' }}
            axisLine={{ stroke: 'var(--border-subtle)' }}
            tickLine={{ stroke: 'var(--border-subtle)' }}
            interval="preserveStartEnd"
          />
          <YAxis 
            hide
            domain={[0, 'auto']}
          />
          <Tooltip content={<CustomTooltip />} />
          
          {/* BC/AD divider line */}
          {bcAdDividerIndex !== null && (
            <ReferenceLine
              x={0}
              stroke="var(--text-ghost)"
              strokeDasharray="3 3"
              label={{
                value: 'BC|AD',
                position: 'top',
                fill: 'var(--text-ghost)',
                fontSize: 10,
              }}
            />
          )}
          
          <Bar
            dataKey="count"
            radius={[2, 2, 0, 0]}
            onClick={handleBarClick}
            cursor={onYearClick ? 'pointer' : 'default'}
          >
            {chartData.map((entry, index) => {
              const isInRange = selectedRange 
                ? entry.year >= selectedRange.start && entry.year <= selectedRange.end
                : true;
              return (
                <Cell
                  key={`cell-${index}`}
                  fill={isInRange ? 'var(--cat-imperial)' : 'var(--bg-hover)'}
                  opacity={isInRange ? 0.8 : 0.3}
                />
              );
            })}
          </Bar>
          
          {showBrush && (
            <Brush
              dataKey="year"
              height={20}
              stroke="var(--border-subtle)"
              fill="var(--bg-elevated)"
              tickFormatter={formatYear}
              onChange={handleBrushChange}
            />
          )}
        </BarChart>
      </ResponsiveContainer>

      {/* Selected range info */}
      {selectedRange && (
        <div 
          className="text-center text-xs"
          style={{ color: 'var(--text-secondary)' }}
        >
          Selected: {formatYear(selectedRange.start)} — {formatYear(selectedRange.end)}
        </div>
      )}
    </div>
  );
}
