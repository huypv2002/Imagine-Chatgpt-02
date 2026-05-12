# Text-to-Image Generator UI

Ứng dụng desktop minimalist để generate ảnh từ text prompts sử dụng ChatGPT API.

## Tính năng

✨ **Giao diện minimalist** - Tone màu xám, trắng, đen, thiết kế đơn giản tinh tế

🎨 **Generate ảnh từ text** - Nhập prompts hoặc upload file txt

📁 **Upload file txt** - Mỗi dòng là một prompt để gen ảnh

🔧 **Chọn kích thước** - Nhiều preset sizes (1024x1024, 1792x1024, 1024x1792, v.v.)

👥 **Quản lý accounts** - Thêm, xóa, refresh nhiều accounts

⚡ **Session management** - Tự động phân bổ prompts cho các accounts

📊 **Theo dõi tiến trình** - Progress bar và kết quả real-time

## Cài đặt

### 1. Cài đặt dependencies

```bash
# Sử dụng uv (khuyến nghị)
uv sync

# Hoặc sử dụng pip
pip install pyside6
```

### 2. Chạy ứng dụng

```bash
python image_generator_ui.py
```

## Hướng dẫn sử dụng

### Bước 1: Thêm Accounts

1. Chuyển sang tab **"Quản Lý Accounts"**
2. Nhập access tokens vào ô text (mỗi dòng một token)
3. Click **"Thêm Accounts"**
4. Accounts sẽ được hiển thị trong bảng với thông tin:
   - Email
   - Type (free/plus/team)
   - Status (正常/限流/异常)
   - Quota còn lại
   - Số lần thành công/thất bại

### Bước 2: Generate Images

1. Chuyển sang tab **"Generate Images"**
2. Nhập prompts theo một trong hai cách:
   - **Upload file txt**: Click "Chọn File TXT" và chọn file (mỗi dòng một prompt)
   - **Nhập trực tiếp**: Gõ prompts vào ô text (mỗi dòng một prompt)

3. Chọn cài đặt:
   - **Model**: `gpt-image-2` hoặc `codex-gpt-image-2`
   - **Kích thước**: 1024x1024, 1792x1024, 1024x1792, 512x512, 768x768

4. Click **"Bắt Đầu Generate"**

5. Theo dõi tiến trình:
   - Progress bar hiển thị % hoàn thành
   - Label hiển thị prompt đang xử lý
   - Danh sách kết quả cập nhật real-time

6. Khi hoàn thành:
   - Click **"Mở Thư Mục Output"** để xem ảnh
   - Ảnh được lưu trong `./output/YYYYMMDD_HHMMSS/`

### Quản lý Accounts

#### Refresh Accounts
- Click **"Refresh All"** để cập nhật thông tin tất cả accounts
- Hệ thống sẽ kiểm tra quota, status, và thông tin mới nhất

#### Xóa Accounts
- Chọn các accounts trong bảng (click để chọn, Ctrl/Cmd+Click để chọn nhiều)
- Click **"Xóa Selected"**
- Xác nhận để xóa

#### Xem thông tin Account
- Bảng hiển thị đầy đủ thông tin:
  - **Email**: Email của account
  - **Type**: Loại tài khoản (free, plus, team)
  - **Status**: Trạng thái (正常 = OK, 限流 = Rate limited, 异常 = Error)
  - **Quota**: Số lượng ảnh còn lại
  - **Success**: Số lần generate thành công
  - **Failed**: Số lần generate thất bại

## Session Management

Hệ thống tự động:
- ✅ Chọn account có quota available
- ✅ Phân bổ prompts đều cho các accounts
- ✅ Xử lý rate limiting tự động
- ✅ Retry khi có lỗi
- ✅ Cập nhật quota sau mỗi lần generate

## Format File TXT

File txt chứa prompts phải có format:

```
a beautiful sunset over the ocean
a cat sitting on a windowsill
cyberpunk city at night with neon lights
portrait of a wise old wizard
```

- Mỗi dòng là một prompt
- Dòng trống sẽ bị bỏ qua
- Encoding: UTF-8

## Kích thước ảnh

Các kích thước được hỗ trợ:
- **1024x1024** - Vuông, cân đối
- **1792x1024** - Ngang, phù hợp landscape
- **1024x1792** - Dọc, phù hợp portrait
- **512x512** - Nhỏ, nhanh
- **768x768** - Trung bình

## Thư mục Output

Ảnh được lưu trong:
```
./output/
  └── 20260511_143022/          # Timestamp của session
      ├── img_conv123_0.png     # Ảnh 1
      ├── img_conv456_0.png     # Ảnh 2
      └── ...
```

## Troubleshooting

### Lỗi "No available image quota"
- Kiểm tra accounts có quota > 0
- Refresh accounts để cập nhật quota
- Thêm thêm accounts mới

### Lỗi "Invalid access token"
- Token đã hết hạn hoặc không hợp lệ
- Xóa token cũ và thêm token mới
- Kiểm tra token có đúng format không

### Ảnh không được generate
- Kiểm tra prompt có hợp lệ không
- Xem log trong terminal để biết lỗi chi tiết
- Kiểm tra account status (phải là "正常")

### UI bị lag
- Đang xử lý nhiều prompts cùng lúc
- Đợi hoặc click "Dừng" để dừng lại
- Chia nhỏ batch prompts

## Tips

💡 **Tối ưu performance**:
- Thêm nhiều accounts để xử lý song song
- Chia nhỏ file prompts thành nhiều batch
- Sử dụng model `gpt-image-2` cho tốc độ nhanh hơn

💡 **Viết prompts tốt**:
- Mô tả chi tiết, rõ ràng
- Thêm style, mood, lighting
- Tham khảo: "a photorealistic portrait of a cat, studio lighting, 4k"

💡 **Quản lý accounts**:
- Refresh accounts định kỳ để cập nhật quota
- Xóa accounts bị "异常" hoặc "限流"
- Backup tokens ở nơi an toàn

## Keyboard Shortcuts

- **Ctrl/Cmd + O**: Mở file txt
- **Ctrl/Cmd + Enter**: Bắt đầu generate (khi focus vào prompts)
- **Esc**: Dừng generation

## Giao diện

### Màu sắc
- **Background**: #f5f5f5 (xám nhạt)
- **Cards**: #ffffff (trắng)
- **Primary**: #2c2c2c (đen)
- **Text**: #2c2c2c (đen)
- **Secondary text**: #666666 (xám)
- **Border**: #e0e0e0 (xám nhạt)

### Typography
- **Font**: System font (-apple-system, Segoe UI, Roboto)
- **Size**: 13px (body), 20px (title)
- **Weight**: 400 (normal), 500 (medium), 600 (semibold)

## License

MIT License - Xem file LICENSE để biết thêm chi tiết.
