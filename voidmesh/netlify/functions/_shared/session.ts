import type { VoidActor, VoidState } from "../../../src/shared/voidState";

const SESSION_TTL_SECONDS = 60 * 60 * 8;

type SessionClaims = {
  sub: string;
  admin: boolean;
  iat: number;
  exp: number;
};

export async function createSessionToken(actor: VoidActor): Promise<string> {
  const now = epochSeconds();
  const claims: SessionClaims = {
    sub: actor.citizenId,
    admin: actor.isAdmin,
    iat: now,
    exp: now + SESSION_TTL_SECONDS
  };
  const payload = base64UrlEncode(JSON.stringify(claims));
  return `${payload}.${await sign(payload)}`;
}

export async function actorFromSessionRequest(req: Request): Promise<VoidActor | null> {
  const token = bearerToken(req) || req.headers.get("x-void-session")?.trim() || "";
  if (!token) return null;

  const claims = await verifySessionToken(token);
  return { citizenId: claims.sub, isAdmin: claims.admin };
}

export async function verifySessionToken(token: string): Promise<SessionClaims> {
  const [payload, signature, extra] = token.split(".");
  if (!payload || !signature || extra) throw new Error("Void session token is malformed.");

  const expected = await sign(payload);
  if (!timingSafeEqual(signature, expected)) throw new Error("Void session token signature is invalid.");

  const claims = JSON.parse(base64UrlDecode(payload)) as Partial<SessionClaims>;
  if (!claims.sub || typeof claims.sub !== "string") throw new Error("Void session token is missing an actor.");
  if (typeof claims.exp !== "number" || claims.exp <= epochSeconds()) throw new Error("Void session token is expired.");

  return {
    sub: claims.sub,
    admin: claims.admin === true,
    iat: typeof claims.iat === "number" ? claims.iat : 0,
    exp: claims.exp
  };
}

export function assertSessionCitizen(state: VoidState, actor: VoidActor) {
  const citizen = state.citizens.find((entry) => entry.id === actor.citizenId && entry.status === "Active");
  if (!citizen) throw new Error("Void session actor is not an active citizen.");

  if (actor.isAdmin && !(citizen.titles.includes("Founder") || citizen.titles.includes("Admin"))) {
    throw new Error("Void admin session requires a Founder/Admin-titled citizen.");
  }
}

function bearerToken(req: Request) {
  const header = req.headers.get("authorization") || "";
  const [scheme, token] = header.split(" ");
  return scheme?.toLowerCase() === "bearer" ? token?.trim() || "" : "";
}

async function sign(payload: string) {
  const secret = sessionSecret();
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(payload));
  return base64UrlBytes(new Uint8Array(signature));
}

function sessionSecret() {
  const netlify = (globalThis as { Netlify?: { env?: { get(name: string): string | undefined } } }).Netlify;
  const secret = netlify?.env?.get("VOID_SESSION_SECRET") || process.env.VOID_SESSION_SECRET || "";
  if (!secret && !process.env.CONTEXT) return "void-local-private-preview-session-secret";
  if (!secret) throw new Error("VOID_SESSION_SECRET must be configured for deployed Void functions.");
  if (secret.length < 32) throw new Error("VOID_SESSION_SECRET must be configured with at least 32 characters.");
  return secret;
}

function timingSafeEqual(a: string, b: string) {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let index = 0; index < a.length; index += 1) {
    result |= a.charCodeAt(index) ^ b.charCodeAt(index);
  }
  return result === 0;
}

function base64UrlEncode(value: string) {
  return base64UrlBytes(new TextEncoder().encode(value));
}

function base64UrlDecode(value: string) {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(value.length / 4) * 4, "=");
  const binary = atob(base64);
  return new TextDecoder().decode(Uint8Array.from(binary, (char) => char.charCodeAt(0)));
}

function base64UrlBytes(bytes: Uint8Array) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function epochSeconds() {
  return Math.floor(Date.now() / 1000);
}
