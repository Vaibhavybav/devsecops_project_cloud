import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Papa from "papaparse";
import { Loader2, Download, Leaf } from "lucide-react";
import { Button } from "@/components/ui/button";
import { InputSection } from "@/components/dashboard/InputSection";
import { SummaryCards } from "@/components/dashboard/SummaryCards";
import { ResultsTable } from "@/components/dashboard/ResultsTable";
import { Visualizations } from "@/components/dashboard/Visualizations";
import { InsightsPanel } from "@/components/dashboard/InsightsPanel";
import { buildApiUrl } from "@/lib/api";
import { getAuthToken, clearAuthToken } from "@/lib/auth";
import type { VMResult, DashboardSummary } from "@/types/dashboard";

export const Route = createFileRoute("/dashboard")({
  component: DashboardPage,
  head: () => ({
    meta: [
      { title: "Dashboard — Green FinOps" },
      {
        name: "description",
        content:
          "Analyze VM usage, detect anomalies, and optimize cloud costs with carbon awareness.",
      },
    ],
  }),
});

const PREDICT_ENDPOINT = buildApiUrl("/predict");

function generateSampleData(count = 25): { vcpu_usage: number; ram_usage: number }[] {
  return Array.from({ length: count }, () => ({
    vcpu_usage: Math.round(Math.random() * 100 * 10) / 10,
    ram_usage: Math.round((1 + Math.random() * 63) * 10) / 10,
  }));
}

function computeSummary(data: VMResult[]): DashboardSummary {
  const moveRecommendations = data.filter((r) =>
    r.final_action.toLowerCase().startsWith("move from "),
  );
  const regionCarbonAgg = new Map<string, { total: number; count: number }>();

  data.forEach((row) => {
    const current = regionCarbonAgg.get(row.region) ?? { total: 0, count: 0 };
    current.total += row.carbon_intensity;
    current.count += 1;
    regionCarbonAgg.set(row.region, current);
  });

  let highestCarbonRegion = "N/A";
  let highestAverage = -1;
  regionCarbonAgg.forEach((value, region) => {
    const average = value.total / value.count;
    if (average > highestAverage) {
      highestAverage = average;
      highestCarbonRegion = region;
    }
  });

  return {
    totalVMs: data.length,
    anomalies: data.filter((r) => r.ml_anomaly === 1).length,
    migrationRecs: moveRecommendations.length,
    totalSavings: data.reduce((sum, r) => sum + r.estimated_savings, 0),
    totalCarbonReduction: moveRecommendations.reduce(
      (sum, r) => sum + Math.max(r.carbon_saving, 0),
      0,
    ),
    highestCarbonRegion,
    healthyVMs: data.filter((r) => r.vm_status === "Healthy").length,
    badVMs: data.filter((r) => r.vm_status === "Bad").length,
  };
}

type VmFilter = "all" | "bad" | "healthy";

function downloadCSV(data: VMResult[]) {
  const csv = Papa.unparse(data);
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "green_finops_results.csv";
  a.click();
  URL.revokeObjectURL(url);
}

function downloadSampleCSV() {
  const sample = generateSampleData(10);
  const csv = Papa.unparse(sample);
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sample_vm_data.csv";
  a.click();
  URL.revokeObjectURL(url);
}

