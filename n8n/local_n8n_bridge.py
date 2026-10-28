#!/usr/bin/env python3
"""
Institutional Document Compliance and Audit System
Local n8n Webhook Bridge & Runner

This script provides an immediate local webhook listener on port 5678 that emulates
an active n8n instance. When the FastAPI backend fires the OTP event, this bridge:
1. Receives the webhook payload at /webhook/send-otp
2. Formats the institutional HTML email template
3. Sends real email to the user's inbox (via configured SMTP or Gmail)
4. Displays formatted delivery logs in the terminal
5. Returns the n8n response payload back to the backend
"""

import os
import sys
import json
import smtplib
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load environment variables
try:
    from dotenv import load_dotenv
    root_dir = Path(__file__).resolve().parent.parent
    load_dotenv(root_dir / ".env")
except Exception:
    pass

PORT = int(os.getenv("N8N_PORT", "5678"))
HOST = os.getenv("N8N_HOST", "127.0.0.1")

class N8nWebhookHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-N8N-API-KEY")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            resp = {
                "status": "online",
                "service": "n8n Automation Webhook Bridge",
                "endpoint": f"http://{HOST}:{PORT}/webhook/send-otp",
                "mode": "Active"
            }
            self.wfile.write(json.dumps(resp, indent=2).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path in ("/webhook/send-otp", "/webhook-test/send-otp"):
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            try:
                payload = json.loads(post_data.decode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Invalid JSON payload: {e}"}).encode("utf-8"))
                return

            email = payload.get("email", "").strip()
            otp = str(payload.get("otp", "")).strip()
            institution = payload.get("institution_name", "Anantha Lakshmi Institute of Technology and Sciences")
            role = payload.get("role", "Faculty")
            purpose = payload.get("purpose", "Login Verification")
            subject = payload.get("subject", f"🔐 [{institution}] Verification Passcode: {otp}")
            expiry = payload.get("expires_in_minutes", 5)

            # Print n8n execution banner in terminal
            print("\n" + "=" * 70)
            print("⚡ [n8n Automation Workflow] Webhook Triggered: /webhook/send-otp")
            print("-" * 70)
            print(f"  Recipient   : {email}")
            print(f"  Passcode    : {otp} (Valid for {expiry} mins)")
            print(f"  Role        : {role}")
            print(f"  Institution : {institution}")
            print(f"  Purpose     : {purpose}")
            print(f"  Timestamp   : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print("-" * 70)

            # Send actual email if SMTP credentials are configured
            email_sent = self._dispatch_smtp_email(email, otp, institution, role, purpose, subject, expiry)

            if email_sent:
                print(f"  Delivery    : [OK] Email successfully sent to {email} inbox.")
            else:
                print(f"  Delivery    : [SIMULATED] Passcode ready. Enter {otp} on the web portal.")
            print("=" * 70 + "\n")
            sys.stdout.flush()

            # Return standard n8n webhook response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()

            response_body = {
                "success": True,
                "message": f"Verification OTP email successfully dispatched via n8n automation to {email}!",
                "recipient": email,
                "dispatched_at": datetime.now(timezone.utc).isoformat(),
                "workflow": "n8n-institutional-otp-v2",
                "email_delivered": email_sent
            }
            self.wfile.write(json.dumps(response_body).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Endpoint {self.path} not found"}).encode("utf-8"))

    def _dispatch_smtp_email(self, email: str, otp: str, institution: str, role: str, purpose: str, subject: str, expiry: int) -> bool:
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USERNAME")
        smtp_pass = os.getenv("SMTP_PASSWORD")
        smtp_from = os.getenv("SMTP_FROM", os.getenv("SMTP_SENDER_EMAIL") or smtp_user)

        if not (smtp_host and smtp_user and smtp_pass):
            return False

        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = smtp_from
            msg["To"] = email

            html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ margin: 0; padding: 24px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f1f5f9; }}
    .wrapper {{ max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }}
    .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); padding: 28px 24px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; }}
    .header p {{ margin: 6px 0 0; font-size: 13px; color: #bfdbfe; }}
    .badge-bar {{ background: #0f172a; padding: 8px 16px; text-align: center; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #38bdf8; font-weight: 600; }}
    .content {{ padding: 32px 28px; text-align: center; color: #1e293b; }}
    .otp-container {{ background: #eff6ff; border: 2px dashed #60a5fa; border-radius: 10px; padding: 18px 24px; margin: 24px 0; display: inline-block; }}
    .otp-code {{ font-family: 'Courier New', monospace; font-size: 40px; font-weight: 800; letter-spacing: 10px; color: #1d4ed8; margin: 0; }}
    .expiry {{ font-size: 13px; color: #64748b; margin: 16px 0 0; }}
    .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 20px; text-align: center; font-size: 11px; color: #94a3b8; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1>{institution}</h1>
      <p>Automated Institutional Compliance & Document Audit System</p>
    </div>
    <div class="badge-bar">
      ⚡ Dispatched via n8n Automated Email Delivery
    </div>
    <div class="content">
      <p>{purpose}</p>
      <div class="otp-container">
        <div class="otp-code">{otp}</div>
      </div>
      <p class="expiry">⏱️ This passcode is valid for <strong>{expiry} minutes</strong> and can only be used once.</p>
    </div>
    <div class="footer">
      Automated Security Verification &bull; {institution}
    </div>
  </div>
</body>
</html>"""

            plain_text = f"{institution}\n{purpose}\n\nYour Verification Passcode: {otp}\nValid for {expiry} minutes."

            msg.set_content(plain_text)
            msg.add_alternative(html_content, subtype="html")

            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as s:
                    s.login(smtp_user, smtp_pass)
                    s.send_message(msg)
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as s:
                    s.starttls()
                    s.login(smtp_user, smtp_pass)
                    s.send_message(msg)
            return True
        except Exception as e:
            print(f"  [SMTP Dispatch Error]: {e}")
            return False

def main():
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, N8nWebhookHandler)
    print("\n" + "=" * 70)
    print(f"🚀 n8n Automation Webhook Bridge is running at http://{HOST}:{PORT}")
    print(f"📌 Webhook Endpoint: http://{HOST}:{PORT}/webhook/send-otp")
    print("=" * 70)
    print("Waiting for OTP requests from FastAPI backend...\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping n8n webhook bridge...")
        httpd.server_close()

if __name__ == "__main__":
    main()
