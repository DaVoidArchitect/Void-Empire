import type { Config, Context } from "@netlify/functions";
import { applyVoidApiAction, authorizeVoidApiAction, createVoidSeedState, type VoidActor, type VoidApiAction } from "../../src/shared/voidState";
import type { VoidAction } from "../../src/state/demoStore";
import type { VoidApiResponse, VoidState } from "../../src/state/types";
import { actorFromSessionRequest, assertSessionCitizen } from "./_shared/session";
import { activateCredentialForRequest, registerCitizenCredential } from "./_shared/voidSessionStore";
import { readVoidState, writeVoidState } from "./_shared/voidStore";

const adminActions = new Set<VoidAction["type"]>([
  "approveCitizen",
  "denyCitizen",
  "creditPulse",
  "verifyQuest",
  "reset"
]);

const publicActions = new Set<VoidAction["type"]>([
  "requestActivation"
]);

const MAX_BODY_BYTES = 8192;

export default async (req: Request, _context: Context) => {
  try {
    if (req.method === "GET") {
      return json({ ok: true, state: await readableState(await readState(), req) });
    }

    if (req.method !== "POST") {
      return json({ ok: false, state: await readableState(await readState(), req), message: "Method not allowed." }, 405);
    }

    assertBodySize(req);
    const body = await req.json().catch(() => null) as { action?: VoidAction } | null;
    if (!body?.action?.type) {
      return json({ ok: false, state: await readableState(await readState(), req), message: "A valid Void action is required." }, 400);
    }

    if (adminActions.has(body.action.type) && !isAdminRequest(req)) {
      return json({
        ok: false,
        state: await readableState(await readState(), req),
        message: "This action requires the deployment admin key."
      }, 403);
    }

    if (!publicActions.has(body.action.type) && !await actorFromRequest(req)) {
      return json({
        ok: false,
        state: await readableState(await readState(), req),
        message: "This action requires a Void citizen session."
      }, 403);
    }

    if (body.action.type === "reset") {
      const seeded = createVoidSeedState();
      await writeState(seeded);
      return json({ ok: true, state: await readableState(seeded, req) });
    }

    const apiAction = toApiAction(body.action);
    if (!apiAction) {
      return json({ ok: false, state: await readableState(await readState(), req), message: "Action is local-only in this alpha." }, 400);
    }

    const current = await readState();
    const authorizedAction = authorizeVoidApiAction(current, apiAction, await actorFromRequest(req));
    const result = applyVoidApiAction(current, authorizedAction);
    await persistSessionSideEffects(apiAction, result.event);
    const next = result.state;
    await writeState(next);

    return json({ ok: true, state: await readableState(next, req) });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Void API failed.";
    return json({ ok: false, state: await readableState(await safeState(), req), message }, 500);
  }
};

export const config: Config = {
  method: ["GET", "POST"]
};

async function readState(): Promise<VoidState> {
  return readVoidState();
}

async function writeState(state: VoidState) {
  await writeVoidState(state);
}

async function safeState() {
  try {
    return await readState();
  } catch {
    return createVoidSeedState();
  }
}

function isAdminRequest(req: Request) {
  const configuredKey = readEnv("VOID_ADMIN_KEY");
  const providedKey = req.headers.get("x-void-admin-key") || "";

  if (!configuredKey) {
    return false;
  }

  return providedKey === configuredKey;
}

function readEnv(key: string) {
  const netlify = (globalThis as { Netlify?: { env?: { get(name: string): string | undefined } } }).Netlify;
  return netlify?.env?.get(key) || process.env[key] || "";
}

async function readableState(state: VoidState, req: Request): Promise<VoidState> {
  const actor = await actorFromRequest(req);
  if (actor) {
    try {
      assertSessionCitizen(state, actor);
      return actor.isAdmin ? state : citizenProjection(state, actor.citizenId);
    } catch {
      // Return the public projection if a stale session points at a missing or inactive citizen.
    }
  }

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

function publicCitizen(citizen: VoidState["citizens"][number]): VoidState["citizens"][number] {
  return {
    ...citizen,
    email: "",
    operator: ""
  };
}

function citizenProjection(state: VoidState, citizenId: string): VoidState {
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
  if (isAdminRequest(req)) {
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

function toApiAction(action: VoidAction): VoidApiAction | null {
  if (action.type === "replaceState" || action.type === "setCurrentCitizen" || action.type === "reset") return null;
  if (action.type === "transferPulse") {
    return {
      type: "flowPulse",
      fromCitizenId: action.fromCitizenId,
      toCitizenId: action.toCitizenId,
      amount: action.amount,
      reason: action.reason
    };
  }

  return action;
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

function json(payload: VoidApiResponse, status = 200) {
  return Response.json(payload, {
    status,
    headers: {
      "Cache-Control": "no-store"
    }
  });
}

function assertBodySize(req: Request) {
  const length = Number(req.headers.get("content-length") || "0");
  if (Number.isFinite(length) && length > MAX_BODY_BYTES) {
    throw new Error("Request body is too large.");
  }
}
