// Middleware: Basic Auth cho toàn bộ dashboard
export async function onRequest(context) {
  const auth = context.request.headers.get("Authorization") || "";
  // "mvh30:30102002" base64 = "bXZoMzA6MzAxMDIwMDI="
  if (auth !== "Basic bXZoMzA6MzAxMDIwMDI=") {
    return new Response("Vui lòng đăng nhập", {
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="Image Generator Admin", charset="UTF-8"',
        "Content-Type": "text/plain; charset=utf-8",
      },
    });
  }

  // Auth OK — continue to page/API
  return await context.next();
}
