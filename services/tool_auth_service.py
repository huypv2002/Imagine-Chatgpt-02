from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value: object) -> str:
    return str(value or "").strip()


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{base64.urlsafe_b64encode(salt).decode('ascii')}${base64.urlsafe_b64encode(digest).decode('ascii')}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        salt_b64, digest_b64 = encoded.split("$", 1)
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
    except Exception:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return hmac.compare_digest(actual, expected)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ToolAuthConfig:
    backend: str
    file_path: Path
    r2_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket: str
    r2_prefix: str


class _JsonStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(data, dict):
            data = data.get("items")
        return data if isinstance(data, list) else []

    def save(self, items: list[dict[str, Any]]) -> None:
        self.path.write_text(json.dumps({"items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class _R2Store:
    def __init__(self, cfg: ToolAuthConfig):
        self.account_id = cfg.r2_account_id
        self.access_key_id = cfg.r2_access_key_id
        self.secret_access_key = cfg.r2_secret_access_key
        self.bucket = cfg.r2_bucket
        self.prefix = cfg.r2_prefix.strip().strip("/") or "tool-auth"
        self.object_key = f"{self.prefix}/users.json"
        self.session = requests.Session()
        if not self.account_id or not self.access_key_id or not self.secret_access_key or not self.bucket:
            raise ValueError("Thiếu cấu hình Cloudflare R2 cho tool auth")

    def _sign(self, method: str, key: str, body: bytes, content_type: str) -> dict[str, str]:
        import hashlib as _hashlib
        import hmac as _hmac
        from datetime import datetime, timezone as _timezone

        host = f"{self.bucket}.{self.account_id}.r2.cloudflarestorage.com"
        now = datetime.now(_timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        payload_hash = _hashlib.sha256(body).hexdigest()
        canonical_uri = f"/{key}"
        canonical_query = ""
        headers = {
            "content-type": content_type,
            "host": host,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
        }
        sorted_headers = sorted((k, " ".join(v.strip().split())) for k, v in headers.items())
        canonical_headers = "".join(f"{k}:{v}\n" for k, v in sorted_headers)
        signed_headers = ";".join(k for k, _ in sorted_headers)
        canonical_request = "\n".join([
            method.upper(),
            canonical_uri,
            canonical_query,
            canonical_headers,
            signed_headers,
            payload_hash,
        ])
        scope = f"{date_stamp}/auto/s3/aws4_request"
        string_to_sign = "\n".join([
            "AWS4-HMAC-SHA256",
            amz_date,
            scope,
            _hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ])
        def sign(key: bytes, msg: str) -> bytes:
            return _hmac.new(key, msg.encode("utf-8"), _hashlib.sha256).digest()
        k_date = sign(("AWS4" + self.secret_access_key).encode("utf-8"), date_stamp)
        k_region = sign(k_date, "auto")
        k_service = sign(k_region, "s3")
        k_signing = sign(k_service, "aws4_request")
        signature = _hmac.new(k_signing, string_to_sign.encode("utf-8"), _hashlib.sha256).hexdigest()
        authorization = (
            f"AWS4-HMAC-SHA256 Credential={self.access_key_id}/{scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        return {
            "Host": host,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
            "Authorization": authorization,
            "Content-Type": content_type,
        }

    def load(self) -> list[dict[str, Any]]:
        url = f"https://{self.bucket}.{self.account_id}.r2.cloudflarestorage.com/{self.object_key}"
        headers = self._sign("GET", self.object_key, b"", "application/json")
        resp = self.session.get(url, headers=headers, timeout=30)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            data = data.get("items")
        return data if isinstance(data, list) else []

    def save(self, items: list[dict[str, Any]]) -> None:
        body = json.dumps({"items": items}, ensure_ascii=False, indent=2).encode("utf-8")
        url = f"https://{self.bucket}.{self.account_id}.r2.cloudflarestorage.com/{self.object_key}"
        headers = self._sign("PUT", self.object_key, body, "application/json")
        resp = self.session.put(url, headers=headers, data=body, timeout=30)
        resp.raise_for_status()


class ToolAuthService:
    def __init__(self):
        backend = _clean(os.getenv("CHATGPT2API_TOOL_AUTH_BACKEND") or "json").lower()
        file_path = Path(os.getenv("CHATGPT2API_TOOL_AUTH_FILE") or (Path(__file__).resolve().parents[1] / "data" / "tool_users.json"))
        self.cfg = ToolAuthConfig(
            backend=backend,
            file_path=file_path,
            r2_account_id=_clean(os.getenv("CHATGPT2API_TOOL_R2_ACCOUNT_ID")),
            r2_access_key_id=_clean(os.getenv("CHATGPT2API_TOOL_R2_ACCESS_KEY_ID")),
            r2_secret_access_key=_clean(os.getenv("CHATGPT2API_TOOL_R2_SECRET_ACCESS_KEY")),
            r2_bucket=_clean(os.getenv("CHATGPT2API_TOOL_R2_BUCKET")),
            r2_prefix=_clean(os.getenv("CHATGPT2API_TOOL_R2_PREFIX") or "tool-auth"),
        )
        self._store = self._build_store()

    def _build_store(self):
        if self.cfg.backend in {"r2", "cloudflare_r2"}:
            return _R2Store(self.cfg)
        return _JsonStore(self.cfg.file_path)

    def _load(self) -> list[dict[str, Any]]:
        try:
            raw = self._store.load()
        except Exception:
            return []
        return [item for item in raw if isinstance(item, dict)]

    def _save(self, items: list[dict[str, Any]]) -> None:
        self._store.save(items)

    @staticmethod
    def _normalize_username(value: str) -> str:
        return _clean(value).lower()

    def _normalize_user(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        username = self._normalize_username(raw.get("username"))
        password_hash = _clean(raw.get("password_hash"))
        if not username or not password_hash:
            return None
        return {
            "id": _clean(raw.get("id")) or secrets.token_hex(8),
            "username": username,
            "display_name": _clean(raw.get("display_name")) or username,
            "password_hash": password_hash,
            "session_hash": _clean(raw.get("session_hash")) or "",
            "enabled": bool(raw.get("enabled", True)),
            "created_at": _clean(raw.get("created_at")) or _now_iso(),
            "updated_at": _clean(raw.get("updated_at")) or _now_iso(),
            "last_login_at": _clean(raw.get("last_login_at")) or "",
        }

    def _items(self) -> list[dict[str, Any]]:
        return [item for item in (self._normalize_user(raw) for raw in self._load()) if item is not None]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._save(items)

    def register(self, username: str, password: str, display_name: str = "") -> tuple[dict[str, Any], str]:
        username = self._normalize_username(username)
        password = _clean(password)
        display_name = _clean(display_name) or username
        if not username:
            raise ValueError("Tên đăng nhập không được để trống")
        if not password:
            raise ValueError("Mật khẩu không được để trống")
        items = self._items()
        if any(item["username"] == username for item in items):
            raise ValueError("Tên đăng nhập đã tồn tại")
        raw_session = secrets.token_urlsafe(24)
        user = {
            "id": secrets.token_hex(8),
            "username": username,
            "display_name": display_name,
            "password_hash": _hash_password(password),
            "session_hash": _hash_token(raw_session),
            "enabled": True,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "last_login_at": _now_iso(),
        }
        items.append(user)
        self._write_items(items)
        return self._public_user(user), raw_session

    def login(self, username: str, password: str) -> tuple[dict[str, Any], str]:
        username = self._normalize_username(username)
        password = _clean(password)
        if not username or not password:
            raise ValueError("Vui lòng nhập tên đăng nhập và mật khẩu")
        items = self._items()
        for index, item in enumerate(items):
            if item["username"] != username or not item.get("enabled", True):
                continue
            if not _verify_password(password, item["password_hash"]):
                break
            raw_session = secrets.token_urlsafe(24)
            next_item = dict(item)
            next_item["session_hash"] = _hash_token(raw_session)
            next_item["updated_at"] = _now_iso()
            next_item["last_login_at"] = _now_iso()
            items[index] = next_item
            self._write_items(items)
            return self._public_user(next_item), raw_session
        raise ValueError("Tên đăng nhập hoặc mật khẩu không đúng")

    def validate_session(self, session: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(session, dict):
            return None
        username = self._normalize_username(session.get("username"))
        token = _clean(session.get("token"))
        if not username or not token:
            return None
        token_hash = _hash_token(token)
        for item in self._items():
            if item["username"] != username or not item.get("enabled", True):
                continue
            if hmac.compare_digest(item.get("session_hash") or "", token_hash):
                return self._public_user(item)
        return None

    @staticmethod
    def _public_user(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item.get("id"),
            "username": item.get("username"),
            "display_name": item.get("display_name"),
            "role": "user",
        }


tool_auth_service = ToolAuthService()
