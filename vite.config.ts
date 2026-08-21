// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - tanstackStart, viteReact, tailwindcss, tsConfigPaths, cloudflare (build-only),
//     componentTagger (dev-only), VITE_* env injection, @ path alias, React/TanStack dedupe,
//     error logger plugins, and sandbox detection (port/host/strictPort).
// You can pass additional config via defineConfig({ vite: { ... } }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

// Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
// @cloudflare/vite-plugin builds from this — wrangler.jsonc main alone is insufficient.
export default defineConfig({
  tanstackStart: {
    server: { entry: "server" },
  },
  vite: {
    build: {
      cssCodeSplit: false,
    },
    plugins: [
      {
        name: "fix-vite7-css-post",
        enforce: "pre",
        configResolved(resolvedConfig) {
          const plugins = resolvedConfig.plugins as any[];
          const cssPost = plugins.find((p) => p.name === "vite:css-post");
          if (cssPost && cssPost.renderChunk) {
            const orig = cssPost.renderChunk;
            cssPost.renderChunk = function (code, chunk, opts) {
              try {
                return orig.call(this, code, chunk, opts);
              } catch (e) {
                return { code: code || "/* empty */", map: null };
              }
            };
          }
        },
      },
    ],
  },
});
