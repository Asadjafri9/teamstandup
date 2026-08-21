import { createServer } from "node:http";
import { readFile, readdir, stat } from "node:fs/promises";
import { join, extname, normalize } from "node:path";
import ssrServer from "./dist/server/server.js";

const PORT = process.env.PORT || 8080;
const API_PORT = 8001;
const API_BASE = `http://localhost:${API_PORT}`;
const STATIC_DIR = "/app/dist/client";

// Find the CSS file at startup
let cssFilePath = "";
try {
  const assetsDir = join(STATIC_DIR, "assets");
  console.log(`Looking for CSS in: ${assetsDir}`);
  const files = await readdir(assetsDir);
  console.log(`Files in assets: ${files.join(", ")}`);
  const cssFile = files.find((f) => f.endsWith(".css"));
  if (cssFile) {
    cssFilePath = `/assets/${cssFile}`;
    console.log(`Found CSS: ${cssFilePath}`);
  } else {
    console.log("No CSS file found in assets directory");
  }
} catch (e) {
  console.log(`Error finding CSS: ${e.message}`);
}

const MIME_TYPES = {
  ".js": "application/javascript",
  ".css": "text/css",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".json": "application/json",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".eot": "application/vnd.ms-fontobject",
  ".otf": "font/otf",
  ".webp": "image/webp",
  ".avif": "image/avif",
  ".wasm": "application/wasm",
};

async function serveStatic(req, res) {
  const pathname = normalize(new URL(req.url, `http://localhost`).pathname);
  const filePath = join(STATIC_DIR, pathname);

  // Prevent path traversal
  if (!filePath.startsWith(STATIC_DIR)) {
    return false;
  }

  try {
    const stats = await stat(filePath);
    if (stats.isFile()) {
      const data = await readFile(filePath);
      const ext = extname(filePath).toLowerCase();
      const contentType = MIME_TYPES[ext] || "application/octet-stream";
      res.writeHead(200, {
        "content-type": contentType,
        "content-length": stats.size,
        "cache-control": "public, max-age=31536000, immutable",
      });
      res.end(data);
      return true;
    }
  } catch {
    // File not found, fall through to SSR
  }
  return false;
}

const server = createServer(async (req, res) => {
  // Proxy /api requests to the Python backend
  if (req.url.startsWith("/api/")) {
    try {
      const url = new URL(req.url, API_BASE);
      const headers = { ...req.headers, host: `localhost:${API_PORT}` };
      
      // Collect request body for POST/PUT
      const chunks = [];
      for await (const chunk of req) chunks.push(chunk);
      const body = chunks.length > 0 ? Buffer.concat(chunks) : undefined;
      
      const apiRes = await fetch(url, {
        method: req.method,
        headers,
        body: body ? body : undefined,
        redirect: "manual",
      });
      
      const apiHeaders = Object.fromEntries(apiRes.headers.entries());
      delete apiHeaders["transfer-encoding"];
      delete apiHeaders["content-encoding"];
      
      const apiBody = Buffer.from(await apiRes.arrayBuffer());
      res.writeHead(apiRes.status, apiHeaders);
      res.end(apiBody);
    } catch (err) {
      console.error("API proxy error:", err);
      res.writeHead(502, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: "Backend unavailable" }));
    }
    return;
  }

  // Try to serve static files first (CSS, JS, images, etc.)
  if (await serveStatic(req, res)) {
    return;
  }

  // Forward all other requests to the SSR server
  try {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    const headers = new Headers();
    for (const [key, value] of Object.entries(req.headers)) {
      if (Array.isArray(value)) {
        value.forEach((v) => headers.append(key, v));
      } else if (value) {
        headers.set(key, value);
      }
    }

    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const body = chunks.length > 0 ? Buffer.concat(chunks) : undefined;

    const init = {
      method: req.method,
      headers,
      body: body ? body : undefined,
    };

    const response = await ssrServer.fetch(new Request(url, init), {}, { waitUntil: async (p) => p });
    
    const responseHeaders = {};
    response.headers.forEach((value, key) => {
      responseHeaders[key] = value;
    });
    delete responseHeaders["transfer-encoding"];
    delete responseHeaders["content-encoding"];

    let responseBody = Buffer.from(await response.arrayBuffer());

    // Replace VITE_CSS_URL placeholder with actual CSS path
    if (cssFilePath) {
      responseBody = Buffer.from(
        responseBody.toString().replace(
          /__VITE_CSS_URL__[a-f0-9]+__/g,
          cssFilePath
        )
      );
    }

    res.writeHead(response.status, responseHeaders);
    res.end(responseBody);
  } catch (err) {
    console.error("SSR error:", err);
    res.writeHead(500, { "content-type": "text/html" });
    res.end("<h1>Server Error</h1><p>Failed to render page.</p>");
  }
});

server.listen(PORT, () => {
  console.log(`Server running on http://0.0.0.0:${PORT}`);
  console.log(`API proxying to http://localhost:${API_PORT}`);
});
