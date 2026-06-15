const TABLE_NAME = "void_state_records";

export async function readJsonRecord<T>(key: string): Promise<T | null> {
  const config = databaseConfig();
  if (!config) return null;

  const response = await fetch(`${config.url}/rest/v1/${TABLE_NAME}?key=eq.${encodeURIComponent(key)}&select=value&limit=1`, {
    headers: databaseHeaders(config)
  });

  if (!response.ok) throw new Error(`Database read failed: ${response.status}`);

  const rows = await response.json() as Array<{ value: T }>;
  return rows[0]?.value || null;
}

export async function writeJsonRecord(key: string, value: unknown): Promise<boolean> {
  const config = databaseConfig();
  if (!config) return false;

  const response = await fetch(`${config.url}/rest/v1/${TABLE_NAME}?on_conflict=key`, {
    method: "POST",
    headers: {
      ...databaseHeaders(config),
      "Content-Type": "application/json",
      Prefer: "resolution=merge-duplicates"
    },
    body: JSON.stringify([{ key, value, updated_at: new Date().toISOString() }])
  });

  if (!response.ok) throw new Error(`Database write failed: ${response.status}`);
  return true;
}

function databaseConfig() {
  const url = getEnv("VOID_SUPABASE_URL");
  const serviceKey = getEnv("VOID_SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !serviceKey) return null;
  return { url: url.replace(/\/$/, ""), serviceKey };
}

function databaseHeaders(config: { serviceKey: string }) {
  return {
    apikey: config.serviceKey,
    Authorization: `Bearer ${config.serviceKey}`,
    Accept: "application/json"
  };
}

function getEnv(name: string) {
  const netlifyEnv = globalThis as typeof globalThis & { Netlify?: { env?: { get: (key: string) => string | undefined } } };
  return netlifyEnv.Netlify?.env?.get(name) || process.env[name] || "";
}
