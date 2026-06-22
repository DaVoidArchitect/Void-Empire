import { createHmac, randomBytes, timingSafeEqual } from "node:crypto";
import type { VoidActor } from "../src/shared/voidState";
import { readCredentials, writeCredentials, type ActiveCredential, type CredentialState } from "./fileStore";

const SESSION_TTL_SECONDS = 60 * 60 * 8;

type SessionClaims = {
  sub: string;
  admin: boolean;
  iat: number;
  exp: number;
};

export type VoidSession = {
  token: string;
  citizenId: string;
  email: string;
  expiresAt: string;
};

export async function stageActivationCredential(requestId: string, email: string, phrase: string) {
  assertPhrase(phrase);
  const credentials = await readCredentials();
  credentials.pending[requestId] = {
    requestId,
    email: normalizeEmail(email),
    ...hashPhrase(phrase),
    createdAt: new Date().toISOString()
  };
  await writeCredentials(credentials);
}

export async function registerCitizenCredential(citizenId: string, email: string, phrase: string) {
  assertPhrase(phrase);
  const normalizedEmail = normalizeEmail(email);
  const credentials = await readCredentials();
  credentials.activeByEmail[normalizedEmail] = {
    citizenId,
    email: normalizedEmail,
    ...hashPhrase(phrase),
    activatedAt: new Date().toISOString()
  };
  for (const [requestId, pending] of Object.entries(credentials.pending)) {
    if (pending.email === normalizedEmail) delete credentials.pending[requestId];
  }
  delete credentials.attemptsByEmail[normalizedEmail];
  await writeCredentials(credentials);
}

export async function activateCredentialForRequest(requestId: string, citizenId: string) {
  const credentials = await readCredentials();
  const pending = credentials.pending[requestId];
  if (!pending) return;

  credentials.activeByEmail[pending.email] = {
    citizenId,
    email: pending.email,
    salt: pending.salt,
    hash: pending.hash,
    activatedAt: new Date().toISOString()
  };
  delete credentials.pending[requestId];
  await writeCredentials(credentials);
}

export async function createCitizenSession(email: string, phrase: string): Promise<VoidSession> {
  const credentials = await readCredentials();
  const normalizedEmail = normalizeEmail(email);
  assertNotLocked(credentials, normalizedEmail);

  const credential = credentials.activeByEmail[normalizedEmail];
  if (!credential || !verifyPhrase(phrase, credential)) {
    await recordFailedAttempt(credentials, normalizedEmail);
    throw new Error("Citizen session credentials are invalid or not registered.");
  }

  delete credentials.attemptsByEmail[normalizedEmail];
  await writeCredentials(credentials);

  const token = createSessionToken({ citizenId: credential.citizenId, isAdmin: false });
  const claims = verifySessionToken(token);

  return {
    token,
    citizenId: credential.citizenId,
    email: credential.email,
    expiresAt: new Date(claims.exp * 1000).toISOString()
  };
}

export async function verifyCitizenSession(token: string): Promise<VoidSession | null> {
  try {
    const claims = verifySessionToken(token);
    const credentials = await readCredentials();
    const credential = Object.values(credentials.activeByEmail).find((entry) => entry.citizenId === claims.sub);
    if (!credential) return null;
    return {
      token,
      citizenId: claims.sub,
      email: credential.email,
      expiresAt: new Date(claims.exp * 1000).toISOString()
    };
  } catch {
    return null;
  }
}

export function actorFromSessionRequest(req: Request): VoidActor | null {
  const token = bearerToken(req) || req.headers.get("x-void-session")?.trim() || "";
  if (!token) return null;

  const claims = verifySessionToken(token);
  return { citizenId: claims.sub, isAdmin: claims.admin };
}

function createSessionToken(actor: VoidActor): string {
  const now = epochSeconds();
  const claims: SessionClaims = {
    sub: actor.citizenId,
    admin: actor.isAdmin,
    iat: now,
    exp: now + SESSION_TTL_SECONDS
  };
  const payload = Buffer.from(JSON.stringify(claims), "utf8").toString("base64url");
  return `${payload}.${sign(payload)}`;
}

function verifySessionToken(token: string): SessionClaims {
  const [payload, signature, extra] = token.split(".");
  if (!payload || !signature || extra) throw new Error("Void session token is malformed.");

  const expected = sign(payload);
  if (!safeEqual(signature, expected)) throw new Error("Void session token signature is invalid.");

  const claims = JSON.parse(Buffer.from(payload, "base64url").toString("utf8")) as Partial<SessionClaims>;
  if (!claims.sub || typeof claims.sub !== "string") throw new Error("Void session token is missing an actor.");
  if (typeof claims.exp !== "number" || claims.exp <= epochSeconds()) throw new Error("Void session token is expired.");

  return {
    sub: claims.sub,
    admin: claims.admin === true,
    iat: typeof claims.iat === "number" ? claims.iat : 0,
    exp: claims.exp
  };
}

function assertNotLocked(credentials: CredentialState, email: string) {
  const attempt = credentials.attemptsByEmail[email];
  if (!attempt?.lockedUntil) return;
  if (new Date(attempt.lockedUntil).getTime() <= Date.now()) {
    delete credentials.attemptsByEmail[email];
    return;
  }
  throw new Error("Citizen session is temporarily locked after repeated failed attempts.");
}

async function recordFailedAttempt(credentials: CredentialState, email: string) {
  const current = credentials.attemptsByEmail[email];
  const count = (current?.count || 0) + 1;
  credentials.attemptsByEmail[email] = {
    count,
    lockedUntil: count >= 5 ? new Date(Date.now() + 1000 * 60 * 10).toISOString() : null,
    updatedAt: new Date().toISOString()
  };
  await writeCredentials(credentials);
}

function hashPhrase(phrase: string, salt = randomBytes(16).toString("base64url")) {
  return {
    salt,
    hash: createHmac("sha256", sessionSecret()).update(`${salt}:${phrase}`).digest("base64url")
  };
}

function verifyPhrase(phrase: string, credential: Pick<ActiveCredential, "salt" | "hash">) {
  const candidate = hashPhrase(phrase, credential.salt).hash;
  return safeEqual(candidate, credential.hash);
}

function sign(payload: string) {
  return createHmac("sha256", sessionSecret()).update(payload).digest("base64url");
}

function safeEqual(a: string, b: string) {
  const left = Buffer.from(a);
  const right = Buffer.from(b);
  return left.length === right.length && timingSafeEqual(left, right);
}

function assertPhrase(phrase: string) {
  if (!phrase || phrase.length < 12) {
    throw new Error("Private account phrase must be at least 12 characters.");
  }
}

function normalizeEmail(email: string) {
  const value = email.trim().toLowerCase();
  if (!value.includes("@")) throw new Error("A valid email is required.");
  return value;
}

function bearerToken(req: Request) {
  const header = req.headers.get("authorization") || "";
  const [scheme, token] = header.split(" ");
  return scheme?.toLowerCase() === "bearer" ? token?.trim() || "" : "";
}

function sessionSecret() {
  const configured = process.env.VOID_SESSION_SECRET || "";
  if (configured.length >= 32) return configured;
  if (process.env.NODE_ENV === "production") {
    throw new Error("VOID_SESSION_SECRET must be configured with at least 32 characters.");
  }
  return "void-local-private-preview-session-secret";
}

function epochSeconds() {
  return Math.floor(Date.now() / 1000);
}
