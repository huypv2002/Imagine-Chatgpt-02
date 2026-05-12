// GET /api/stats — Dashboard statistics (auth handled by _middleware.js)
export async function onRequestGet(context) {
  const db = context.env.DB;

  const total = await db.prepare("SELECT COUNT(*) as count FROM generations").first();
  const success = await db.prepare("SELECT COUNT(*) as count FROM generations WHERE status = 'success'").first();
  const failed = await db.prepare("SELECT COUNT(*) as count FROM generations WHERE status = 'failed'").first();
  const accounts = await db.prepare("SELECT COUNT(*) as count FROM accounts").first();

  return Response.json({
    total_generations: total?.count || 0,
    total_success: success?.count || 0,
    total_failed: failed?.count || 0,
    total_accounts: accounts?.count || 0,
  });
}
