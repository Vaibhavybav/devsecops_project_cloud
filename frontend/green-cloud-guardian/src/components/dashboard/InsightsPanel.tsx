import { motion } from "framer-motion";
import { Power, Leaf, IndianRupee, AlertTriangle, CheckCircle2 } from "lucide-react";
import type { DashboardSummary, VMResult } from "@/types/dashboard";

export function InsightsPanel({ summary, data }: { summary: DashboardSummary; data: VMResult[] }) {
  const moveRecommendations = data.filter((row) =>
    row.final_action.toLowerCase().startsWith("move from "),
  );
  const criticalVms = data.filter((row) => row.vm_status === "Bad");
  const optimalVms = data.filter((row) => row.vm_status === "Healthy");
  const topMove = moveRecommendations.slice().sort((a, b) => b.carbon_saving - a.carbon_saving)[0];

  const insights = [
    {
      icon: Power,
      text: topMove
        ? `VM ${topMove.server_id} should move from ${topMove.region} → ${topMove.target_region} (reduces carbon by ${Math.max(topMove.carbon_saving, 0).toFixed(0)} gCO2/kWh)`
        : "No migration recommendation currently required",
      color: "text-warning",
      bg: "bg-warning/10",
    },
    {
      icon: Leaf,
      text: `High carbon intensity detected in ${summary.highestCarbonRegion} region`,
      color: "text-primary",
      bg: "bg-primary/10",
    },
    {
      icon: Leaf,
      text: `Total carbon reduction possible: ${summary.totalCarbonReduction.toLocaleString("en-IN", { maximumFractionDigits: 0 })} gCO2`,
      color: "text-primary",
      bg: "bg-primary/10",
    },
    {
      icon: AlertTriangle,
      text: `${criticalVms.length} critical VMs need migration`,
      color: "text-destructive",
      bg: "bg-destructive/10",
    },
    {
      icon: CheckCircle2,
      text: `${optimalVms.length} VMs are operating optimally`,
      color: "text-success",
      bg: "bg-success/10",
    },
    {
      icon: IndianRupee,
      text: `Estimated savings: ₹${summary.totalSavings.toLocaleString("en-IN", { maximumFractionDigits: 0 })}/month`,
      color: "text-success",
      bg: "bg-success/10",
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.5 }}
      className="rounded-xl border border-border bg-card p-6"
      style={{ boxShadow: "var(--shadow-card)" }}
    >
      <h2 className="mb-4 text-lg font-semibold font-[family-name:var(--font-display)] text-card-foreground">
        💡 Insights
      </h2>
      <div className="grid gap-3 sm:grid-cols-2">
        {insights.map((insight, i) => (
          <div
            key={i}
            className="flex items-start gap-3 rounded-lg border border-border/50 bg-secondary/30 p-4"
          >
            <div className={`rounded-lg ${insight.bg} p-2`}>
              <insight.icon className={`h-4 w-4 ${insight.color}`} />
            </div>
            <p className="text-sm leading-relaxed text-card-foreground">{insight.text}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
