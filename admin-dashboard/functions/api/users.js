// GET /api/users — List all users (admin only)
// POST /api/users — Create or Update user (admin only)
// DELETE /api/users — Delete user (admin only)

function checkAdmin(request) {
  const auth = request.headers.get("Authorization") || "";
  return auth === "Basic bXZoMzA6MzAxMDIwMDI=";
}

async function hashPassword(password) {
  const encoder = new TextEncoder();
  const data = encoder.encode(password + "_imagine_salt_2024");
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, "0")).join("");
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
  const { id, username, password, is_active, max_sessions, expires_at, extend_days } = body;
  const db = context.env.DB;

  // ─── CREATE NEW USER (no id provided)
  if (!id && username && password) {
    const existing = await db.prepare("SELECT id FROM users WHERE username = ?").bind(username).first();
    if (existing) {
      return Response.json({ ok: false, error: "Username đã tồn tại" }, { status: 409 });
    }

    const pw_hash = await hashPassword(password);
    const active = is_active !== undefined ? (is_active ? 1 : 0) : 1;
    const sessions = max_sessions || 3;

    // Calculate expires_at if extend_days provided
    let expiresValue = null;
    if (extend_days && extend_days > 0) {
      const d = new Date();
      d.setDate(d.getDate() + extend_days);
      expiresValue = d.toISOString().replace("T", " ").substring(0, 19);
    } else if (expires_at) {
      expiresValue = expires_at;
    }

    await db.prepare(
      "INSERT INTO users (username, password_hash, is_active, max_sessions, expires_at) VALUES (?, ?, ?, ?, ?)"
    ).bind(username, pw_hash, active, sessions, expiresValue).run();

    return Response.json({ ok: true, message: "User created" });
  }

  // ─── UPDATE EXISTING USER (id provided)
  if (!id) {
    return Response.json({ ok: false, error: "Missing user id or username+password for creation" }, { status: 400 });
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
  if (password) {
    const pw_hash = await hashPassword(password);
    updates.push("password_hash = ?");
    values.push(pw_hash);
  }
  if (expires_at !== undefined) {
    updates.push("expires_at = ?");
    values.push(expires_at || null);
  }
  if (extend_days !== undefined && extend_days > 0) {
    const user = await db.prepare("SELECT expires_at FROM users WHERE id = ?").bind(id).first();
    let baseDate = new Date();
    if (user && user.expires_at) {
      const existing = new Date(user.expires_at + "Z");
      if (existing > baseDate) {
        baseDate = existing;
      }
    }
    baseDate.setDate(baseDate.getDate() + extend_days);
    const newExpires = baseDate.toISOString().replace("T", " ").substring(0, 19);
    updates.push("expires_at = ?");
    values.push(newExpires);
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
