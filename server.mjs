import { createServer } from "node:http";
import ssrServer from "./dist/server/server.js";

const PORT = process.env.PORT || 8080;
const API_PORT = 8001;
const API_BASE = `http://localhost:${API_PORT}`;

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
      // Remove transfer-encoding since we'll set content-length
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

    const responseBody = Buffer.from(await response.arrayBuffer());
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
