import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger("n8n_service")

def is_n8n_enabled() -> bool:
    """Checks whether n8n workflow integration is enabled."""
    val = os.getenv("N8N_ENABLED", "true").strip().lower()
    return val in ("true", "1", "yes", "on")

def is_dev_otp_exposed() -> bool:
    """
    Checks if OTP should be exposed in API response for local development.
    When False, OTP is only exposed if real email delivery could not be completed.
    """
    val = os.getenv("DEV_EXPOSE_OTP", "false").strip().lower()
    return val in ("true", "1", "yes", "on")

def get_n8n_webhook_url() -> str:
    """Returns the configured n8n webhook URL."""
    return os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/send-otp").strip()

def send_otp_via_n8n(
    email: str,
    otp: str,
    institution_name: str,
    role: str,
    purpose: str,
    subject: str,
    expires_in_minutes: int = 5
) -> Dict[str, Any]:
    """
    Dispatches the generated OTP to the n8n automation webhook.
    n8n will execute the email workflow and send the formatted email.
    """
    if not is_n8n_enabled():
        return {
            "success": False,
            "dispatched": False,
            "email_delivered": False,
            "message": "n8n integration is disabled via configuration."
        }

    webhook_url = get_n8n_webhook_url()
    timeout_sec = float(os.getenv("N8N_TIMEOUT", "5.0"))
    api_key = os.getenv("N8N_API_KEY", "").strip()

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Institutional-Compliance-Audit-System/2.0"
    }
    if api_key:
        headers["X-N8N-API-KEY"] = api_key
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "event": "otp_dispatch",
        "email": email,
        "otp": otp,
        "institution_name": institution_name,
        "role": role,
        "purpose": purpose,
        "subject": subject,
        "expires_in_minutes": expires_in_minutes,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    try:
        with httpx.Client(timeout=timeout_sec) as client:
            response = client.post(webhook_url, json=payload, headers=headers)

        if response.status_code in (200, 201, 202, 204):
            data = {}
            try:
                data = response.json()
            except Exception:
                pass
            
            # Check if actual email was delivered by n8n/bridge
            email_delivered = data.get("email_delivered", False) if isinstance(data, dict) else False
            
            print(f"[n8n DISPATCH SUCCESS] Handed off OTP for {email} to n8n webhook ({webhook_url}) - HTTP {response.status_code} (Real Email Delivered: {email_delivered})")
            return {
                "success": True,
                "dispatched": True,
                "email_delivered": email_delivered,
                "provider": "n8n",
                "status_code": response.status_code,
                "details": data
            }
        else:
            print(f"[n8n DISPATCH WARNING] Webhook {webhook_url} returned status {response.status_code}: {response.text[:200]}")
            return {
                "success": False,
                "dispatched": False,
                "email_delivered": False,
                "provider": "n8n",
                "status_code": response.status_code,
                "error": response.text[:200]
            }

    except httpx.ConnectError:
        print(f"[n8n NOTICE] Could not connect to n8n webhook at {webhook_url} (n8n not running on this port).")
        return {
            "success": False,
            "dispatched": False,
            "email_delivered": False,
            "provider": "n8n",
            "error": "Connection refused - n8n service offline"
        }
    except httpx.TimeoutException:
        print(f"[n8n NOTICE] n8n webhook timed out after {timeout_sec}s.")
        return {
            "success": False,
            "dispatched": False,
            "email_delivered": False,
            "provider": "n8n",
            "error": "n8n request timeout"
        }
    except Exception as e:
        print(f"[n8n NOTICE] Error dispatching to n8n: {e}")
        return {
            "success": False,
            "dispatched": False,
            "email_delivered": False,
            "provider": "n8n",
            "error": str(e)
        }
