import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, LockKeyhole, Leaf, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { setAuthToken } from "@/lib/auth";

export const Route = createFileRoute("/login")({
  component: LoginPage,
  head: () => ({
    meta: [
      { title: "Login — Green FinOps" },
      { name: "description", content: "Login to access the Green FinOps dashboard." },
    ],
  }),
});

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? "http://127.0.0.1:8000" : "/api");
const LOGIN_ENDPOINT = `${API_BASE_URL.replace(/\/$/, "")}/login`;

function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(LOGIN_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || `Login failed: ${response.status}`);
      }

      const payload = await response.json();
      if (!payload?.access_token) {
        throw new Error("Login succeeded but no access token was returned.");
      }

      setAuthToken(payload.access_token);
      void navigate({ to: "/dashboard" });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background px-4 py-10">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground">
            <Leaf className="h-3.5 w-3.5 text-primary" />
            Secure access for carbon-aware optimization
          </div>
          <div className="space-y-4">
            <h1 className="max-w-xl text-4xl font-bold font-[family-name:var(--font-display)] text-foreground sm:text-5xl">
              Sign in to the Green FinOps dashboard
            </h1>
            <p className="max-w-xl text-base text-muted-foreground">
              Use your credentials to access the real-time carbon recommendations, VM health
              insights, and protected prediction API.
            </p>
          </div>
          <div className="grid gap-3 text-sm text-muted-foreground sm:grid-cols-2">
            <div
              className="rounded-xl border border-border bg-card p-4"
              style={{ boxShadow: "var(--shadow-card)" }}
            >
              <p className="font-medium text-foreground">JWT protected</p>
              <p className="mt-1">
                Tokens are stored locally and sent as Bearer auth to the backend.
              </p>
            </div>
            <div
              className="rounded-xl border border-border bg-card p-4"
              style={{ boxShadow: "var(--shadow-card)" }}
            >
              <p className="font-medium text-foreground">Real-time carbon</p>
              <p className="mt-1">Dashboard uses live Electricity Maps data after login.</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-border/80 bg-card/95 backdrop-blur">
            <CardHeader>
              <div className="mb-2 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <LockKeyhole className="h-6 w-6" />
              </div>
              <CardTitle className="text-2xl font-[family-name:var(--font-display)]">
                Login
              </CardTitle>
              <CardDescription>Enter the admin credentials to continue.</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={handleSubmit}>
                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    autoComplete="username"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    autoComplete="current-password"
                  />
                </div>

                {error && (
                  <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                    {error}
                  </div>
                )}

                <Button type="submit" className="w-full gap-2" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Signing in...
                    </>
                  ) : (
                    <>
                      Enter Dashboard
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
