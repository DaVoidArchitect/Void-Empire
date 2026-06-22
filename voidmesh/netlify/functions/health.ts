export default async function handler() {
  return new Response(
    JSON.stringify({
      ok: true,
      service: "void-alpha",
      runtime: "netlify-functions"
    }),
    {
      headers: {
        "content-type": "application/json"
      }
    }
  );
}
