import { applyVoidApiAction, authorizeVoidApiAction, pulseSafetyNotice, type VoidActor, type VoidApiAction, type VoidState } from "../src/shared/voidState";
import type { CitizenType, FeedbackScope, ListingCategory } from "../src/state/types";
import { dataStoreInfo, readVoidState, writeVoidState } from "./fileStore";
import { activateCredentialForRequest, actorFromSessionRequest, createCitizenSession, registerCitizenCredential, verifyCitizenSession } from "./session";

type JsonBody = Record<string, unknown>;

const MAX_BODY_BYTES = 8192;
const STARTED_AT = Date.now();
const RATE_LIMITS = new Map<string, { count: number; resetAt: number }>();

const jsonHeaders = {
  "Content-Type": "application/json",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff"
};

export async function handleVoidApiRequest(req: Request): Promise<Response> {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }

  try {
    const route = getRoute(req);

    if (route[0] === "health") {
      return await handleHealth();
    }

    if (route[0] === "session") {
      return await handleSession(req);
    }

    if (req.method === "GET") {
      return await handleRead(req, route);
    }

    if (req.method !== "POST") {
      return await jsonWithState(req, "Method not allowed.", 405);
    }

    return await handleMutation(req, route);
  } catch (error) {
    return await jsonWithState(req, readableError(error), 400);
  }
}

async function handleHealth() {
  try {
    await readVoidState();
    const configuration = runtimeConfigurationStatus();
    const productionBlocked = configuration === "missing-required";
    return json({
      ok: !productionBlocked,
      status: productionBlocked ? "unhealthy" : configuration === "development-fallback" ? "degraded" : "healthy",
      service: "void-api",
      uptimeSeconds: Math.floor((Date.now() - STARTED_AT) / 1000),
      timestamp: new Date().toISOString(),
      configuration,
      store: dataStoreInfo()
    }, productionBlocked ? 503 : 200);
  } catch {
    return json({
      ok: false,
      status: "unhealthy",
      service: "void-api",
      timestamp: new Date().toISOString(),
      store: { kind: "file", configured: false }
    }, 503);
  }
}

async function handleSession(req: Request) {
  if (req.method !== "POST") {
    return json({ ok: false, message: "Method not allowed." }, 405);
  }

  const rateLimitMessage = rateLimitError(req, "session", 30, 10 * 60 * 1000);
  if (rateLimitMessage) return json({ ok: false, message: rateLimitMessage }, 429);

  const body = await readJson(req) as { email?: string; accessPhrase?: string; token?: string };

  if (body.token) {
    const session = await verifyCitizenSession(body.token);
    if (!session) return json({ ok: false, message: "Session is invalid or expired." }, 401);
    return json({ ok: true, session });
  }

  if (!body.email || !body.accessPhrase) {
    return json({ ok: false, message: "Email and private account phrase are required." }, 400);
  }

  return json({ ok: true, session: await createCitizenSession(body.email, body.accessPhrase) });
}

async function handleRead(req: Request, route: string[]) {
  const state = await readVoidState();
  const actor = await actorFromRequest(req);
  const area = route[0] || "state";
  const readableState = scopedStateForActor(state, actor);

  if (area === "state" || area === "") {
    return json({ ok: true, state: readableState, pulse: pulseSafetyNotice() });
  }

  if (area === "audit") {
    if (!actor?.isAdmin) return json({ ok: false, state: readableState, message: "Audit reads require admin authority.", pulse: pulseSafetyNotice() }, 403);
    return json({ ok: true, audit: state.audit, state: readableState, pulse: pulseSafetyNotice() });
  }

  return json({ ok: false, state: readableState, message: "Unknown read route.", pulse: pulseSafetyNotice() }, 404);
}

