import { motion } from "framer-motion";
import {
  Server,
  AlertTriangle,
  MoveRight,
  Leaf,
  IndianRupee,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";
import type { DashboardSummary } from "@/types/dashboard";

const cards = [
  { key: "totalVMs" as const, label: "Total VMs", icon: Server, color: "text-foreground" },
  { key: "healthyVMs" as const, label: "Healthy VMs", icon: ShieldCheck, color: "text-success" },
  { key: "badVMs" as const, label: "Bad VMs", icon: ShieldAlert, color: "text-destructive" },
  {
    key: "anomalies" as const,
    label: "Anomalies Detected",
    icon: AlertTriangle,
    color: "text-destructive",
  },
  {
    key: "migrationRecs" as const,
    label: "Migration Recs",
    icon: MoveRight,
    color: "text-warning",
  },
  {
    key: "totalCarbonReduction" as const,
    label: "Carbon Reduction (gCO2)",
    icon: Leaf,
    color: "text-primary",
  },
  {
    key: "totalSavings" as const,
    label: "Est. Savings (₹/mo)",
    icon: IndianRupee,
    color: "text-success",
  },
];

export function SummaryCards({ summary }: { summary: DashboardSummary }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-7">
      {cards.map((card, i) => (
        <motion.div
          key={card.key}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: i * 0.08 }}
          className="rounded-xl border border-border bg-card p-5"
          style={{ boxShadow: "var(--shadow-card)" }}
        >
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {card.label}
            </p>
            <card.icon className={`h-4 w-4 ${card.color}`} />
          </div>
          <p className="mt-2 text-2xl font-bold font-[family-name:var(--font-display)] text-card-foreground">
            {card.key === "totalSavings"
              ? `₹${summary[card.key].toLocaleString("en-IN", { maximumFractionDigits: 0 })}`
              : card.key === "totalCarbonReduction"
                ? `${summary[card.key].toLocaleString("en-IN", { maximumFractionDigits: 0 })}`
                : summary[card.key]}
          </p>
        </motion.div>
      ))}
    </div>
  );
}
