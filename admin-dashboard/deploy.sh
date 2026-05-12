#!/bin/bash
echo "=== Image Generator Admin Dashboard ==="
echo ""

# 1. Create D1 database
echo "1. Tạo D1 database..."
DB_OUTPUT=$(wrangler d1 create image-gen-db 2>&1)
echo "$DB_OUTPUT"

# Extract database_id
DB_ID=$(echo "$DB_OUTPUT" | grep -o 'database_id = "[^"]*"' | cut -d'"' -f2)
if [ -z "$DB_ID" ]; then
    DB_ID=$(echo "$DB_OUTPUT" | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' | head -1)
fi

if [ -n "$DB_ID" ]; then
    echo "Database ID: $DB_ID"
    # Update wrangler.toml
    sed -i '' "s/database_id = \"\"/database_id = \"$DB_ID\"/" wrangler.toml
    echo "Đã cập nhật wrangler.toml"
else
    echo "⚠️  Không lấy được database_id. Có thể DB đã tồn tại."
    echo "   Chạy: wrangler d1 list"
    echo "   Rồi cập nhật database_id trong wrangler.toml"
fi

echo ""

# 2. Apply schema
echo "2. Tạo bảng..."
wrangler d1 execute image-gen-db --file=./schema.sql
echo ""

# 3. Deploy Pages
echo "3. Deploy lên Cloudflare Pages..."
wrangler pages deploy ./dist --project-name=image-gen-admin
echo ""

echo "=== DONE ==="
echo "Dashboard sẽ có tại: https://image-gen-admin.pages.dev"
