from __future__ import annotations

import html
import smtplib
from datetime import date
from email.message import EmailMessage
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.approvals import create_approval, get, mark_executed, mark_execution_failed, resolve
from app.broker import KiteExecutionClient
from app.config.settings import settings

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _base_url() -> str:
    return settings.public_base_url.rstrip("/")


def _send_html(subject: str, recipients: list[str], html_body: str, text_body: str) -> None:
    if not settings.smtp_host or not settings.smtp_username or not settings.smtp_password:
        raise RuntimeError("SMTP settings are not fully configured")
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.alert_from_email or settings.smtp_username
    message["To"] = ", ".join(recipients)
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)


def _approval_email(token: str, trade: dict) -> tuple[str, str, str]:
    recipients = settings.approval_recipients()
    rating = int(trade["rating"])
    symbol = html.escape(str(trade["symbol"]).upper())
    signal = html.escape(str(trade.get("signal", "BUY_CANDIDATE")))
    regime = html.escape(str(trade.get("market_regime", "—")))
    entry = float(trade["entry_price"])
    stop = float(trade["stop_loss"])
    target = float(trade["target_price"])
    qty = int(trade["quantity"])
    rr = float(trade["risk_reward"])
    risk = float(trade["capital_at_risk"])

    approve_links = []
    reject_links = []
    for recipient in recipients:
        q = f"recipient={quote(recipient)}"
        approve_links.append(
            f'<a href="{_base_url()}/api/approvals/{token}/action?decision=approve&{q}" '
            'style="display:inline-block;padding:14px 28px;background:#16803c;color:#fff;'
            'text-decoration:none;border-radius:10px;font-weight:800;margin:4px;">APPROVE</a>'
        )
        reject_links.append(
            f'<a href="{_base_url()}/api/approvals/{token}/action?decision=reject&{q}" '
            'style="display:inline-block;padding:14px 28px;background:#a61b2b;color:#fff;'
            'text-decoration:none;border-radius:10px;font-weight:800;margin:4px;">REJECT</a>'
        )

    subject = f"ModelX trade approval — {symbol} — Rating {rating}/100"
    body = f"""ModelX trade approval
{symbol} | Rating {rating}/100 | {signal}
Entry ₹{entry:.2f} | SL ₹{stop:.2f} | Target ₹{target:.2f} | Qty {qty}
Risk/reward {rr:.2f} | Capital at risk ₹{risk:.2f}
"""

    html_body = f"""<!doctype html>
<html><body style="margin:0;background:#f4f7fb;font-family:Arial,sans-serif;color:#182033;">
<div style="max-width:680px;margin:24px auto;background:#fff;border-radius:18px;overflow:hidden;
box-shadow:0 8px 30px rgba(20,35,60,.12);">
<div style="padding:26px 28px;background:#101a30;color:#fff;">
  <div style="font-size:13px;letter-spacing:1.4px;text-transform:uppercase;opacity:.75;">ModelX Trade Approval</div>
  <div style="font-size:30px;font-weight:800;margin-top:8px;">{symbol}</div>
  <div style="font-size:15px;margin-top:6px;opacity:.85;">{signal} · {regime}</div>
</div>
<div style="padding:28px;">
  <div style="text-align:center;border:1px solid #dce3ef;border-radius:16px;padding:18px;background:#f8faff;">
    <div style="font-size:12px;text-transform:uppercase;letter-spacing:1.5px;color:#667085;">ModelX Rating</div>
    <div style="font-size:64px;line-height:1;font-weight:900;margin:8px 0;">{rating}</div>
    <div style="font-size:14px;color:#667085;">out of 100</div>
  </div>
  <table style="width:100%;border-collapse:separate;border-spacing:8px;margin:18px -8px;">
    <tr>
      <td style="padding:13px;background:#f6f8fc;border-radius:10px;"><small>ENTRY</small><br><b>₹{entry:.2f}</b></td>
      <td style="padding:13px;background:#fff5f5;border-radius:10px;"><small>STOP LOSS</small><br><b>₹{stop:.2f}</b></td>
      <td style="padding:13px;background:#f2fbf5;border-radius:10px;"><small>TARGET</small><br><b>₹{target:.2f}</b></td>
    </tr>
    <tr>
      <td style="padding:13px;background:#f6f8fc;border-radius:10px;"><small>QUANTITY</small><br><b>{qty}</b></td>
      <td style="padding:13px;background:#f6f8fc;border-radius:10px;"><small>R:R</small><br><b>{rr:.2f}</b></td>
      <td style="padding:13px;background:#f6f8fc;border-radius:10px;"><small>RISK</small><br><b>₹{risk:.2f}</b></td>
    </tr>
  </table>
  <div style="padding:15px;border-left:4px solid #e1a900;background:#fffaf0;border-radius:8px;">
    <b>Important:</b> Approval authorises the configured ModelX execution path. Review the values above before clicking.
  </div>
  <div style="text-align:center;margin:24px 0 10px;">{"".join(approve_links)}</div>
  <div style="text-align:center;">{"".join(reject_links)}</div>
  <p style="font-size:12px;color:#7b8496;text-align:center;margin-top:24px;">
    Either authorised recipient's APPROVE action is sufficient. Approval links expire automatically.
  </p>
</div></div></body></html>"""
    return subject, body, html_body