function DashboardPage() {
  const navigate = useNavigate();
  const [inputData, setInputData] = useState<{ vcpu_usage: number; ram_usage: number }[] | null>(
    null,
  );
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [results, setResults] = useState<VMResult[] | null>(null);
  const [vmFilter, setVmFilter] = useState<VmFilter>("all");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingHint, setLoadingHint] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getAuthToken()) {
      void navigate({ to: "/login" });
    }
  }, [navigate]);

  const handleFileUpload = useCallback((file: File) => {
    Papa.parse(file, {
      header: true,
      dynamicTyping: true,
      complete: (result) => {
        const parsed = result.data as { vcpu_usage: number; ram_usage: number }[];
        const valid = parsed.filter((r) => r.vcpu_usage != null && r.ram_usage != null);
        setInputData(valid);
        setUploadedFile(file);
        setResults(null);
        setVmFilter("all");
        setError(null);
      },
      error: () => setError("Failed to parse CSV file"),
    });
  }, []);

  const handleGenerateSample = useCallback(() => {
    const data = generateSampleData();
    setInputData(data);
    setUploadedFile(null);
    setResults(null);
    setVmFilter("all");
    setError(null);
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (!inputData || inputData.length === 0) return;
    setIsLoading(true);
    setLoadingHint("Fetching real-time carbon data...");
    setError(null);

    const controller = new AbortController();
    const slowHintTimer = window.setTimeout(() => {
      setLoadingHint("Live carbon signals are taking longer than usual. Still working...");
    }, 6000);
    const timeoutTimer = window.setTimeout(() => {
      controller.abort();
    }, 30000);

    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("Session expired. Please sign in again.");
      }

      const formData = new FormData();
      if (uploadedFile) {
        formData.append("file", uploadedFile);
      } else {
        const csv = Papa.unparse(inputData);
        const blob = new Blob([csv], { type: "text/csv" });
        formData.append("file", blob, "vm_input.csv");
      }

      const res = await fetch(PREDICT_ENDPOINT, {
        method: "POST",
        body: formData,
        headers: {
          Authorization: `Bearer ${token}`,
        },
        signal: controller.signal,
      });
      if (!res.ok) {
        if (res.status === 401) {
          clearAuthToken();
          void navigate({ to: "/login" });
          throw new Error("Your session expired. Please sign in again.");
        }
        const errorPayload = await res.json().catch(() => null);
        throw new Error(errorPayload?.detail || `API error: ${res.status}`);
      }
      const data = await res.json();
      setResults(Array.isArray(data) ? data : data.results || data.predictions || [data]);
      setVmFilter("all");
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setError("API timeout while waiting for real-time carbon data. Please retry.");
      } else {
        setError(err instanceof Error ? err.message : "Failed to connect to API");
      }
    } finally {
      window.clearTimeout(slowHintTimer);
      window.clearTimeout(timeoutTimer);
      setLoadingHint(null);
      setIsLoading(false);
    }
  }, [inputData, navigate, uploadedFile]);

  const summary = results ? computeSummary(results) : null;
  const badVMs = (results ?? []).filter((row) => row.vm_status === "Bad");
  const healthyVMs = (results ?? []).filter((row) => row.vm_status === "Healthy");

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary/10 p-2">
              <Leaf className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-lg font-bold font-[family-name:var(--font-display)] text-foreground">
                Green FinOps
              </h1>
              <p className="text-xs text-muted-foreground">Cloud Cost & Carbon Optimizer</p>
            </div>
          </div>
          {results && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => downloadCSV(results)}
              className="gap-2"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </Button>
          )}
        </div>
      </header>

      {/* Content */}
      <main className="mx-auto max-w-7xl space-y-6 px-6 py-8">
        <InputSection
          onFileUpload={handleFileUpload}
          onGenerateSample={handleGenerateSample}
          onDownloadSample={downloadSampleCSV}
          isLoading={isLoading}
        />

        {/* Data loaded indicator + Analyze */}
        {inputData && !results && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center gap-4 rounded-xl border border-border bg-card p-8"
            style={{ boxShadow: "var(--shadow-card)" }}
          >
            <p className="text-sm text-muted-foreground">
              {inputData.length} VMs loaded and ready for analysis
            </p>
            <Button
              size="lg"
              onClick={handleAnalyze}
              disabled={isLoading}
              className="gap-2 px-8 text-base"
              style={{ boxShadow: "var(--shadow-glow)" }}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Analyzing…
                </>
              ) : (
                "🔍 Analyze"
              )}
            </Button>
            {isLoading && loadingHint && (
              <p className="text-xs text-muted-foreground">{loadingHint}</p>
            )}
          </motion.div>
        )}

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-center text-sm text-destructive"
            >
              ⚠️ {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        {results && summary && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <SummaryCards summary={summary} />
            <Visualizations data={results} />
            <InsightsPanel summary={summary} data={results} />

            <div
              className="rounded-xl border border-border bg-card p-4"
              style={{ boxShadow: "var(--shadow-card)" }}
            >
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant={vmFilter === "all" ? "default" : "outline"}
                  onClick={() => setVmFilter("all")}
                >
                  Show All
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={vmFilter === "bad" ? "default" : "outline"}
                  onClick={() => setVmFilter("bad")}
                >
                  Show Bad Only
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={vmFilter === "healthy" ? "default" : "outline"}
                  onClick={() => setVmFilter("healthy")}
                >
                  Show Healthy Only
                </Button>
              </div>
            </div>

            {(vmFilter === "all" || vmFilter === "bad") && (
              <section className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-2.5 w-2.5 rounded-full bg-destructive" />
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-destructive">
                    Bad VMs (High Priority)
                  </h3>
                  <span className="text-xs text-muted-foreground">{badVMs.length} entries</span>
                </div>
                <ResultsTable data={badVMs} tone="bad" />
              </section>
            )}

            {(vmFilter === "all" || vmFilter === "healthy") && (
              <section className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-2.5 w-2.5 rounded-full bg-success" />
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-success">
                    Healthy VMs
                  </h3>
                  <span className="text-xs text-muted-foreground">{healthyVMs.length} entries</span>
                </div>
                <ResultsTable data={healthyVMs} tone="healthy" />
              </section>
            )}
          </motion.div>
        )}
      </main>
    </div>
  );
}
