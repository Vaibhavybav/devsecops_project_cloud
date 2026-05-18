// @lovable.dev/vite-tanstack-config already includes the TanStack Start, React,
// Tailwind, and tsconfig-paths plugins. Extend it here instead of adding them again.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  tanstackStart: {
    prerender: {
      enabled: true,
      autoSubfolderIndex: true,
      crawlLinks: true,
    },
  },
});