@router.post("/send")
def send_trade_approval(
    symbol: str = Query(..., min_length=1, max_length=30),
    rating: int = Query(..., ge=0, le=100),
    signal: str = Query("BUY_CANDIDATE"),
    market_regime: str = Query("BULLISH_TREND"),
    entry_price: float = Query(..., gt=0),
    stop_loss: float = Query(..., gt=0),
    target_price: float = Query(..., gt=0),
    quantity: int = Query(..., gt=0),
    risk_reward: float = Query(..., gt=0),
    capital_at_risk: float = Query(..., ge=0),
) -> dict[str, object]:
    if not settings.approval_secret:
        raise HTTPException(status_code=503, detail="Approval secret is not configured")
    recipients = settings.approval_recipients()
    if not recipients:
        raise HTTPException(status_code=503, detail="Approval recipients are not configured")
    if signal != "BUY_CANDIDATE":
        raise HTTPException(status_code=400, detail="Only BUY_CANDIDATE signals can request trade approval")
    if risk_reward < settings.min_risk_reward:
        raise HTTPException(status_code=400, detail="Trade does not meet the configured minimum risk/reward")

    trade = {
        "symbol": symbol.upper(),
        "rating": rating,
        "signal": signal,
        "market_regime": market_regime,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "target_price": target_price,
        "quantity": quantity,
        "risk_reward": risk_reward,
        "capital_at_risk": capital_at_risk,
    }
    token, record = create_approval(trade)
    subject, text_body, html_body = _approval_email(token, trade)
    try:
        _send_html(subject, recipients, html_body, text_body)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Approval email delivery failed") from exc

    return {
        "sent": True,
        "approval_id": record["approval_id"],
        "recipients": recipients,
        "status": record["status"],
        "expires_at": record["expires_at"],
        "execution_mode": "LIVE" if settings.live_trading_enabled else "PAPER",
    }


def _execute(record: dict) -> dict:
    trade = record["trade"]
    if not settings.live_trading_enabled:
        return {
            "mode": "PAPER",
            "status": "PAPER_APPROVED",
            "symbol": trade["symbol"],
            "quantity": trade["quantity"],
        }

    try:
        result = KiteExecutionClient().place_approved_entry(
            symbol=trade["symbol"],
            quantity=int(trade["quantity"]),
        )
        return {"mode": "LIVE", "status": "ORDER_PLACED", **result}
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc


@router.get("/{token}/action", response_class=HTMLResponse)
def approval_action(
    token: str,
    decision: str = Query(...),
    recipient: str = Query(...),
) -> HTMLResponse:
    try:
        record = resolve(token, decision.lower(), recipient)
    except ValueError as exc:
        return HTMLResponse(
            f"<h2>ModelX approval</h2><p>{html.escape(str(exc))}</p>",
            status_code=400,
        )

    if record["status"] == "APPROVED":
        try:
            execution = _execute(record)
            mark_executed(record["approval_id"], execution)
        except Exception as exc:
            mark_execution_failed(record["approval_id"], str(exc))

    status = get(record["approval_id"]) or record
    message = {
        "EXECUTED": "Approval accepted and the configured execution action has been triggered.",
        "EXECUTION_FAILED": "Approval was accepted, but execution failed. Check ModelX logs.",
        "REJECTED": "Trade rejected.",
        "APPROVED": "Trade approved.",
    }.get(status["status"], status["status"])

    return HTMLResponse(
        f"""<!doctype html><html><body style="font-family:Arial;background:#f4f7fb;padding:40px;">
        <div style="max-width:560px;margin:auto;background:#fff;padding:30px;border-radius:16px;">
        <h1>ModelX</h1><h2>{html.escape(message)}</h2>
        <p>Symbol: <b>{html.escape(status["trade"]["symbol"])}</b></p>
        <p>Status: <b>{html.escape(status["status"])}</b></p>
        </div></body></html>"""
    )


@router.get("/{approval_id}")
def approval_status(approval_id: str) -> dict:
    record = get(approval_id)
    if not record:
        raise HTTPException(status_code=404, detail="Approval not found")
    return record