async function handleMutation(req: Request, route: string[]) {
  const body = await readJson(req);
  const action = toAction(route, body);
  const rateLimitMessage = action.type === "requestActivation"
    ? rateLimitError(req, "registration", 10, 60 * 60 * 1000)
    : rateLimitError(req, "mutation", 120, 10 * 60 * 1000);
  if (rateLimitMessage) return await jsonWithState(req, rateLimitMessage, 429);

  if (isAdminRoute(route) || action.type === "creditPulse" || action.type === "verifyQuest") {
    const adminError = adminKeyError(req);
    if (adminError) return await jsonWithState(req, adminError, 403);
  } else if (action.type !== "requestActivation") {
    const actor = await actorFromRequest(req);
    if (!actor) return await jsonWithState(req, "A valid Void citizen session is required.", 403);
  }

  const current = await readVoidState();
  const actor = await actorFromRequest(req);
  const authorizedAction = authorizeVoidApiAction(current, action, actor);
  const result = applyVoidApiAction(current, authorizedAction);
  await persistSessionSideEffects(action, result.event);
  await writeVoidState(result.state);

  return json({ ok: true, state: scopedStateForActor(result.state, actor), event: result.event, pulse: pulseSafetyNotice() });
}

function toAction(route: string[], body: JsonBody): VoidApiAction {
  const key = route.join("/");
  if (!key && body.action && typeof body.action === "object") {
    return genericAction(body.action as Partial<VoidApiAction> & { type?: string });
  }

  switch (key) {
    case "request-activation":
    case "register":
      return {
        type: "requestActivation",
        payload: {
          name: text(body.name),
          email: text(body.email),
          type: citizenType(body.type),
          operator: text(body.operator),
          purpose: text(body.purpose),
          accessPhrase: text(body.accessPhrase)
        }
      };
    case "admin/approve":
      return { type: "approveCitizen", requestId: text(body.requestId) };
    case "admin/deny":
      return { type: "denyCitizen", requestId: text(body.requestId) };
    case "subnets/create":
      return { type: "createSubnet", founderId: text(body.founderId), name: text(body.name), focus: text(body.focus), charter: text(body.charter) };
    case "subnets/join":
      return { type: "joinSubnet", citizenId: text(body.citizenId), subnetId: text(body.subnetId) };
    case "quests/publish":
      return {
        type: "publishQuest",
        issuerId: text(body.issuerId),
        subnetId: text(body.subnetId),
        title: text(body.title),
        questClass: text(body.questClass || "Build"),
        reward: numberValue(body.reward),
        expectedImpact: numberValue(body.expectedImpact),
        proofRequired: text(body.proofRequired)
      };
    case "quests/claim":
      return { type: "claimQuest", citizenId: text(body.citizenId), questId: text(body.questId) };
    case "quests/submit":
      return { type: "submitProof", questId: text(body.questId), proof: text(body.proof) };
    case "quests/verify":
      return { type: "verifyQuest", questId: text(body.questId), accepted: Boolean(body.accepted) };
    case "market/list":
      return {
        type: "publishListing",
        sellerId: text(body.sellerId),
        title: text(body.title),
        category: listingCategory(body.category),
        description: text(body.description),
        price: numberValue(body.price),
        unit: text(body.unit),
        proofRequired: text(body.proofRequired)
      };
    case "pulse/credit":
      return { type: "creditPulse", citizenId: text(body.citizenId), amount: numberValue(body.amount), reason: text(body.reason) };
    case "pulse/flow":
      return { type: "flowPulse", fromCitizenId: text(body.fromCitizenId), toCitizenId: text(body.toCitizenId), amount: numberValue(body.amount), reason: text(body.reason) };
    case "feedback/submit":
      return { type: "submitFeedback", citizenId: text(body.citizenId), scope: feedbackScope(body.scope), message: text(body.message), benefit: text(body.benefit) };
    default:
      throw new Error("Unknown API route.");
  }
}

function genericAction(action: Partial<VoidApiAction> & { type?: string }): VoidApiAction {
  if (action.type === "transferPulse") {
    const pulseAction = action as unknown as { fromCitizenId: string; toCitizenId: string; amount: number; reason: string };
    return {
      type: "flowPulse",
      fromCitizenId: pulseAction.fromCitizenId,
      toCitizenId: pulseAction.toCitizenId,
      amount: pulseAction.amount,
      reason: pulseAction.reason
    };
  }

  switch (action.type) {
    case "requestActivation":
    case "approveCitizen":
    case "denyCitizen":
    case "createSubnet":
    case "joinSubnet":
    case "publishQuest":
    case "claimQuest":
    case "submitProof":
    case "verifyQuest":
    case "creditPulse":
    case "flowPulse":
    case "publishListing":
    case "submitFeedback":
      return action as VoidApiAction;
    default:
      throw new Error("Unknown API action.");
  }
}

