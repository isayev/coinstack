import { useStats } from "@/hooks/useStats"
import { Card, CardContent } from "@/components/ui/card"
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts"
import { Coins, TrendingUp, Award, Layers } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"

// V3.0 Design System Colors
const CATEGORY_COLORS: Record<string, string> = {
  greek: "#16A34A",
  celtic: "#059669",
  republic: "#DC2626",
  imperial: "#7C3AED",
  provincial: "#2563EB",
  judaean: "#0EA5E9",
  byzantine: "#A855F7",
  migration: "#6366F1",
  pseudo_roman: "#EC4899",
  other: "#6B7280",
}

const METAL_COLORS: Record<string, string> = {
  gold: "#F59E0B",
  electrum: "#EAB308",
  silver: "#94A3B8",
  billon: "#71717A",
  potin: "#78716C",
  orichalcum: "#D97706",
  bronze: "#F97316",
  copper: "#EA580C",
  lead: "#64748B",
  ae: "#A1A1AA",
  uncertain: "#D1D5DB",
}

const GRADE_COLORS: Record<string, string> = {
  poor: "#3B82F6",
  fair: "#64D2FF",
  fine: "#34C759",
  vf: "#F59E0B",
  ef: "#FF9500",
  au: "#FF6B35",
  ms: "#EF4444",
}

