from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from app.config.settings import settings


_APPROVALS: dict[str, dict[str, Any]] = {}


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _sign(payload: str) -> str:
    if not settings.approval_secret:
        raise RuntimeError("Approval secret is not configured")
    return _b64(hmac.new(settings.approval_secret.encode(), payload.encode(), hashlib.sha256).digest())


def create_approval(trade: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    approval_id = uuid4().hex
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.approval_ttl_minutes)
    record = {
        "approval_id": approval_id,
        "status": "PENDING",
        "trade": trade,
        "approved_by": None,
        "rejected_by": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at.isoformat(),
    }
    _APPROVALS[approval_id] = record

    payload = _b64(json.dumps(
        {"approval_id": approval_id, "exp": int(expires_at.timestamp())},
        separators=(",", ":"),
        sort_keys=True,
    ).encode())
    return f"{payload}.{_sign(payload)}", record


def resolve(token: str, decision: str, recipient: str) -> dict[str, Any]:
    try:
        payload, signature = token.split(".", 1)
        if not hmac.compare_digest(signature, _sign(payload)):
            raise ValueError("Invalid approval signature")
        data = json.loads(_unb64(payload))
    except Exception as exc:
        raise ValueError("Invalid approval link") from exc

    if int(data["exp"]) < int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("Approval link has expired")

    allowed = settings.approval_recipients()
    if recipient.lower() not in allowed:
        raise ValueError("Recipient is not authorised for this approval")

    record = _APPROVALS.get(data["approval_id"])
    if not record:
        raise ValueError("Approval is no longer available; the service may have restarted")

    if record["status"] in {"EXECUTED", "EXECUTION_FAILED", "REJECTED", "EXPIRED"}:
        return record

    if decision == "reject":
        record["rejected_by"].append(recipient.lower())
        record["status"] = "REJECTED"
        return record

    if decision != "approve":
        raise ValueError("Decision must be approve or reject")

    record["status"] = "APPROVED"
    record["approved_by"] = recipient.lower()
    return record


def get(approval_id: str) -> dict[str, Any] | None:
    return _APPROVALS.get(approval_id)


def mark_executed(approval_id: str, execution: dict[str, Any]) -> dict[str, Any]:
    record = _APPROVALS[approval_id]
    record["status"] = "EXECUTED"
    record["execution"] = execution
    return record


def mark_execution_failed(approval_id: str, error: str) -> dict[str, Any]:
    record = _APPROVALS[approval_id]
    record["status"] = "EXECUTION_FAILED"
    record["execution_error"] = error
    return record
