import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  component: Index,
  head: () => ({
    meta: [
      { title: "Green FinOps — Cloud Cost & Carbon Optimization" },
      {
        name: "description",
        content: "ML-powered cloud cost optimization with carbon-aware recommendations.",
      },
    ],
  }),
});

function Index() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="text-center">
        <h1 className="bg-gradient-to-r from-primary to-chart-2 bg-clip-text text-5xl font-bold font-[family-name:var(--font-display)] text-transparent">
          Green FinOps
        </h1>
        <p className="mt-4 max-w-md text-muted-foreground">
          ML-powered cloud cost & carbon optimization platform
        </p>
        <a
          href="/login"
          className="mt-8 inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-medium text-primary-foreground transition-all hover:opacity-90"
          style={{ boxShadow: "var(--shadow-glow)" }}
        >
          Sign In →
        </a>
      </div>
    </div>
  );
}
