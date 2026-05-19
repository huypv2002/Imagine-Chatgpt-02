// GET /api/users — List all users (admin only)
// POST /api/users — Update user (activate/deactivate/change max_sessions/set expires_at/extend days)

function checkAdmin(request) {
  const auth = request.headers.get("Authorization") || "";
  return auth === "Basic bXZoMzA6MzAxMDIwMDI=";
}

export async function onRequestGet(context) {
  if (!checkAdmin(context.request)) {
    return new Response("Unauthorized", { status: 401 });
  }
  const db = context.env.DB;
  const rows = await db.prepare(
    "SELECT id, username, is_active, max_sessions, expires_at, created_at, last_login_at FROM users ORDER BY created_at DESC"
  ).all();

  // Calculate days_remaining for each user
  const now = new Date();
  const users = (rows.results || []).map(user => {
    let days_remaining = null;
    if (user.expires_at) {
      const expiresAt = new Date(user.expires_at + "Z");
      days_remaining = Math.max(0, Math.ceil((expiresAt - now) / (1000 * 60 * 60 * 24)));
      if (days_remaining === 0 && user.is_active) {
        days_remaining = 0; // expired but not yet disabled (will be on next login)
      }
    }
    return { ...user, days_remaining };
  });

  return Response.json({ users });
}

export async function onRequestPost(context) {
  if (!checkAdmin(context.request)) {
    return new Response("Unauthorized", { status: 401 });
  }
  const body = await context.request.json();
  const { id, is_active, max_sessions, expires_at, extend_days } = body;
  const db = context.env.DB;

  if (!id) {
    return Response.json({ ok: false, error: "Missing user id" }, { status: 400 });
  }

  const updates = [];
  const values = [];

  if (is_active !== undefined) {
    updates.push("is_active = ?");
    values.push(is_active ? 1 : 0);
  }
  if (max_sessions !== undefined) {
    updates.push("max_sessions = ?");
    values.push(max_sessions);
  }
  if (expires_at !== undefined) {
    // Set exact expiration date (ISO format: "2025-06-30 23:59:59")
    updates.push("expires_at = ?");
    values.push(expires_at || null); // null = unlimited
  }
  if (extend_days !== undefined && extend_days > 0) {
    // Extend from current expires_at or from now
    // If user already has expires_at in the future, extend from that date
    // If expired or no expires_at, extend from now
    const user = await db.prepare("SELECT expires_at FROM users WHERE id = ?").bind(id).first();
    let baseDate = new Date();
    if (user && user.expires_at) {
      const existing = new Date(user.expires_at + "Z");
      if (existing > baseDate) {
        baseDate = existing; // extend from future date
      }
    }
    baseDate.setDate(baseDate.getDate() + extend_days);
    const newExpires = baseDate.toISOString().replace("T", " ").substring(0, 19);
    updates.push("expires_at = ?");
    values.push(newExpires);
    // Also activate the user when extending
    if (is_active === undefined) {
      updates.push("is_active = 1");
    }
  }

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
