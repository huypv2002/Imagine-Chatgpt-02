// GET /api/users — List all users (admin only)
// POST /api/users — Update user (activate/deactivate/change max_sessions)

function checkAdmin(request) {
  const auth = request.headers.get("Authorization") || "";
  return auth === "Basic bXZoMzA6MzAxMDIwMDI=";
}

export async function onRequestGet(context) {
  if (!checkAdmin(context.request)) {
    return new Response("Unauthorized", { status: 401 });
  }
  const db = context.env.DB;
  const rows = await db.prepare("SELECT id, username, is_active, max_sessions, created_at, last_login_at FROM users ORDER BY created_at DESC").all();
  return Response.json({ users: rows.results || [] });
}

export async function onRequestPost(context) {
  if (!checkAdmin(context.request)) {
    return new Response("Unauthorized", { status: 401 });
  }
  const body = await context.request.json();
  const { id, is_active, max_sessions } = body;
  const db = context.env.DB;

  if (!id) {
    return Response.json({ ok: false, error: "Missing user id" }, { status: 400 });
  }

  const updates = [];
  const values = [];
  if (is_active !== undefined) { updates.push("is_active = ?"); values.push(is_active ? 1 : 0); }
  if (max_sessions !== undefined) { updates.push("max_sessions = ?"); values.push(max_sessions); }

  if (updates.length === 0) {
    return Response.json({ ok: false, error: "Nothing to update" }, { status: 400 });
  }

  values.push(id);
  await db.prepare(`UPDATE users SET ${updates.join(", ")} WHERE id = ?`).bind(...values).run();
  return Response.json({ ok: true });
}

// DELETE /api/users — Delete user
export async function onRequestDelete(context) {
  if (!checkAdmin(context.request)) {
    return new Response("Unauthorized", { status: 401 });
  }
  const url = new URL(context.request.url);
  const id = url.searchParams.get("id");
  if (!id) {
    return Response.json({ ok: false, error: "Missing id" }, { status: 400 });
  }
  const db = context.env.DB;
  await db.prepare("DELETE FROM users WHERE id = ?").bind(id).run();
  return Response.json({ ok: true });
}