export function StatsPageV3() {
  const { data: stats, isLoading, error } = useStats()

  if (isLoading) {
    return (
      <div
        className="h-full"
        style={{ background: 'var(--bg-app)' }}
      >
        <div className="container mx-auto p-6 max-w-7xl space-y-6">
          <Skeleton className="h-12 w-64" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Skeleton className="h-[280px]" />
            <Skeleton className="h-[280px]" />
            <Skeleton className="h-[280px]" />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Skeleton className="h-[400px]" />
            <Skeleton className="h-[400px]" />
          </div>
        </div>
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div
        className="flex items-center justify-center h-full"
        style={{ background: 'var(--bg-app)' }}
      >
        <div className="text-center">
          <h2
            className="text-xl font-bold mb-2"
            style={{ color: 'var(--text-primary)' }}
          >
            Error loading statistics
          </h2>
          <p
            className="text-sm"
            style={{ color: 'var(--text-muted)' }}
          >
            Unable to load collection statistics. Please try again.
          </p>
        </div>
      </div>
    )
  }

  // Process data
  const categoryData = stats.by_category.map((c) => ({
    ...c,
    name: c.category.charAt(0).toUpperCase() + c.category.slice(1).replace("_", " "),
    fill: CATEGORY_COLORS[c.category] || "#6B7280",
  }))

  const metalData = stats.by_metal.map((m) => ({
    ...m,
    name: m.metal.charAt(0).toUpperCase() + m.metal.slice(1).replace("_", " "),
    fill: METAL_COLORS[m.metal] || "#6B7280",
  }))

  // Calculate grade distribution
  const gradeDistribution = [
    { grade: "Poor", count: 0, fill: GRADE_COLORS.poor },
    { grade: "Fair", count: 0, fill: GRADE_COLORS.fair },
    { grade: "Fine", count: 0, fill: GRADE_COLORS.fine },
    { grade: "VF", count: 0, fill: GRADE_COLORS.vf },
    { grade: "EF", count: 0, fill: GRADE_COLORS.ef },
    { grade: "AU", count: 0, fill: GRADE_COLORS.au },
    { grade: "MS", count: 0, fill: GRADE_COLORS.ms },
  ]

  // This is a simplified distribution - in production you'd get this from the API
  const gradeMap: Record<string, number> = {
    "Poor": 2,
    "Fair": 8,
    "Fine": 15,
    "VF": 32,
    "EF": 25,
    "AU": 12,
    "MS": 6,
  }

  gradeDistribution.forEach(g => {
    g.count = gradeMap[g.grade] || 0
  })

  // Mock sparkline data (in production, this would come from API)
  const valueSparklineData = [
    { month: "Jan", value: stats.total_value * 0.85 },
    { month: "Feb", value: stats.total_value * 0.88 },
    { month: "Mar", value: stats.total_value * 0.92 },
    { month: "Apr", value: stats.total_value * 0.95 },
    { month: "May", value: stats.total_value * 0.98 },
    { month: "Jun", value: stats.total_value },
  ]

  const performanceChange = ((stats.total_value - valueSparklineData[0].value) / valueSparklineData[0].value * 100)

  return (
    <div
      className="h-full flex flex-col"
      style={{ background: 'var(--bg-app)' }}
    >
      {/* Header */}
      <div
        className="border-b px-6 py-4"
        style={{
          background: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)',
        }}
      >
        <h1
          className="text-2xl font-bold"
          style={{ color: 'var(--text-primary)' }}
        >
          Analytics
        </h1>
        <p
          className="text-sm"
          style={{ color: 'var(--text-muted)' }}
        >
          Portfolio performance across {stats.total_coins} coins
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 max-w-7xl space-y-6">

          {/* Row 1: Key Metrics (3-col) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

            {/* Portfolio Value */}
            <div
              className="relative rounded-2xl p-8 border transition-all hover:shadow-2xl"
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              <div
                className="absolute left-0 top-0 bottom-0 w-[6px] rounded-l-2xl"
                style={{ background: 'var(--cat-imperial)' }}
              />
              <div className="relative z-10">
                <div
                  className="text-xs uppercase tracking-wider font-medium mb-2"
                  style={{ color: 'var(--text-muted)' }}
                >
                  Portfolio Value
                </div>
                <div
                  className="text-4xl font-bold mb-2"
                  style={{ color: 'var(--text-primary)' }}
                >
                  ${stats.total_value.toLocaleString()}
                </div>
                <div className="flex items-center gap-2 mb-6">
                  <div
                    className="px-3 py-1 rounded-full text-xs font-medium"
                    style={{
                      background: performanceChange > 0 ? 'var(--perf-positive)' : 'var(--perf-negative)',
                      color: '#000',
                    }}
                  >
                    {performanceChange > 0 ? '▲' : '▼'} {Math.abs(performanceChange).toFixed(1)}%
                  </div>
                  <div
                    className="text-sm"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    vs 6 months ago
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={40}>
                  <AreaChart data={valueSparklineData}>
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="var(--perf-positive)"
                      fill="var(--perf-positive)"
                      fillOpacity={0.2}
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Category Distribution */}
            <div
              className="relative rounded-2xl p-8 border transition-all hover:shadow-2xl"
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              <div
                className="absolute left-0 top-0 bottom-0 w-[6px] rounded-l-2xl"
                style={{ background: 'var(--cat-republic)' }}
              />
              <div className="relative z-10">
                <div
                  className="text-xs uppercase tracking-wider font-medium mb-4"
                  style={{ color: 'var(--text-muted)' }}
                >
                  By Category
                </div>
                <ResponsiveContainer width="100%" height={160}>
                  <PieChart>
                    <Pie
                      data={categoryData}
                      dataKey="count"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={70}
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-1 mt-4">
                  {categoryData.slice(0, 3).map((cat) => (
                    <div
                      key={cat.category}
                      className="flex justify-between text-sm"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      <span>{cat.name}</span>
                      <span className="font-mono">
                        {cat.count} ({((cat.count / stats.total_coins) * 100).toFixed(0)}%)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Average Grade */}
            <div
              className="relative rounded-2xl p-8 border transition-all hover:shadow-2xl"
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              <div
                className="absolute left-0 top-0 bottom-0 w-[6px] rounded-l-2xl"
                style={{ background: 'var(--grade-vf)' }}
              />
              <div className="relative z-10 text-center">
                <div
                  className="text-xs uppercase tracking-wider font-medium mb-4"
                  style={{ color: 'var(--text-muted)' }}
                >
                  Portfolio Grade
                </div>
                <div
                  className="inline-block px-6 py-3 rounded-full text-lg font-bold mb-4 shadow-lg"
                  style={{
                    background: 'var(--grade-vf)',
                    color: '#000',
                  }}
                >
                  VF
                </div>
                <div
                  className="text-3xl font-bold mb-2"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {((gradeDistribution.slice(3).reduce((sum, g) => sum + g.count, 0) / 100) * 100).toFixed(0)}%
                </div>
                <div
                  className="text-sm mb-4"
                  style={{ color: 'var(--text-muted)' }}
                >
                  VF or better
                </div>
                <ResponsiveContainer width="100%" height={50}>
                  <BarChart data={gradeDistribution} layout="horizontal">
                    <Bar dataKey="count" radius={[4, 4, 4, 4]}>
                      {gradeDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>

          {/* Row 2: Metal & Grade Distributions (2-col) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* Metal Distribution */}
            <div
              className="relative rounded-2xl p-8 border"
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              <div
                className="absolute left-0 top-0 bottom-0 w-[6px] rounded-l-2xl"
                style={{ background: 'var(--metal-au)' }}
              />
              <div className="relative z-10">
                <h3
                  className="text-xl font-semibold mb-6"
                  style={{ color: 'var(--text-primary)' }}
                >
                  By Metal
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={metalData}
                      dataKey="count"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={({ name, percent }) =>
                        `${name} ${(percent * 100).toFixed(0)}%`
                      }
                    >
                      {metalData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number, name: string, props: any) => [
                        `${value} coins ($${props.payload.total_value.toLocaleString()})`,
                        name,
                      ]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Grade Distribution */}
            <div
              className="relative rounded-2xl p-8 border"
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              <div
                className="absolute left-0 top-0 bottom-0 w-[6px] rounded-l-2xl"
                style={{ background: 'var(--grade-vf)' }}
              />
              <div className="relative z-10">
                <h3
                  className="text-xl font-semibold mb-6"
                  style={{ color: 'var(--text-primary)' }}
                >
                  By Grade
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={gradeDistribution} layout="vertical">
                    <XAxis type="number" hide />
                    <YAxis
                      dataKey="grade"
                      type="category"
                      width={60}
                      tick={{ fill: 'var(--text-secondary)', fontSize: 13 }}
                    />
                    <Tooltip
                      formatter={(value: number) => [`${value} coins`, "Count"]}
                    />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                      {gradeDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>

          {/* Row 3: Additional Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

            <Card
              className="border"
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Coins
                    className="w-4 h-4"
                    style={{ color: 'var(--text-muted)' }}
                  />
                  <span
                    className="text-sm"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    Total Coins
                  </span>
                </div>
                <div
                  className="text-2xl font-bold mt-1"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {stats.total_coins}
                </div>
              </CardContent>
            </Card>

            <Card
              className="border"
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <TrendingUp
                    className="w-4 h-4"
                    style={{ color: 'var(--text-muted)' }}
                  />
                  <span
                    className="text-sm"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    Average
                  </span>
                </div>
                <div
                  className="text-2xl font-bold mt-1"
                  style={{ color: 'var(--text-primary)' }}
                >
                  ${stats.average_price.toFixed(0)}
                </div>
              </CardContent>
            </Card>

            <Card
              className="border"
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Layers
                    className="w-4 h-4"
                    style={{ color: 'var(--text-muted)' }}
                  />
                  <span
                    className="text-sm"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    Median
                  </span>
                </div>
                <div
                  className="text-2xl font-bold mt-1"
                  style={{ color: 'var(--text-primary)' }}
                >
                  ${stats.median_price.toFixed(0)}
                </div>
              </CardContent>
            </Card>

            <Card
              className="border"
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              <CardContent className="pt-6">
                <div className="flex items-center gap-2">
                  <Award
                    className="w-4 h-4"
                    style={{ color: 'var(--text-muted)' }}
                  />
                  <span
                    className="text-sm"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    Highest
                  </span>
                </div>
                <div
                  className="text-2xl font-bold mt-1"
                  style={{ color: 'var(--text-primary)' }}
                >
                  ${stats.highest_value_coin.toLocaleString()}
                </div>
              </CardContent>
            </Card>

          </div>

          {/* Row 4: Top Rulers & Price Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* Top Rulers */}
            <div
              className="relative rounded-2xl p-8 border"
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              <div
                className="absolute left-0 top-0 bottom-0 w-[6px] rounded-l-2xl"
                style={{ background: 'var(--cat-imperial)' }}
              />
              <div className="relative z-10">
                <h3
                  className="text-xl font-semibold mb-6"
                  style={{ color: 'var(--text-primary)' }}
                >
                  Top 10 Rulers
                </h3>
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart
                    data={stats.top_rulers}
                    layout="vertical"
                    margin={{ left: 80 }}
                  >
                    <XAxis type="number" tick={{ fill: 'var(--text-muted)' }} />
                    <YAxis
                      dataKey="ruler"
                      type="category"
                      width={75}
                      tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                    />
                    <Tooltip
                      formatter={(value: number, _name: string, props: any) => [
                        `${value} coins ($${props.payload.total_value.toLocaleString()})`,
                        "Count",
                      ]}
                    />
                    <Bar dataKey="count" fill="#3B82F6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Price Distribution */}
            <div
              className="relative rounded-2xl p-8 border"
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              <div
                className="absolute left-0 top-0 bottom-0 w-[6px] rounded-l-2xl"
                style={{ background: 'var(--perf-positive)' }}
              />
              <div className="relative z-10">
                <h3
                  className="text-xl font-semibold mb-6"
                  style={{ color: 'var(--text-primary)' }}
                >
                  Price Distribution
                </h3>
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={stats.price_distribution}>
                    <XAxis
                      dataKey="range"
                      tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
                    />
                    <YAxis tick={{ fill: 'var(--text-muted)' }} />
                    <Tooltip formatter={(value: number) => [`${value} coins`, "Count"]} />
                    <Bar dataKey="count" fill="#10B981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>

        </div>
      </div>
    </div>
  )
}
