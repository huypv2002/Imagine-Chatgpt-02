# Imagine CLI - Hướng dẫn sử dụng

CLI tool đơn giản để tạo ảnh từ text sử dụng chức năng Imagine 2.0 của ChatGPT.

## Yêu cầu

### 1. Cài đặt dependencies

```bash
cd /Users/phamvanhuy/Downloads/chatgpt2api/chatgpt2api
uv sync
```

Hoặc nếu không dùng `uv`, cài đặt thủ công:

```bash
pip install curl-cffi fastapi pillow pybase64 python-multipart tiktoken uvicorn
```

### 2. Lấy Access Token

Bạn cần có **ChatGPT Access Token** để sử dụng tool này.

#### Cách lấy Access Token:

1. Đăng nhập vào https://chatgpt.com
2. Mở Developer Tools (F12)
3. Vào tab **Application** (Chrome) hoặc **Storage** (Firefox)
4. Tìm **Cookies** → `https://chatgpt.com`
5. Tìm cookie có tên `__Secure-next-auth.session-token`
6. Copy giá trị của cookie này - đây là access token của bạn

**Lưu ý:** 
- Token này sẽ hết hạn sau một thời gian
- Không chia sẻ token với người khác
- Nên dùng tài khoản test, không dùng tài khoản chính

### 3. Loại tài khoản

- **Free account**: Có giới hạn số lượng ảnh/ngày
- **Plus/Team/Pro**: Có quota cao hơn
- Tool sẽ hiển thị quota còn lại khi chạy

## Cách sử dụng

### Cú pháp cơ bản

```bash
python imagine_cli.py --token "YOUR_ACCESS_TOKEN" --prompt "mô tả ảnh"
```

### Ví dụ

#### 1. Tạo 1 ảnh đơn giản

```bash
python imagine_cli.py \
  --token "eyJhbGc..." \
  --prompt "một con mèo đang bay trong không gian, phong cách anime"
```

#### 2. Tạo nhiều ảnh cùng lúc

```bash
python imagine_cli.py \
  --token "eyJhbGc..." \
  --prompt "cyberpunk city at night with neon lights" \
  --num 2
```

#### 3. Chỉ định thư mục output

```bash
python imagine_cli.py \
  --token "eyJhbGc..." \
  --prompt "beautiful sunset over mountains" \
  --output ./my_images
```

#### 4. Sử dụng model Codex (chỉ Plus/Team/Pro)

```bash
python imagine_cli.py \
  --token "eyJhbGc..." \
  --prompt "futuristic robot" \
  --model codex-gpt-image-2
```

#### 5. Bật chế độ verbose để debug

```bash
python imagine_cli.py \
  --token "eyJhbGc..." \
  --prompt "dragon flying" \
  --verbose
```

### Tham số

| Tham số | Viết tắt | Mô tả | Mặc định | Bắt buộc |
|---------|----------|-------|----------|----------|
| `--token` | `-t` | ChatGPT access token | - | ✓ |
| `--prompt` | `-p` | Mô tả ảnh cần tạo | - | ✓ |
| `--model` | `-m` | Model: `gpt-image-2` hoặc `codex-gpt-image-2` | `gpt-image-2` | ✗ |
| `--output` | `-o` | Thư mục lưu ảnh | `./output` | ✗ |
| `--num` | `-n` | Số lượng ảnh (1-4) | `1` | ✗ |
| `--verbose` | `-v` | Hiển thị log chi tiết | `False` | ✗ |

## Kết quả

Ảnh sẽ được lưu với tên: `imagine_{conversation_id}_{index}.png`

Ví dụ:
```
output/
  ├── imagine_abc123_0.png
  ├── imagine_abc123_1.png
  └── imagine_def456_0.png
```

## Xử lý lỗi

### Lỗi thường gặp

#### 1. "Access token không hợp lệ"
- Token đã hết hạn → Lấy token mới
- Token sai format → Kiểm tra lại

#### 2. "Tài khoản đang bị giới hạn tốc độ"
- Đã hết quota → Đợi reset (tool sẽ hiển thị thời gian)
- Tạo quá nhiều ảnh trong thời gian ngắn → Đợi một lúc

#### 3. "Không tìm thấy URL ảnh"
- Server đang xử lý → Thử lại sau
- Prompt vi phạm policy → Thay đổi prompt

#### 4. Import error
- Thiếu dependencies → Chạy `uv sync` hoặc cài đặt thủ công
- Sai đường dẫn → Chạy từ thư mục gốc của project

## Tips

### 1. Viết prompt tốt

✅ **Tốt:**
```
"a cute cat floating in space, anime style, detailed, colorful"
"cyberpunk city at night, neon lights, rain, cinematic"
"portrait of a warrior, fantasy art, dramatic lighting"
```

❌ **Không tốt:**
```
"cat"  # Quá ngắn
"make me a picture"  # Không rõ ràng
```

### 2. Tiết kiệm quota

- Tạo 1 ảnh trước để test prompt
- Chỉ tạo nhiều ảnh khi đã hài lòng với kết quả
- Kiểm tra quota trước khi chạy batch lớn

### 3. Tổ chức file

```bash
# Tạo thư mục theo chủ đề
python imagine_cli.py -t "token" -p "landscape" -o ./images/landscapes
python imagine_cli.py -t "token" -p "portrait" -o ./images/portraits
```

## Lưu ý bảo mật

⚠️ **QUAN TRỌNG:**

1. **Không commit token vào git**
2. **Không chia sẻ token công khai**
3. **Sử dụng biến môi trường cho token:**

```bash
# Lưu token vào file .env
echo 'CHATGPT_TOKEN=your_token_here' > .env

# Sử dụng trong script
export CHATGPT_TOKEN="your_token_here"
python imagine_cli.py --token "$CHATGPT_TOKEN" --prompt "..."
```

## Troubleshooting

### Chạy với verbose để xem log chi tiết

```bash
python imagine_cli.py -t "token" -p "test" -v
```

### Kiểm tra kết nối

```bash
# Test xem có kết nối được không
curl https://chatgpt.com
```

### Kiểm tra dependencies

```bash
python -c "import curl_cffi; print('OK')"
python -c "from PIL import Image; print('OK')"
```

## Hỗ trợ

Nếu gặp vấn đề:

1. Kiểm tra log với `--verbose`
2. Đảm bảo token còn hợp lệ
3. Kiểm tra quota còn lại
4. Thử với prompt đơn giản trước

## License

Xem file LICENSE trong repo gốc.

## Disclaimer

Tool này chỉ dùng cho mục đích học tập và nghiên cứu. Vui lòng tuân thủ Terms of Service của OpenAI.
