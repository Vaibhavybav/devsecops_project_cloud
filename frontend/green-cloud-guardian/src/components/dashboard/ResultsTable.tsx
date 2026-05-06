import { motion } from "framer-motion";
import { useState } from "react";
import { AlertTriangle } from "lucide-react";
import type { VMResult } from "@/types/dashboard";

function ActionBadge({ action }: { action: string }) {
  const lower = action.toLowerCase();
  let cls = "bg-secondary text-secondary-foreground";
  if (lower.includes("shutdown")) cls = "bg-destructive/15 text-destructive";
  else if (lower.includes("move from") || lower.includes("green") || lower.includes("migrat"))
    cls = "bg-primary/15 text-primary";
  else if (lower.includes("normal") || lower.includes("keep")) cls = "bg-success/15 text-success";
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {action}
    </span>
  );
}

function AnomalyBadge({ anomaly }: { anomaly: number }) {
  return anomaly === 1 ? (
    <span className="inline-block rounded-full bg-destructive/15 px-2.5 py-0.5 text-xs font-medium text-destructive">
      Anomaly
    </span>
  ) : (
    <span className="inline-block rounded-full bg-success/15 px-2.5 py-0.5 text-xs font-medium text-success">
      Normal
    </span>
  );
}

function VmStatusBadge({ status }: { status: VMResult["vm_status"] }) {
  return status === "Bad" ? (
    <span className="inline-flex items-center gap-1 rounded-full bg-destructive/15 px-2.5 py-0.5 text-xs font-medium text-destructive">
      <AlertTriangle className="h-3 w-3" />
      Bad
    </span>
  ) : (
    <span className="inline-block rounded-full bg-success/15 px-2.5 py-0.5 text-xs font-medium text-success">
      Healthy
    </span>
  );
}

export function ResultsTable({
  data,
  tone = "all",
}: {
  data: VMResult[];
  tone?: "all" | "bad" | "healthy";
}) {
  const [selectedVmId, setSelectedVmId] = useState<string | null>(null);
  const selectedRow = data.find((row) => row.server_id === selectedVmId) ?? null;

  const borderToneClass =
    tone === "bad"
      ? "border-destructive/40"
      : tone === "healthy"
        ? "border-success/40"
        : "border-border";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className={`overflow-hidden rounded-xl border bg-card ${borderToneClass}`}
      style={{ boxShadow: "var(--shadow-card)" }}
    >
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <h2 className="text-lg font-semibold font-[family-name:var(--font-display)] text-card-foreground">
          VM Analysis Results
        </h2>
        <span className="text-xs text-muted-foreground">
          {data.length} entries • Click a row for details
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-secondary/30">
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Server</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">VM Status</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                Current Region
              </th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Target</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">vCPU %</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">RAM (GB)</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Cost (₹)</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                Carbon (gCO2/kWh)
              </th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                Carbon Saving
              </th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">ML Status</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Action</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Savings (₹)</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Reason</th>
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 50).map((row, i) => (
              <tr
                key={i}
                className={`cursor-pointer border-b border-border/50 transition-colors hover:bg-secondary/20 ${selectedVmId === row.server_id ? "bg-secondary/30" : ""} ${row.vm_status === "Bad" ? "bg-destructive/5" : "bg-success/5"}`}
                onClick={() => setSelectedVmId(row.server_id)}
              >
                <td className="px-4 py-3 font-[family-name:var(--font-mono)] text-card-foreground">
                  {row.server_id}
                </td>
                <td className="px-4 py-3">
                  <VmStatusBadge status={row.vm_status} />
                </td>
                <td className="px-4 py-3 text-card-foreground">{row.region}</td>
                <td className="px-4 py-3 text-card-foreground">{row.target_region}</td>
                <td className="px-4 py-3 font-[family-name:var(--font-mono)] text-card-foreground">
                  {row.vcpu_usage.toFixed(1)}
                </td>
                <td className="px-4 py-3 font-[family-name:var(--font-mono)] text-card-foreground">
                  {row.ram_usage.toFixed(1)}
                </td>
                <td className="px-4 py-3 font-[family-name:var(--font-mono)] text-card-foreground">
                  ₹{row.cost.toFixed(2)}
                </td>
                <td className="px-4 py-3 font-[family-name:var(--font-mono)] text-card-foreground">
                  {row.carbon_intensity.toFixed(2)}
                </td>
                <td className="px-4 py-3 font-[family-name:var(--font-mono)] text-primary">
                  {Math.max(row.carbon_saving, 0).toFixed(2)}
                </td>
                <td className="px-4 py-3">
                  <AnomalyBadge anomaly={row.ml_anomaly} />
                </td>
                <td className="px-4 py-3">
                  <ActionBadge action={row.final_action} />
                </td>
                <td className="px-4 py-3 font-[family-name:var(--font-mono)] text-success">
                  ₹{row.estimated_savings.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{row.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selectedRow && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="border-t border-border bg-secondary/20 p-5"
        >
          <h3 className="text-sm font-semibold text-card-foreground">Recommendation Detail</h3>
          <div className="mt-3 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-5">
            <div className="rounded-lg border border-border/50 bg-background/40 p-3">
              <p className="text-xs text-muted-foreground">VM ID</p>
              <p className="mt-1 font-medium text-card-foreground">{selectedRow.server_id}</p>
            </div>
            <div className="rounded-lg border border-border/50 bg-background/40 p-3">
              <p className="text-xs text-muted-foreground">Current Region</p>
              <p className="mt-1 font-medium text-card-foreground">{selectedRow.region}</p>
            </div>
            <div className="rounded-lg border border-border/50 bg-background/40 p-3">
              <p className="text-xs text-muted-foreground">Target Region</p>
              <p className="mt-1 font-medium text-card-foreground">{selectedRow.target_region}</p>
            </div>
            <div className="rounded-lg border border-border/50 bg-background/40 p-3">
              <p className="text-xs text-muted-foreground">Carbon Reduction</p>
              <p className="mt-1 font-medium text-primary">
                {Math.max(selectedRow.carbon_saving, 0).toFixed(2)} gCO2/kWh
              </p>
            </div>
            <div className="rounded-lg border border-border/50 bg-background/40 p-3 sm:col-span-2 lg:col-span-1">
              <p className="text-xs text-muted-foreground">Reason</p>
              <p className="mt-1 font-medium text-card-foreground">{selectedRow.reason}</p>
            </div>
            <div className="rounded-lg border border-border/50 bg-background/40 p-3 sm:col-span-2 lg:col-span-1">
              <p className="text-xs text-muted-foreground">VM Status</p>
              <div className="mt-1">
                <VmStatusBadge status={selectedRow.vm_status} />
              </div>
            </div>
          </div>
        </motion.div>
      )}
      {data.length > 50 && (
        <div className="border-t border-border px-6 py-3 text-center text-xs text-muted-foreground">
          Showing 50 of {data.length} results
        </div>
      )}
    </motion.div>
  );
}
