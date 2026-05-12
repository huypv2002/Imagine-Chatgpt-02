from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from curl_cffi import requests

from services.storage.base import StorageBackend


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _clean(value: object) -> str:
    return str(value or "").strip()


def _sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hmac_sha256(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


class R2StorageBackend(StorageBackend):
    """Cloudflare R2 object storage backend for accounts/auth keys."""

    def __init__(self, settings: dict[str, object]):
        self.account_id = _clean(settings.get("account_id") or os.getenv("R2_ACCOUNT_ID"))
        self.access_key_id = _clean(settings.get("access_key_id") or os.getenv("R2_ACCESS_KEY_ID"))
        self.secret_access_key = _clean(settings.get("secret_access_key") or os.getenv("R2_SECRET_ACCESS_KEY"))
        self.bucket = _clean(settings.get("bucket") or os.getenv("R2_BUCKET"))
        self.prefix = _clean(settings.get("prefix") or os.getenv("R2_PREFIX")) or "chatgpt2api-db"
        self.accounts_key = f"{self.prefix.rstrip('/')}/accounts.json"
        self.auth_keys_key = f"{self.prefix.rstrip('/')}/auth_keys.json"
        self.session = requests.Session(impersonate="chrome", verify=True)

    def validate(self) -> None:
        missing = []
        if not self.account_id:
            missing.append("R2_ACCOUNT_ID")
        if not self.access_key_id:
            missing.append("R2_ACCESS_KEY_ID")
        if not self.secret_access_key:
            missing.append("R2_SECRET_ACCESS_KEY")
        if not self.bucket:
            missing.append("R2_BUCKET")
        if missing:
            raise ValueError(f"R2 storage config incomplete: missing {', '.join(missing)}")

    @property
    def endpoint(self) -> str:
        return f"https://{self.account_id}.r2.cloudflarestorage.com"

    def _aws_v4_headers(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        body: bytes = b"",
        extra_headers: dict[str, str] | None = None,
    ) -> tuple[str, dict[str, str]]:
        now = _utc_now()
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        encoded_query = urlencode(sorted((query or {}).items()))
        payload_hash = _sha256_hex(body)
        host = f"{self.account_id}.r2.cloudflarestorage.com"
        headers = {
            "host": host,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
        }
        if extra_headers:
            for key, value in extra_headers.items():
                headers[key.lower()] = value.strip()
        sorted_items = sorted((key.lower(), " ".join(str(value).strip().split())) for key, value in headers.items())
        canonical_headers = "".join(f"{key}:{value}\n" for key, value in sorted_items)
        signed_headers = ";".join(key for key, _ in sorted_items)
        canonical_request = "\n".join([
            method.upper(),
            path,
            encoded_query,
            canonical_headers,
            signed_headers,
            payload_hash,
        ])
        credential_scope = f"{date_stamp}/auto/s3/aws4_request"
        string_to_sign = "\n".join([
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            _sha256_hex(canonical_request.encode("utf-8")),
        ])
        k_date = _hmac_sha256(("AWS4" + self.secret_access_key).encode("utf-8"), date_stamp)
        k_region = hmac.new(k_date, b"auto", hashlib.sha256).digest()
        k_service = hmac.new(k_region, b"s3", hashlib.sha256).digest()
        k_signing = hmac.new(k_service, b"aws4_request", hashlib.sha256).digest()
        signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        authorization = (
            "AWS4-HMAC-SHA256 "
            f"Credential={self.access_key_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )
        request_headers = {key: value for key, value in headers.items()}
        request_headers["authorization"] = authorization
        return encoded_query, request_headers

    def _request(
        self,
        method: str,
        key: str = "",
        *,
        query: dict[str, str] | None = None,
        body: bytes = b"",
        extra_headers: dict[str, str] | None = None,
        timeout: float = 60.0,
    ):
        object_path = f"/{self.bucket}"
        if key:
            object_path += f"/{quote(key.lstrip('/'), safe='/')}"
        encoded_query, headers = self._aws_v4_headers(method, object_path, query=query, body=body, extra_headers=extra_headers)
        url = f"{self.endpoint}{object_path}"
        if encoded_query:
            url += f"?{encoded_query}"
        return self.session.request(method.upper(), url, headers=headers, data=body, timeout=timeout)

    @staticmethod
    def _load_json_value(raw: bytes | str | None) -> Any:
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except Exception:
            return None

    def _download_key(self, key: str) -> Any:
        response = self._request("GET", key, timeout=60.0)
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise RuntimeError(f"R2 download failed for {key}: HTTP {response.status_code}")
        return self._load_json_value(response.content)

    def _upload_key(self, key: str, payload: Any) -> None:
        body = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        response = self._request(
            "PUT",
            key,
            body=body,
            extra_headers={"content-type": "application/json"},
            timeout=60.0,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"R2 upload failed for {key}: HTTP {response.status_code}")

    def load_accounts(self) -> list[dict[str, Any]]:
        value = self._download_key(self.accounts_key)
        return value if isinstance(value, list) else []

    def save_accounts(self, accounts: list[dict[str, Any]]) -> None:
        self._upload_key(self.accounts_key, accounts)

    def load_auth_keys(self) -> list[dict[str, Any]]:
        value = self._download_key(self.auth_keys_key)
        if isinstance(value, dict):
            value = value.get("items")
        return value if isinstance(value, list) else []

    def save_auth_keys(self, auth_keys: list[dict[str, Any]]) -> None:
        self._upload_key(self.auth_keys_key, {"items": auth_keys})

    def health_check(self) -> dict[str, Any]:
        try:
            self.validate()
            response = self._request("GET", query={"list-type": "2", "max-keys": "1"}, timeout=30.0)
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code}")
            return {
                "status": "healthy",
                "backend": "r2",
                "bucket": self.bucket,
                "prefix": self.prefix,
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "backend": "r2",
                "error": str(exc),
            }

    def get_backend_info(self) -> dict[str, Any]:
        return {
            "type": "r2",
            "description": "Cloudflare R2 storage",
            "bucket": self.bucket,
            "prefix": self.prefix,
            "account_id": self.account_id,
        }