async function readJson(req: Request): Promise<JsonBody> {
  assertBodySize(req);
  try {
    const parsed = await req.json();
    return parsed && typeof parsed === "object" ? parsed as JsonBody : {};
  } catch {
    return {};
  }
}

function assertBodySize(req: Request) {
  const length = Number(req.headers.get("content-length") || "0");
  if (Number.isFinite(length) && length > MAX_BODY_BYTES) {
    throw new Error("Request body is too large.");
  }
}

function rateLimitError(req: Request, bucket: string, maxAttempts: number, windowMs: number) {
  const key = `${bucket}:${clientFingerprint(req)}`;
  const now = Date.now();
  cleanupRateLimits(now);
  const current = RATE_LIMITS.get(key);
  if (!current || current.resetAt <= now) {
    RATE_LIMITS.set(key, { count: 1, resetAt: now + windowMs });
    return null;
  }

  current.count += 1;
  if (current.count <= maxAttempts) return null;

  const retrySeconds = Math.max(1, Math.ceil((current.resetAt - now) / 1000));
  return `Too many Void requests. Try again in ${retrySeconds} seconds.`;
}

function cleanupRateLimits(now: number) {
  for (const [key, value] of RATE_LIMITS) {
    if (value.resetAt <= now) RATE_LIMITS.delete(key);
  }
}

function clientFingerprint(req: Request) {
  const direct = req.headers.get("x-void-client-ip")?.trim();
  if (process.env.VOID_TRUST_PROXY === "true") {
    const forwarded = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim();
    return forwarded || req.headers.get("x-real-ip")?.trim() || direct || "direct-local";
  }
  return direct || "direct-local";
}

function getRoute(req: Request) {
  const url = new URL(req.url);
  return url.pathname
    .replace(/^\/api\/void\/?/, "")
    .split("/")
    .map((part) => part.trim())
    .filter(Boolean);
}

function isAdminRoute(route: string[]) {
  return route[0] === "admin";
}

function adminKeyError(req: Request) {
  const expected = process.env.VOID_ADMIN_KEY || "";
  const received = req.headers.get("x-void-admin-key") || "";

  if (!expected) {
    return "VOID_ADMIN_KEY is not configured for protected Void admin actions.";
  }

  if (received !== expected) {
    return "Admin key header is missing or invalid.";
  }

  return null;
}

function hasAdminKey(req: Request) {
  const expected = process.env.VOID_ADMIN_KEY || "";
  const received = req.headers.get("x-void-admin-key") || "";
  return Boolean(expected && received === expected);
}

function scopedStateForActor(state: VoidState, actor: VoidActor | null) {
  if (actor?.isAdmin) return state;
  if (actor) return citizenProjection(state, actor.citizenId);

  return {
    ...state,
    currentCitizenId: state.citizens[0]?.id || "citizen_public",
    activationRequests: [],
    citizens: state.citizens.map(publicCitizen),
    quests: state.quests.filter((quest) => quest.status === "Open").map((quest) => ({
      ...quest,
      issuerId: "redacted",
      assigneeId: null,
      submission: null
    })),
    ledger: [],
    impactEvents: [],
    legacy: [],
    audit: [],
    feedback: []
  };
}

function publicCitizen(citizen: VoidState["citizens"][number]) {
  return {
    ...citizen,
    email: "",
    operator: ""
  };
}

