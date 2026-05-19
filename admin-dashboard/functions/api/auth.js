// POST /api/auth — Register & Login for desktop tool
// Body: { "action": "register"|"login", "username": "...", "password": "..." }

async function hashPassword(password) {
  const encoder = new TextEncoder();
  const data = encoder.encode(password + "_imagine_salt_2024");
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, "0")).join("");
}

export async function onRequestPost(context) {
  const body = await context.request.json();
  const { action, username, password } = body;
  const db = context.env.DB;

  if (!username || !password) {
    return Response.json({ ok: false, error: "Thiếu username hoặc password" }, { status: 400 });
  }

  const pw_hash = await hashPassword(password);

  if (action === "register") {
    // Check if username exists
    const existing = await db.prepare("SELECT id FROM users WHERE username = ?").bind(username).first();
    if (existing) {
      return Response.json({ ok: false, error: "Username đã tồn tại" }, { status: 409 });
    }
    // Create user (is_active = 0, cần admin kích hoạt + set ngày)
    await db.prepare(
      "INSERT INTO users (username, password_hash, is_active, max_sessions) VALUES (?, ?, 0, 3)"
    ).bind(username, pw_hash).run();

    return Response.json({ ok: true, message: "Đăng ký thành công! Liên hệ admin để kích hoạt tài khoản." });
  }

  if (action === "login") {
    const user = await db.prepare(
      "SELECT id, username, is_active, max_sessions, expires_at FROM users WHERE username = ? AND password_hash = ?"
    ).bind(username, pw_hash).first();

    if (!user) {
      return Response.json({ ok: false, error: "Sai username hoặc password" }, { status: 401 });
    }

    if (!user.is_active) {
      return Response.json({ ok: false, error: "Tài khoản chưa được kích hoạt. Liên hệ admin." }, { status: 403 });
    }

    // Check subscription expiration
    if (user.expires_at) {
      const now = new Date();
      const expiresAt = new Date(user.expires_at + "Z"); // UTC
      if (now > expiresAt) {
        // Auto-disable account
        await db.prepare("UPDATE users SET is_active = 0 WHERE id = ?").bind(user.id).run();
        return Response.json({
          ok: false,
          error: "Gói dịch vụ đã hết hạn. Liên hệ admin để gia hạn.",
          expired: true,
          expires_at: user.expires_at,
        }, { status: 403 });
      }
    }

    // Update last login
    await db.prepare("UPDATE users SET last_login_at = datetime('now') WHERE id = ?").bind(user.id).run();

    // Calculate remaining days
    let days_remaining = null;
    if (user.expires_at) {
      const now = new Date();
      const expiresAt = new Date(user.expires_at + "Z");
      days_remaining = Math.max(0, Math.ceil((expiresAt - now) / (1000 * 60 * 60 * 24)));
    }

    return Response.json({
      ok: true,
      user: {
        id: user.id,
        username: user.username,
        max_sessions: user.max_sessions,
        expires_at: user.expires_at || null,
        days_remaining: days_remaining,
      }
    });
  }

  return Response.json({ ok: false, error: "action phải là 'register' hoặc 'login'" }, { status: 400 });
}
