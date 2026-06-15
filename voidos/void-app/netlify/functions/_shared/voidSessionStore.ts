import { createHmac, randomBytes, timingSafeEqual } from "node:crypto";
import { getStore } from "@netlify/blobs";
import { createSessionToken, verifySessionToken } from "./session";
import { readJsonRecord, writeJsonRecord } from "./supabaseStore";

const STORE_NAME = "void-private-auth";
const CREDENTIALS_KEY = "citizen-credentials";
const DATABASE_CREDENTIALS_KEY = "citizen_credentials";

type PendingCredential = {
  requestId: string;
  email: string;
  salt: string;
  hash: string;
  createdAt: string;
};

type ActiveCredential = {
  citizenId: string;
  email: string;
  salt: string;
  hash: string;
  activatedAt: string;
};

type CredentialState = {
  pending: Record<string, PendingCredential>;
  activeByEmail: Record<string, ActiveCredential>;
  attemptsByEmail: Record<string, { count: number; lockedUntil: string | null; updatedAt: string }>;
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

  const token = await createSessionToken({ citizenId: credential.citizenId, isAdmin: false });
  const claims = await verifySessionToken(token);

  return {
    token,
    citizenId: credential.citizenId,
    email: credential.email,
    expiresAt: new Date(claims.exp * 1000).toISOString()
  };
}

export async function verifyCitizenSession(token: string): Promise<VoidSession | null> {
  try {
    const claims = await verifySessionToken(token);
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

async function readCredentials(): Promise<CredentialState> {
  const databaseCredentials = await readJsonRecord<CredentialState>(DATABASE_CREDENTIALS_KEY);
  if (databaseCredentials) return normalizeCredentials(databaseCredentials);

  const store = getStore({ name: STORE_NAME, consistency: "strong" });
  const saved = await store.get(CREDENTIALS_KEY, { type: "json" }).catch(() => null) as CredentialState | null;
  return normalizeCredentials(saved);
}

async function writeCredentials(credentials: CredentialState) {
  if (await writeJsonRecord(DATABASE_CREDENTIALS_KEY, credentials)) return;

  const store = getStore({ name: STORE_NAME, consistency: "strong" });
  await store.setJSON(CREDENTIALS_KEY, credentials);
}

function normalizeCredentials(value: CredentialState | null | undefined): CredentialState {
  return {
    pending: value?.pending && typeof value.pending === "object" ? value.pending : {},
    activeByEmail: value?.activeByEmail && typeof value.activeByEmail === "object" ? value.activeByEmail : {},
    attemptsByEmail: value?.attemptsByEmail && typeof value.attemptsByEmail === "object" ? value.attemptsByEmail : {}
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

function verifyPhrase(phrase: string, credential: { salt: string; hash: string }) {
  const candidate = hashPhrase(phrase, credential.salt).hash;
  return safeEqual(candidate, credential.hash);
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

function sessionSecret() {
  const configured = getEnv("VOID_SESSION_SECRET");
  if (configured) return configured;
  if (getEnv("CONTEXT")) {
    throw new Error("VOID_SESSION_SECRET is required for deployed Void functions.");
  }
  return "void-local-private-preview-session-secret";
}

function getEnv(name: string) {
  const netlifyEnv = globalThis as typeof globalThis & { Netlify?: { env?: { get: (key: string) => string | undefined } } };
  return netlifyEnv.Netlify?.env?.get(name) || process.env[name] || "";
}
