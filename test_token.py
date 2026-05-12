#!/usr/bin/env python3
"""Test token - đọc từ data/accounts.json"""
import sys, json
sys.path.insert(0, '.')

from services.openai_backend_api import OpenAIBackendAPI, InvalidAccessTokenError

# Đọc token từ accounts.json
from pathlib import Path
accounts_file = Path(__file__).parent / "data" / "accounts.json"
try:
    accounts = json.loads(accounts_file.read_text())
    if not accounts:
        print("Không có account nào trong data/accounts.json")
        sys.exit(1)
except Exception as e:
    print(f"Lỗi đọc {accounts_file}: {e}")
    sys.exit(1)

for i, acc in enumerate(accounts):
    token = acc.get("access_token", "")
    print(f"\n{'='*60}")
    print(f"Account {i+1}: {token[:20]}...{token[-10:]}")
    print(f"  Length: {len(token)}")
    
    try:
        api = OpenAIBackendAPI(access_token=token)
        print("  Gọi get_user_info()...")
        info = api.get_user_info()
        print(f"  ✓ OK! Email={info.get('email')}, Type={info.get('type')}, Quota={info.get('quota')}, Status={info.get('status')}")
    except InvalidAccessTokenError as e:
        print(f"  ✗ InvalidAccessTokenError: {e}")
    except Exception as e:
        print(f"  ✗ {type(e).__name__}: {e}")
