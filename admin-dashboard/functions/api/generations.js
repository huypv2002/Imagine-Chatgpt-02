// GET /api/generations — List generations (auth handled by _middleware.js)
export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const page = parseInt(url.searchParams.get("page") || "1");
  const limit = parseInt(url.searchParams.get("limit") || "50");
  const offset = (page - 1) * limit;

  const db = context.env.DB;
  const rows = await db.prepare(
    "SELECT * FROM generations ORDER BY created_at DESC LIMIT ? OFFSET ?"
  ).bind(limit, offset).all();

  const total = await db.prepare("SELECT COUNT(*) as count FROM generations").first();

  return Response.json({
    data: rows.results,
    total: total?.count || 0,
    page,
    limit,
  });
}

// POST /api/generations — Add generation record (auth handled by _middleware.js)
export async function onRequestPost(context) {
  const body = await context.request.json();
  const db = context.env.DB;

  await db.prepare(
    "INSERT INTO generations (prompt, model, ratio, status, file_name, error, account_name, completed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
  ).bind(
    body.prompt || "",
    body.model || "gpt-image-2",
    body.ratio || "1:1",
    body.status || "pending",
    body.file_name || null,
    body.error || null,
    body.account_name || null,
    body.status === "success" || body.status === "failed" ? new Date().toISOString() : null
  ).run();

  return Response.json({ ok: true });
}
