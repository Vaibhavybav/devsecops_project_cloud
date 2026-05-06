import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { VMResult } from "@/types/dashboard";

const COLORS = [
  "oklch(0.72 0.19 155)", // green/primary
  "oklch(0.60 0.22 25)", // red
  "oklch(0.80 0.16 80)", // yellow
  "oklch(0.65 0.20 200)", // teal
  "oklch(0.65 0.18 280)", // purple
];

export function Visualizations({ data }: { data: VMResult[] }) {
  // Action distribution
  const actionCounts: Record<string, number> = {};
  data.forEach((r) => {
    actionCounts[r.final_action] = (actionCounts[r.final_action] || 0) + 1;
  });
  const actionData = Object.entries(actionCounts).map(([name, value]) => ({ name, value }));

  const currentAvgCarbon = data.length
    ? data.reduce((sum, row) => sum + row.carbon_intensity, 0) / data.length
    : 0;
  const targetAvgCarbon = data.length
    ? data.reduce((sum, row) => sum + (row.carbon_intensity - row.carbon_saving), 0) / data.length
    : 0;
  const carbonComparison = [
    { name: "Current", value: Math.max(currentAvgCarbon, 0) },
    { name: "Target", value: Math.max(targetAvgCarbon, 0) },
  ];

  const regionCounts: Record<string, number> = {};
  data.forEach((row) => {
    regionCounts[row.region] = (regionCounts[row.region] || 0) + 1;
  });
  const regionDistribution = Object.entries(regionCounts).map(([name, value]) => ({ name, value }));

  // Anomaly pie
  const anomalyCount = data.filter((r) => r.ml_anomaly === 1).length;
  const normalCount = data.length - anomalyCount;
  const pieData = [
    { name: "Normal", value: normalCount },
    { name: "Anomaly", value: anomalyCount },
  ];

  const tooltipStyle = {
    backgroundColor: "oklch(0.17 0.02 260)",
    border: "1px solid oklch(0.25 0.02 260)",
    borderRadius: "8px",
    color: "oklch(0.93 0.01 260)",
    fontSize: "12px",
  };

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.25 }}
        className="rounded-xl border border-border bg-card p-6"
        style={{ boxShadow: "var(--shadow-card)" }}
      >
        <h3 className="mb-4 text-sm font-semibold font-[family-name:var(--font-display)] text-card-foreground">
          Carbon Intensity: Current vs Target
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={carbonComparison}>
            <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.25 0.02 260)" />
            <XAxis dataKey="name" tick={{ fill: "oklch(0.60 0.02 260)", fontSize: 11 }} />
            <YAxis tick={{ fill: "oklch(0.60 0.02 260)", fontSize: 11 }} />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value) => `${Number(value).toFixed(1)} gCO2/kWh`}
            />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              <Cell fill="oklch(0.60 0.22 25)" />
              <Cell fill="oklch(0.72 0.19 155)" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.28 }}
        className="rounded-xl border border-border bg-card p-6"
        style={{ boxShadow: "var(--shadow-card)" }}
      >
        <h3 className="mb-4 text-sm font-semibold font-[family-name:var(--font-display)] text-card-foreground">
          Region Distribution
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={regionDistribution}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={3}
              dataKey="value"
              strokeWidth={0}
            >
              {regionDistribution.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: "12px", color: "oklch(0.60 0.02 260)" }} />
          </PieChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Bar chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="rounded-xl border border-border bg-card p-6"
        style={{ boxShadow: "var(--shadow-card)" }}
      >
        <h3 className="mb-4 text-sm font-semibold font-[family-name:var(--font-display)] text-card-foreground">
          Action Distribution
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={actionData}>
            <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.25 0.02 260)" />
            <XAxis dataKey="name" tick={{ fill: "oklch(0.60 0.02 260)", fontSize: 11 }} />
            <YAxis tick={{ fill: "oklch(0.60 0.02 260)", fontSize: 11 }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              {actionData.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Pie chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
        className="rounded-xl border border-border bg-card p-6"
        style={{ boxShadow: "var(--shadow-card)" }}
      >
        <h3 className="mb-4 text-sm font-semibold font-[family-name:var(--font-display)] text-card-foreground">
          Anomaly vs Normal
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={4}
              dataKey="value"
              strokeWidth={0}
            >
              <Cell fill="oklch(0.72 0.19 155)" />
              <Cell fill="oklch(0.60 0.22 25)" />
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: "12px", color: "oklch(0.60 0.02 260)" }} />
          </PieChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
}
