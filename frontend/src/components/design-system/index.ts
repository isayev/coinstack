/**
 * CoinStack Design System
 * 
 * Centralized component library for consistent UI across the application.
 * 
 * @module design-system
 */

// Color system and configuration
export * from './colors';

// Badge components
export { MetalBadge, MetalChip } from './MetalBadge';
export type { MetalBadgeProps, MetalBadgeSize, MetalChipProps } from './MetalBadge';

export { GradeBadge, GradeScale } from './GradeBadge';
export type { GradeBadgeProps } from './GradeBadge';

export { RarityIndicator, RarityLegend } from './RarityIndicator';
export type { RarityIndicatorProps } from './RarityIndicator';

// Trend and chart components
export { PriceTrend, SimplePriceTrend } from './PriceTrend';
export type { PriceTrendProps } from './PriceTrend';

export { Sparkline, SparklineWithLabel, PlaceholderSparkline } from './Sparkline';
export type { SparklineProps, SparklineWithLabelProps } from './Sparkline';
