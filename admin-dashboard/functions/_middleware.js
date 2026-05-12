// Middleware: Basic Auth cho toàn bộ dashboard
export async function onRequest(context) {
  const url = new URL(context.request.url);

  // /api/auth là public — không cần Basic Auth (dùng cho tool desktop đăng ký/đăng nhập)
  if (url.pathname === "/api/auth") {
    return await context.next();
  }

  const auth = context.request.headers.get("Authorization") || "";
  // "mvh30:30102002" in base64 = "bXZoMzA6MzAxMDIwMDI="
  if (auth !== "Basic bXZoMzA6MzAxMDIwMDI=") {
    return new Response("Vui lòng đăng nhập", {
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="Image Generator Admin", charset="UTF-8"',
        "Content-Type": "text/plain; charset=utf-8",
      },
    });
  }

  return await context.next();
}
