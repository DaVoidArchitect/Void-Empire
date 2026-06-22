import type { VoidAction } from "./demoStore";
import type { VoidApiResponse, VoidState } from "./types";

const API_PATH = import.meta.env.VITE_VOID_API_PATH || "/api/void";

export type SyncStatus =
  | { mode: "idle"; label: string }
  | { mode: "syncing"; label: string }
  | { mode: "online"; label: string }
  | { mode: "offline"; label: string }
  | { mode: "error"; label: string };

export type RemoteKeys = {
  adminKey: string;
  sessionToken: string;
  actorCitizenId: string;
};

export async function loadRemoteState(keys: RemoteKeys): Promise<VoidState> {
  const response = await fetch(API_PATH, {
    headers: {
      Accept: "application/json",
      ...authHeaders(keys)
    }
  });
  return parseVoidResponse(response);
}

export async function sendRemoteAction(action: VoidAction, keys: RemoteKeys): Promise<VoidState> {
  if (action.type === "replaceState") return action.state;

  const response = await fetch(API_PATH, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...authHeaders(keys)
    },
    body: JSON.stringify({ action })
  });

  return parseVoidResponse(response);
}

export function requiresAdminKey(action: VoidAction) {
  return ["approveCitizen", "denyCitizen", "creditPulse", "verifyQuest", "reset"].includes(action.type);
}

export function requiresCitizenSession(action: VoidAction) {
  return !["replaceState", "setCurrentCitizen", "requestActivation"].includes(action.type);
}

function authHeaders(keys: RemoteKeys) {
  return {
    ...(keys.adminKey ? { "x-void-admin-key": keys.adminKey } : {}),
    ...(keys.sessionToken ? { Authorization: `Bearer ${keys.sessionToken}`, "x-void-session": keys.sessionToken } : {}),
    ...(keys.actorCitizenId ? { "x-void-actor-id": keys.actorCitizenId } : {})
  };
}

async function parseVoidResponse(response: Response): Promise<VoidState> {
  let payload: VoidApiResponse | null = null;
  try {
    payload = await response.json() as VoidApiResponse;
  } catch {
    throw new Error("Void API returned an unreadable response.");
  }

  if (!response.ok || !payload.ok) {
    throw new Error(payload?.message || "Void API request failed.");
  }

  return payload.state;
}
