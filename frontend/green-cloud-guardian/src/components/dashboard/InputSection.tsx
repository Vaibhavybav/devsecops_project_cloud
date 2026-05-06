import { useRef } from "react";
import { motion } from "framer-motion";
import { Upload, Sparkles, Download } from "lucide-react";
import { Button } from "@/components/ui/button";

interface InputSectionProps {
  onFileUpload: (file: File) => void;
  onGenerateSample: () => void;
  onDownloadSample: () => void;
  isLoading: boolean;
}

export function InputSection({
  onFileUpload,
  onGenerateSample,
  onDownloadSample,
  isLoading,
}: InputSectionProps) {
  const fileRef = useRef<HTMLInputElement>(null);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="rounded-xl border border-border bg-card p-6"
      style={{ boxShadow: "var(--shadow-card)" }}
    >
      <h2 className="mb-4 text-lg font-semibold font-[family-name:var(--font-display)] text-card-foreground">
        Data Input
      </h2>
      <div className="grid gap-4 sm:grid-cols-3">
        {/* Upload CSV */}
        <button
          onClick={() => fileRef.current?.click()}
          disabled={isLoading}
          className="group flex flex-col items-center gap-3 rounded-lg border border-dashed border-border bg-secondary/50 p-6 transition-all hover:border-primary hover:bg-secondary disabled:opacity-50"
        >
          <div className="rounded-full bg-primary/10 p-3 transition-colors group-hover:bg-primary/20">
            <Upload className="h-5 w-5 text-primary" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-card-foreground">Upload CSV</p>
            <p className="mt-1 text-xs text-muted-foreground">vcpu_usage, ram_usage</p>
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) onFileUpload(file);
            }}
          />
        </button>

        {/* Generate Sample */}
        <button
          onClick={onGenerateSample}
          disabled={isLoading}
          className="group flex flex-col items-center gap-3 rounded-lg border border-dashed border-border bg-secondary/50 p-6 transition-all hover:border-primary hover:bg-secondary disabled:opacity-50"
        >
          <div className="rounded-full bg-primary/10 p-3 transition-colors group-hover:bg-primary/20">
            <Sparkles className="h-5 w-5 text-primary" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-card-foreground">Generate Sample</p>
            <p className="mt-1 text-xs text-muted-foreground">Random VM data</p>
          </div>
        </button>

        {/* Download Sample */}
        <button
          onClick={onDownloadSample}
          disabled={isLoading}
          className="group flex flex-col items-center gap-3 rounded-lg border border-dashed border-border bg-secondary/50 p-6 transition-all hover:border-primary hover:bg-secondary disabled:opacity-50"
        >
          <div className="rounded-full bg-primary/10 p-3 transition-colors group-hover:bg-primary/20">
            <Download className="h-5 w-5 text-primary" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-card-foreground">Download Sample</p>
            <p className="mt-1 text-xs text-muted-foreground">Example CSV file</p>
          </div>
        </button>
      </div>
    </motion.div>
  );
}
