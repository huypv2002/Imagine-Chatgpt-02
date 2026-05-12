#!/usr/bin/env python3
"""
CLI Tool đơn giản cho chức năng Imagine 2.0 (Text-to-Image)
Chỉ tập trung vào việc tạo ảnh từ text prompt
"""

import argparse
import base64
import sys
from pathlib import Path
from typing import Optional

from services.openai_backend_api import OpenAIBackendAPI, InvalidAccessTokenError
from utils.log import logger


def save_image(image_data: bytes, output_path: Path, index: int = 0) -> None:
    """Lưu ảnh vào file"""
    if len(image_data) == 0:
        logger.error(f"Không có dữ liệu ảnh để lưu")
        return
    
    # Tạo tên file với index nếu có nhiều ảnh
    if index > 0:
        stem = output_path.stem
        suffix = output_path.suffix
        output_path = output_path.parent / f"{stem}_{index}{suffix}"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_data)
    logger.info(f"✓ Đã lưu ảnh: {output_path}")


def generate_image(
    access_token: str,
    prompt: str,
    model: str = "gpt-image-2",
    output_dir: str = "./output",
    num_images: int = 1,
) -> bool:
    """
    Tạo ảnh từ text prompt
    
    Args:
        access_token: ChatGPT access token
        prompt: Mô tả ảnh cần tạo
        model: Model sử dụng (gpt-image-2 hoặc codex-gpt-image-2)
        output_dir: Thư mục lưu ảnh
        num_images: Số lượng ảnh cần tạo (1-4)
    
    Returns:
        True nếu thành công, False nếu thất bại
    """
    try:
        logger.info(f"🎨 Bắt đầu tạo ảnh với prompt: '{prompt}'")
        logger.info(f"📦 Model: {model}")
        logger.info(f"🔢 Số lượng: {num_images}")
        
        # Khởi tạo API client
        api = OpenAIBackendAPI(access_token=access_token)
        
        # Kiểm tra thông tin tài khoản
        logger.info("🔍 Đang kiểm tra thông tin tài khoản...")
        user_info = api.get_user_info()
        logger.info(f"✓ Email: {user_info.get('email')}")
        logger.info(f"✓ Loại tài khoản: {user_info.get('type')}")
        logger.info(f"✓ Quota còn lại: {user_info.get('quota')}")
        logger.info(f"✓ Trạng thái: {user_info.get('status')}")
        
        if user_info.get('status') == '限流':
            logger.warning("⚠️  Tài khoản đang bị giới hạn tốc độ!")
            restore_at = user_info.get('restore_at')
            if restore_at:
                logger.warning(f"⏰ Sẽ khôi phục lúc: {restore_at}")
        
        # Tạo ảnh
        logger.info("🚀 Đang tạo ảnh...")
        conversation_id = None
        file_ids = []
        sediment_ids = []
        
        # Stream conversation để lấy kết quả
        for event_data in api.stream_conversation(
            prompt=prompt,
            model=model,
            system_hints=["picture_v2"]
        ):
            # Parse event data để lấy conversation_id và file_ids
            import json
            try:
                # event_data có thể là string JSON
                if isinstance(event_data, str):
                    data = json.loads(event_data)
                else:
                    data = event_data
                    
                if "conversation_id" in data:
                    conversation_id = data["conversation_id"]
                    logger.debug(f"Conversation ID: {conversation_id}")
                
                # Kiểm tra message có chứa file_ids không
                message = data.get("message", {})
                content = message.get("content", {})
                if content.get("content_type") == "multimodal_text":
                    for part in content.get("parts", []):
                        if isinstance(part, dict) and "asset_pointer" in part:
                            pointer = part["asset_pointer"]
                            if pointer.startswith("file-service://"):
                                file_id = pointer.replace("file-service://", "")
                                if file_id not in file_ids:
                                    file_ids.append(file_id)
                            elif pointer.startswith("sediment://"):
                                sediment_id = pointer.replace("sediment://", "")
                                if sediment_id not in sediment_ids:
                                    sediment_ids.append(sediment_id)
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass
        
        logger.info("✓ Đã nhận phản hồi từ server")
        
        # Resolve URLs và download ảnh
        if conversation_id:
            logger.info("🔗 Đang lấy URL ảnh...")
            urls = api.resolve_conversation_image_urls(
                conversation_id=conversation_id,
                file_ids=file_ids,
                sediment_ids=sediment_ids,
                poll=True
            )
            
            if not urls:
                logger.error("❌ Không tìm thấy URL ảnh")
                return False
            
            logger.info(f"✓ Tìm thấy {len(urls)} ảnh")
            
            # Download và lưu ảnh
            logger.info("⬇️  Đang tải ảnh...")
            images = api.download_image_bytes(urls)
            
            output_path = Path(output_dir)
            for idx, image_data in enumerate(images):
                filename = f"imagine_{conversation_id}_{idx}.png"
                save_image(image_data, output_path / filename, 0)
            
            logger.info(f"🎉 Hoàn thành! Đã tạo {len(images)} ảnh")
            return True
        else:
            logger.error("❌ Không nhận được conversation_id")
            return False
            
    except InvalidAccessTokenError as e:
        logger.error(f"❌ Access token không hợp lệ: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="CLI Tool cho Imagine 2.0 - Tạo ảnh từ text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  %(prog)s --token "your_access_token" --prompt "một con mèo trong không gian"
  %(prog)s -t "token" -p "cyberpunk city at night" -n 2 -o ./my_images
  %(prog)s -t "token" -p "beautiful sunset" --model codex-gpt-image-2
        """
    )
    
    parser.add_argument(
        "-t", "--token",
        required=True,
        help="ChatGPT access token (bắt buộc)"
    )
    
    parser.add_argument(
        "-p", "--prompt",
        required=True,
        help="Mô tả ảnh cần tạo (bắt buộc)"
    )
    
    parser.add_argument(
        "-m", "--model",
        default="gpt-image-2",
        choices=["gpt-image-2", "codex-gpt-image-2"],
        help="Model sử dụng (mặc định: gpt-image-2)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="./output",
        help="Thư mục lưu ảnh (mặc định: ./output)"
    )
    
    parser.add_argument(
        "-n", "--num",
        type=int,
        default=1,
        choices=[1, 2, 3, 4],
        help="Số lượng ảnh cần tạo (1-4, mặc định: 1)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Hiển thị log chi tiết"
    )
    
    args = parser.parse_args()
    
    # Cấu hình log level
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # Chạy generate
    success = generate_image(
        access_token=args.token,
        prompt=args.prompt,
        model=args.model,
        output_dir=args.output,
        num_images=args.num,
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
