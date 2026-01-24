import { useStats } from "@/hooks/useStats";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  Legend,
} from "recharts";
import { Coins, DollarSign, TrendingUp, Award, Layers, MapPin } from "lucide-react";

// Color palettes
const CATEGORY_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];
const METAL_COLORS = {
  gold: "#fbbf24",
  silver: "#94a3b8",
  bronze: "#f97316",
  billon: "#71717a",
  copper: "#ea580c",
  orichalcum: "#eab308",
};

export function StatsPage() {
  const { data: stats, isLoading, error } = useStats();

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading statistics...</div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-destructive">Error loading statistics</div>
      </div>
    );
  }

  // Aggregate storage by tray (Velv1, Velv2, Velv3, SlabBox1)
  const storageAggregated = stats.by_storage.reduce((acc, item) => {
    let key = item.location;
    if (item.location.startsWith("Velv1")) key = "Velvet Tray 1";
    else if (item.location.startsWith("Velv2")) key = "Velvet Tray 2";
    else if (item.location.startsWith("Velv3")) key = "Velvet Tray 3";
    else if (item.location === "SlabBox1") key = "Slab Box";
    else key = "Other";
    
    acc[key] = (acc[key] || 0) + item.count;
    return acc;
  }, {} as Record<string, number>);

  const storageData = Object.entries(storageAggregated).map(([name, count]) => ({
    name,
    count,
  }));

  // Add colors to metal data
  const metalData = stats.by_metal.map((m) => ({
    ...m,
    name: m.metal.charAt(0).toUpperCase() + m.metal.slice(1),
    fill: METAL_COLORS[m.metal as keyof typeof METAL_COLORS] || "#6b7280",
  }));

  // Format category names
  const categoryData = stats.by_category.map((c, i) => ({
    ...c,
    name: c.category.charAt(0).toUpperCase() + c.category.slice(1),
    fill: CATEGORY_COLORS[i % CATEGORY_COLORS.length],
  }));

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Collection Statistics</h1>
        <p className="text-muted-foreground">Overview of your coin collection</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Coins className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Total Coins</span>
            </div>
            <div className="text-2xl font-bold mt-1">{stats.total_coins}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Total Value</span>
            </div>
            <div className="text-2xl font-bold mt-1">
              ${stats.total_value.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Average</span>
            </div>
            <div className="text-2xl font-bold mt-1">
              ${stats.average_price.toFixed(0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Median</span>
            </div>
            <div className="text-2xl font-bold mt-1">
              ${stats.median_price.toFixed(0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Award className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Highest</span>
            </div>
            <div className="text-2xl font-bold mt-1">
              ${stats.highest_value_coin.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Lowest</span>
            </div>
            <div className="text-2xl font-bold mt-1">
              ${stats.lowest_value_coin.toFixed(0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* By Category */}
        <Card>
          <CardHeader>
            <CardTitle>By Category</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categoryData}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                >
                  {categoryData.map((entry, index) => (
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
          </CardContent>
        </Card>

        {/* By Metal */}
        <Card>
          <CardHeader>
            <CardTitle>By Metal</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
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
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Rulers */}
        <Card>
          <CardHeader>
            <CardTitle>Top 10 Rulers</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart
                data={stats.top_rulers}
                layout="vertical"
                margin={{ left: 80 }}
              >
                <XAxis type="number" />
                <YAxis dataKey="ruler" type="category" width={75} tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value: number, name: string, props: any) => [
                    `${value} coins ($${props.payload.total_value.toLocaleString()})`,
                    "Count",
                  ]}
                />
                <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Price Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Price Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={stats.price_distribution}>
                <XAxis dataKey="range" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip formatter={(value: number) => [`${value} coins`, "Count"]} />
                <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Storage */}
      <Card>
        <CardHeader>
          <CardTitle>Storage Locations</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={storageData}>
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis />
              <Tooltip formatter={(value: number) => [`${value} coins`, "Count"]} />
              <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
