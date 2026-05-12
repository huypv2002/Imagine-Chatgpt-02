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
    // Create user (is_active = 1, active ngay khi đăng ký)
    await db.prepare(
      "INSERT INTO users (username, password_hash, is_active, max_sessions) VALUES (?, ?, 1, 3)"
    ).bind(username, pw_hash).run();

    return Response.json({ ok: true, message: "Đăng ký thành công! Bạn có thể đăng nhập ngay." });
  }

  if (action === "login") {
    const user = await db.prepare(
      "SELECT id, username, is_active, max_sessions FROM users WHERE username = ? AND password_hash = ?"
    ).bind(username, pw_hash).first();

    if (!user) {
      return Response.json({ ok: false, error: "Sai username hoặc password" }, { status: 401 });
    }

    if (!user.is_active) {
      return Response.json({ ok: false, error: "Tài khoản chưa được kích hoạt. Liên hệ admin." }, { status: 403 });
    }

    // Update last login
    await db.prepare("UPDATE users SET last_login_at = datetime('now') WHERE id = ?").bind(user.id).run();

    return Response.json({
      ok: true,
      user: {
        id: user.id,
        username: user.username,
        max_sessions: user.max_sessions,
      }
    });
  }

  return Response.json({ ok: false, error: "action phải là 'register' hoặc 'login'" }, { status: 400 });
}
