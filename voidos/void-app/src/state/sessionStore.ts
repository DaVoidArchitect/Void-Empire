const SESSION_PATH = import.meta.env.VITE_VOID_SESSION_PATH || "/api/void/session";
const SESSION_STORAGE_KEY = "void-citizen-session";

export type CitizenSession = {
  token: string;
  citizenId: string;
  email: string;
  expiresAt: string;
};

type SessionResponse = {
  ok: boolean;
  session?: CitizenSession;
  message?: string;
};

export function readStoredSession(): CitizenSession | null {
  try {
    const saved = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!saved) return null;
    const session = JSON.parse(saved) as CitizenSession;
    if (!session.token || !session.citizenId || !session.expiresAt) return null;
    if (new Date(session.expiresAt).getTime() <= Date.now()) return null;
    return session;
  } catch {
    return null;
  }
}

export function saveStoredSession(session: CitizenSession | null) {
  if (!session) {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    return;
  }

  sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

export async function createRemoteSession(email: string, accessPhrase: string): Promise<CitizenSession> {
  const response = await fetch(SESSION_PATH, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ email, accessPhrase })
  });
  return parseSessionResponse(response);
}

export async function verifyRemoteSession(token: string): Promise<CitizenSession> {
  const response = await fetch(SESSION_PATH, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ token })
  });
  return parseSessionResponse(response);
}

async function parseSessionResponse(response: Response): Promise<CitizenSession> {
  let payload: SessionResponse | null = null;
  try {
    payload = await response.json() as SessionResponse;
  } catch {
    throw new Error("Void session service returned an unreadable response.");
  }

  if (!response.ok || !payload.ok || !payload.session) {
    throw new Error(payload?.message || "Void session request failed.");
  }

  return payload.session;
}
