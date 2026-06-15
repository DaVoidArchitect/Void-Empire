import { createReadStream } from "node:fs";
import { access, stat } from "node:fs/promises";
import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { handleVoidApiRequest } from "./api";

const PORT = Number(process.env.PORT || 3000);
const HOST = process.env.HOST || "127.0.0.1";
const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const DIST_DIR = resolve(process.env.VOID_DIST_DIR || join(ROOT, "dist"));
const INDEX_FILE = join(DIST_DIR, "index.html");
const MAX_STATIC_BYTES = 1024 * 1024 * 20;

const server = createServer(async (req, res) => {
  try {
    await handleRequest(req, res);
  } catch {
    sendText(res, 500, "Void server request failed.");
  }
});

server.listen(PORT, HOST, () => {
  console.log(`Void VPS server listening at http://${HOST}:${PORT}`);
});

async function handleRequest(req: IncomingMessage, res: ServerResponse) {
  const url = new URL(req.url || "/", `http://${req.headers.host || `${HOST}:${PORT}`}`);

  if (url.pathname === "/healthz") {
    const response = await handleVoidApiRequest(new Request(new URL("/api/void/health", url).toString(), { method: "GET", headers: requestHeaders(req) }));
    await writeWebResponse(res, response);
    return;
  }

  if (url.pathname === "/api/void" || url.pathname.startsWith("/api/void/")) {
    const response = await handleVoidApiRequest(toWebRequest(req, url));
    await writeWebResponse(res, response);
    return;
  }

  if (req.method !== "GET" && req.method !== "HEAD") {
    sendText(res, 405, "Method not allowed.");
    return;
  }

  await serveStatic(req, res, url);
}

function toWebRequest(req: IncomingMessage, url: URL) {
  const init: RequestInit & { duplex?: "half" } = {
    method: req.method || "GET",
    headers: requestHeaders(req)
  };

  if (req.method && !["GET", "HEAD"].includes(req.method)) {
    init.body = req as unknown as BodyInit;
    init.duplex = "half";
  }

  return new Request(url.toString(), init);
}

function requestHeaders(req: IncomingMessage) {
  const headers = new Headers();
  for (const [key, value] of Object.entries(req.headers)) {
    if (Array.isArray(value)) {
      for (const item of value) headers.append(key, item);
    } else if (value !== undefined) {
      headers.set(key, String(value));
    }
  }
  headers.set("x-void-client-ip", req.socket.remoteAddress || "direct-local");
  return headers;
}

async function writeWebResponse(res: ServerResponse, response: Response) {
  res.statusCode = response.status;
  response.headers.forEach((value, key) => res.setHeader(key, value));
  applySecurityHeaders(res);
  const body = Buffer.from(await response.arrayBuffer());
  res.end(body);
}

async function serveStatic(req: IncomingMessage, res: ServerResponse, url: URL) {
  const pathname = decodeURIComponent(url.pathname);
  const requestedPath = pathname === "/" ? INDEX_FILE : resolve(DIST_DIR, normalize(pathname).replace(/^([/\\])+/, ""));
  const filePath = await safeStaticPath(requestedPath, pathname);
  const fileStat = await stat(filePath).catch(() => null);

  if (!fileStat?.isFile() || fileStat.size > MAX_STATIC_BYTES) {
    sendText(res, 404, "Not found.");
    return;
  }

  res.statusCode = 200;
  res.setHeader("Content-Type", mimeType(filePath));
  res.setHeader("Cache-Control", cacheHeader(filePath));
  applySecurityHeaders(res);

  if (req.method === "HEAD") {
    res.end();
    return;
  }

  createReadStream(filePath)
    .on("error", () => sendText(res, 500, "Static asset failed."))
    .pipe(res);
}

async function safeStaticPath(requestedPath: string, pathname: string) {
  const resolved = resolve(requestedPath);
  const insideDist = resolved === DIST_DIR || resolved.startsWith(`${DIST_DIR}\\`) || resolved.startsWith(`${DIST_DIR}/`);
  if (!insideDist) return INDEX_FILE;

  try {
    await access(resolved);
    return resolved;
  } catch {
    return extname(pathname) ? resolved : INDEX_FILE;
  }
}

function sendText(res: ServerResponse, status: number, text: string) {
  if (res.headersSent) {
    res.end();
    return;
  }

  res.statusCode = status;
  res.setHeader("Content-Type", "text/plain; charset=utf-8");
  applySecurityHeaders(res);
  res.end(text);
}

function applySecurityHeaders(res: ServerResponse) {
  res.setHeader("X-Frame-Options", "DENY");
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");
  res.setHeader("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
  res.setHeader("Content-Security-Policy", "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; form-action 'self'");
}

function cacheHeader(filePath: string) {
  return filePath.includes(`${DIST_DIR}${separator()}assets${separator()}`)
    ? "public, max-age=31536000, immutable"
    : "no-store";
}

function separator() {
  return process.platform === "win32" ? "\\" : "/";
}

function mimeType(filePath: string) {
  switch (extname(filePath).toLowerCase()) {
    case ".html":
      return "text/html; charset=utf-8";
    case ".js":
      return "text/javascript; charset=utf-8";
    case ".css":
      return "text/css; charset=utf-8";
    case ".json":
      return "application/json; charset=utf-8";
    case ".png":
      return "image/png";
    case ".jpg":
    case ".jpeg":
      return "image/jpeg";
    case ".svg":
      return "image/svg+xml";
    case ".webp":
      return "image/webp";
    case ".ico":
      return "image/x-icon";
    default:
      return "application/octet-stream";
  }
}
