from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from services.account_service import account_service
from services.image_task_service import image_task_service
from services.log_service import LOG_TYPE_ACCOUNT, LOG_TYPE_CALL, log_service


def _day(value: str | None = None) -> str:
    if value and len(value.strip()) >= 10:
        return value.strip()[:10]
    return datetime.now().strftime("%Y-%m-%d")


def _status_bucket(status: str) -> str:
    lowered = status.lower()
    if lowered == "success":
        return "success"
    if lowered == "failed":
        return "failed"
    return "other"


def _detail(item: dict[str, Any]) -> dict[str, Any]:
    detail = item.get("detail")
    return detail if isinstance(detail, dict) else {}


class DashboardService:
    def get_summary(self, date: str = "") -> dict[str, Any]:
        day = _day(date)
        accounts = account_service.list_accounts()
        account_counts = Counter(str(account.get("status") or "正常") for account in accounts)
        calls = log_service.list_all(type=LOG_TYPE_CALL, start_date=day, end_date=day)
        account_logs = log_service.list_all(type=LOG_TYPE_ACCOUNT, start_date=day, end_date=day)
        all_call_logs = log_service.list_all(type=LOG_TYPE_CALL)

        today_image_logs = [item for item in calls if str(_detail(item).get("endpoint") or "").startswith("/v1/images/")]
        today_video_logs = [
            item for item in calls
            if "video" in str(_detail(item).get("endpoint") or "").lower()
            or "视频" in str(item.get("summary") or "")
        ]

        status_counts = Counter(_status_bucket(str(_detail(item).get("status") or "")) for item in calls)
        endpoint_counts = Counter(str(_detail(item).get("endpoint") or "") for item in calls)
        top_endpoints = [
            {"endpoint": endpoint, "count": count}
            for endpoint, count in endpoint_counts.most_common(5)
            if endpoint
        ]

        account_created_today = 0
        account_deleted_today = 0
        for item in account_logs:
            detail = _detail(item)
            summary = str(item.get("summary") or "")
            account_created_today += int(detail.get("added") or 0) if "新增" in summary else 0
            account_deleted_today += int(detail.get("removed") or 0) if "删除" in summary else 0

        recent_activity = []
        for item in sorted(log_service.list_all(), key=lambda value: str(value.get("time") or ""), reverse=True)[:12]:
            detail = item.get("detail") if isinstance(item.get("detail"), dict) else {}
            recent_activity.append(
                {
                    "id": item.get("id"),
                    "time": item.get("time"),
                    "type": item.get("type"),
                    "summary": item.get("summary"),
                    "status": detail.get("status"),
                    "endpoint": detail.get("endpoint"),
                    "actor": detail.get("key_name") or detail.get("key_id") or "",
                }
            )

        unique_call_actors = len({str(_detail(item).get("key_id") or "") for item in calls if str(_detail(item).get("key_id") or "")})
        successful_image_jobs = sum(1 for item in today_image_logs if str(_detail(item).get("status") or "") == "success")
        failed_image_jobs = sum(1 for item in today_image_logs if str(_detail(item).get("status") or "") == "failed")

        return {
            "date": day,
            "accounts": {
                "total": len(accounts),
                "active": int(account_counts.get("正常", 0)),
                "limited": int(account_counts.get("限流", 0)),
                "abnormal": int(account_counts.get("异常", 0)),
                "disabled": int(account_counts.get("禁用", 0)),
                "created_today": account_created_today,
                "deleted_today": account_deleted_today,
            },
            "calls": {
                "today_total": len(calls),
                "today_success": int(status_counts.get("success", 0)),
                "today_failed": int(status_counts.get("failed", 0)),
                "today_other": int(status_counts.get("other", 0)),
                "all_time_total": len(all_call_logs),
                "unique_actors_today": unique_call_actors,
            },
            "images": {
                "today_total": len(today_image_logs),
                "today_success": successful_image_jobs,
                "today_failed": failed_image_jobs,
                "all_time_total": sum(1 for item in all_call_logs if str(_detail(item).get("endpoint") or "").startswith("/v1/images/") and str(_detail(item).get("status") or "") == "success"),
            },
            "videos": {
                "today_total": len(today_video_logs),
                "all_time_total": 0,
            },
            "tasks": {
                "total": len(image_task_service.list_all_tasks()),
            },
            "endpoints": top_endpoints,
            "recent_activity": recent_activity,
        }


dashboard_service = DashboardService()
