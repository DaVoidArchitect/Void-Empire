import type { Config, Context } from "@netlify/functions";
import { createCitizenSession, verifyCitizenSession } from "./_shared/voidSessionStore";

const MAX_BODY_BYTES = 8192;

type SessionBody = {
  email?: string;
  accessPhrase?: string;
  token?: string;
};

export default async (req: Request, _context: Context) => {
  try {
    if (req.method !== "POST") {
      return json({ ok: false, message: "Method not allowed." }, 405);
    }

    assertBodySize(req);
    const body = await req.json().catch(() => ({})) as SessionBody;

    if (body.token) {
      const session = await verifyCitizenSession(body.token);
      if (!session) return json({ ok: false, message: "Session is invalid or expired." }, 401);
      return json({ ok: true, session });
    }

    if (!body.email || !body.accessPhrase) {
      return json({ ok: false, message: "Email and private account phrase are required." }, 400);
    }

    return json({ ok: true, session: await createCitizenSession(body.email, body.accessPhrase) });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Session request failed.";
    return json({ ok: false, message }, 400);
  }
};

export const config: Config = {
  method: ["POST"],
  path: "/api/void/session"
};

function json(payload: unknown, status = 200) {
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
