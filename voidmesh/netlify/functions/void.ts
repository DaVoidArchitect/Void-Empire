import { applyVoidApiAction, authorizeVoidApiAction, pulseSafetyNotice } from "../../src/shared/voidState";
import type { CitizenType, FeedbackScope, ListingCategory, VoidActor, VoidApiAction } from "../../src/shared/voidState";
import { actorFromSessionRequest, assertSessionCitizen } from "./_shared/session";
import { activateCredentialForRequest, registerCitizenCredential } from "./_shared/voidSessionStore";
import { readVoidState, writeVoidState } from "./_shared/voidStore";

type JsonBody = Record<string, unknown>;
type StoredVoidState = Awaited<ReturnType<typeof readVoidState>>;

const MAX_BODY_BYTES = 8192;

const jsonHeaders = {
  "Content-Type": "application/json",
  "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Void-Admin-Key, X-Void-Actor-Id, X-Void-Citizen-Id, X-Void-Session",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Cache-Control": "no-store"
};

export default async function handler(req: Request) {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: jsonHeaders });
  }

  try {
    const route = getRoute(req);

    if (req.method === "GET") {
      return await handleRead(req, route);
    }

    if (req.method !== "POST") {
      return json({ error: "Method not allowed." }, 405);
    }

    return await handleMutation(req, route);
  } catch (error) {
    return json({ error: readableError(error), pulse: pulseSafetyNotice() }, 400);
  }
}

export const config = {
  path: [
    "/api/void",
    "/api/void/state",
    "/api/void/audit",
    "/api/void/request-activation",
    "/api/void/register",
    "/api/void/admin/approve",
    "/api/void/admin/deny",
    "/api/void/subnets/create",
    "/api/void/subnets/join",
    "/api/void/quests/publish",
    "/api/void/quests/claim",
    "/api/void/quests/submit",
    "/api/void/quests/verify",
    "/api/void/market/list",
    "/api/void/pulse/credit",
    "/api/void/pulse/flow",
    "/api/void/feedback/submit"
  ]
};

async function handleRead(req: Request, route: string[]) {
  const state = await readVoidState();
  const actor = await actorFromRequest(req);
  if (!actor) throw new Error("A valid Void citizen session is required.");
  assertSessionCitizen(state, actor);

  const area = route[0] || "state";
  const readableState = scopedStateForActor(state, actor);

  if (area === "state") {
    return json({ state: readableState, pulse: pulseSafetyNotice() });
  }

  if (area === "audit") {
    if (!actor.isAdmin) throw new Error("Audit reads require admin authority.");
    return json({ audit: state.audit, state: readableState, pulse: pulseSafetyNotice() });
  }

  return json({
    error: "Unknown read route.",
    availableRoutes: [
      "GET /api/void/state",
      "GET /api/void/audit",
      "POST /api/void/request-activation",
      "POST /api/void/register",
      "POST /api/void/admin/approve",
      "POST /api/void/admin/deny",
      "POST /api/void/subnets/create",
      "POST /api/void/subnets/join",
      "POST /api/void/quests/publish",
      "POST /api/void/quests/claim",
      "POST /api/void/quests/submit",
      "POST /api/void/quests/verify",
      "POST /api/void/market/list",
      "POST /api/void/pulse/credit",
      "POST /api/void/pulse/flow",
      "POST /api/void/feedback/submit"
    ],
    pulse: pulseSafetyNotice()
  }, 404);
}

async function handleMutation(req: Request, route: string[]) {
  const body = await readJson(req);
  const action = toAction(route, body);

  if (isAdminRoute(route) || action.type === "creditPulse" || action.type === "verifyQuest") {
    requireAdminKey(req);
  } else if (action.type !== "requestActivation") {
    await requireSession(req);
  }

  const current = await readVoidState();
  const actor = await actorFromRequest(req);
  const authorizedAction = authorizeVoidApiAction(current, action, actor);
  const result = applyVoidApiAction(current, authorizedAction);
  await persistSessionSideEffects(action, result.event);
  await writeVoidState(result.state);

  return json({ state: scopedStateForActor(result.state, actor), event: result.event, pulse: pulseSafetyNotice() });
}

function toAction(route: string[], body: JsonBody): VoidApiAction {
  const key = route.join("/");
  if (!key && body.action && typeof body.action === "object") {
    return genericAction(body.action as Partial<VoidApiAction>);
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
      return {
        type: "createSubnet",
        founderId: text(body.founderId),
        name: text(body.name),
        focus: text(body.focus),
        charter: text(body.charter)
      };
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
      return {
        type: "creditPulse",
        citizenId: text(body.citizenId),
        amount: numberValue(body.amount),
        reason: text(body.reason)
      };
    case "pulse/flow":
      return {
        type: "flowPulse",
        fromCitizenId: text(body.fromCitizenId),
        toCitizenId: text(body.toCitizenId),
        amount: numberValue(body.amount),
        reason: text(body.reason)
      };
    case "feedback/submit":
      return {
        type: "submitFeedback",
        citizenId: text(body.citizenId),
        scope: feedbackScope(body.scope),
        message: text(body.message),
        benefit: text(body.benefit)
      };
    default:
      throw new Error("Unknown API route.");
  }
}

function genericAction(action: Partial<VoidApiAction>): VoidApiAction {
  if ((action as { type?: string }).type === "transferPulse") {
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

function requireAdminKey(req: Request) {
  const expected = getEnv("VOID_ADMIN_KEY");
  const received = req.headers.get("x-void-admin-key") || "";

  if (!expected) {
    throw new Error("VOID_ADMIN_KEY is not configured for protected Void admin actions.");
  }

  if (received !== expected) {
    throw new Error("Admin key header is missing or invalid.");
  }
}

async function requireSession(req: Request) {
  if (!await actorFromRequest(req)) throw new Error("A valid Void citizen session is required.");
}

function hasAdminKey(req: Request) {
  const expected = getEnv("VOID_ADMIN_KEY");
  const received = req.headers.get("x-void-admin-key") || "";
  return Boolean(expected && received === expected);
}

function scopedStateForActor(state: StoredVoidState, actor: VoidActor | null) {
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

function publicCitizen(citizen: StoredVoidState["citizens"][number]) {
  return {
    ...citizen,
    email: "",
    operator: ""
  };
}

function citizenProjection(state: StoredVoidState, citizenId: string) {
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
      citizenId: req.headers.get("x-void-actor-id") || req.headers.get("x-void-citizen-id") || "citizen_founder",
      isAdmin: true
    };
  }

  try {
    const actor = await actorFromSessionRequest(req);
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

function getEnv(name: string) {
  const netlifyEnv = globalThis as typeof globalThis & { Netlify?: { env?: { get: (key: string) => string | undefined } } };
  return netlifyEnv.Netlify?.env?.get(name) || process.env[name] || "";
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

function json(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), { status, headers: jsonHeaders });
}