function citizenProjection(state: VoidState, citizenId: string) {
  const visibleCitizenIds = new Set<string>([citizenId]);
  const visibleQuestIds = new Set<string>();

  for (const quest of state.quests) {
    if (quest.issuerId === citizenId || quest.assigneeId === citizenId || quest.status === "Open") {
      visibleQuestIds.add(quest.id);
      visibleCitizenIds.add(quest.issuerId);
      if (quest.assigneeId) visibleCitizenIds.add(quest.assigneeId);
    }
  }

  for (const listing of state.marketplace) {
    if (listing.status === "Open" || listing.sellerId === citizenId) {
      visibleCitizenIds.add(listing.sellerId);
    }
  }

  for (const subnet of state.subnets) {
    if (subnet.members.includes(citizenId) || subnet.founderId === citizenId) {
      visibleCitizenIds.add(subnet.founderId);
      subnet.members.forEach((memberId) => visibleCitizenIds.add(memberId));
    }
  }

  return {
    ...state,
    currentCitizenId: citizenId,
    activationRequests: [],
    citizens: state.citizens
      .filter((citizen) => visibleCitizenIds.has(citizen.id))
      .map((citizen) => citizen.id === citizenId ? citizen : { ...citizen, email: "" }),
    subnets: state.subnets.map((subnet) => ({
      ...subnet,
      members: subnet.members.includes(citizenId) ? subnet.members : []
    })),
    quests: state.quests
      .filter((quest) => visibleQuestIds.has(quest.id))
      .map((quest) => quest.issuerId === citizenId || quest.assigneeId === citizenId ? quest : { ...quest, submission: null }),
    marketplace: state.marketplace.filter((listing) => listing.status === "Open" || listing.sellerId === citizenId),
    ledger: state.ledger.filter((event) => event.source === citizenId || event.destination === citizenId),
    impactEvents: state.impactEvents.filter((event) => event.citizenId === citizenId),
    legacy: state.legacy.filter((event) => event.citizenId === citizenId),
    audit: [],
    feedback: state.feedback.filter((entry) => entry.citizenId === citizenId)
  };
}

async function actorFromRequest(req: Request): Promise<VoidActor | null> {
  if (hasAdminKey(req)) {
    return {
      citizenId: "citizen_founder",
      isAdmin: true
    };
  }

  try {
    const actor = actorFromSessionRequest(req);
    if (!actor) return null;
    return { ...actor, isAdmin: false };
  } catch {
    return null;
  }
}

async function persistSessionSideEffects(action: VoidApiAction, event: { targetId: string } | null) {
  if (action.type === "requestActivation") {
    if (!event?.targetId) throw new Error("Citizen registration could not be tied to a session credential.");
    await registerCitizenCredential(event.targetId, action.payload.email, action.payload.accessPhrase || "");
  }

  if (action.type === "approveCitizen" && event?.targetId) {
    await activateCredentialForRequest(action.requestId, event.targetId);
  }
}

async function jsonWithState(req: Request, message: string, status: number) {
  return json({ ok: false, state: scopedStateForActor(await safeState(), await actorFromRequest(req)), message, pulse: pulseSafetyNotice() }, status);
}

async function safeState() {
  try {
    return await readVoidState();
  } catch {
    return {
      currentCitizenId: "citizen_public",
      activationRequests: [],
      citizens: [],
      subnets: [],
      quests: [],
      marketplace: [],
      ledger: [],
      pulseVaults: { ubi: 0, infrastructure: 0, operating: 0 },
      impactEvents: [],
      legacy: [],
      audit: [],
      feedback: []
    } as VoidState;
  }
}

function text(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function citizenType(value: unknown): CitizenType {
  const textValue = text(value);
  if (["Human", "AI Agent", "Machine", "Organization"].includes(textValue)) return textValue as CitizenType;
  return "Human";
}

function feedbackScope(value: unknown): FeedbackScope {
  const textValue = text(value);
  if (["Experience", "AI Companion", "Resources", "Governance", "Safety", "Other"].includes(textValue)) return textValue as FeedbackScope;
  return "Experience";
}

function listingCategory(value: unknown): ListingCategory {
  const textValue = text(value);
  return ["Compute", "Service", "Training", "Product", "Data", "Model"].includes(textValue) ? textValue as ListingCategory : "Service";
}

function numberValue(value: unknown) {
  const numeric = typeof value === "number" ? value : Number(value);
  return Number.isFinite(numeric) ? numeric : 0;
}

function readableError(error: unknown) {
  return error instanceof Error ? error.message : "Void API request failed.";
}

function runtimeConfigurationStatus() {
  const adminKey = process.env.VOID_ADMIN_KEY || "";
  const sessionSecret = process.env.VOID_SESSION_SECRET || "";
  const missingProductionConfig = process.env.NODE_ENV === "production" && (!adminKey || sessionSecret.length < 32);

  if (missingProductionConfig) return "missing-required";
  if (!adminKey || sessionSecret.length < 32) return "development-fallback";
  return "ready";
}

function json(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), { status, headers: corsHeaders() });
}

function corsHeaders() {
  return jsonHeaders;
}
