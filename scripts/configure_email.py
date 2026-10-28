#!/usr/bin/env python3
"""
Institutional Document Compliance & Audit System
Interactive Email / SMTP Configuration & Test Utility

Use this script to connect your Gmail account (via Google App Password) or any institutional SMTP server
so that real OTPs are delivered directly to your inbox.
"""

import os
import sys
import smtplib
from pathlib import Path
from email.message import EmailMessage

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

def send_test_email(smtp_host, smtp_port, smtp_user, smtp_pass, recipient_email):
    print(f"\n[*] Testing connection to {smtp_host}:{smtp_port}...")
    msg = EmailMessage()
    msg["Subject"] = "🔐 [Institutional Compliance] SMTP Email Setup Verification"
    msg["From"] = smtp_user
    msg["To"] = recipient_email

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; }}
    .box {{ max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0; padding: 28px; text-align: center; }}
    .badge {{ background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; padding: 6px 14px; border-radius: 9999px; font-size: 13px; font-weight: 700; display: inline-block; }}
    h2 {{ color: #1e3a8a; margin-top: 16px; }}
    p {{ color: #475569; font-size: 14px; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="box">
    <div class="badge">✓ REAL EMAIL DELIVERY CONNECTED</div>
    <h2>Automated Institutional Compliance System</h2>
    <p>Congratulations! Your email dispatch service is now active.</p>
    <p>From now on, whenever you sign in, create an account, or reset a password on the web portal, your 6-digit OTP will be delivered directly to this inbox.</p>
  </div>
</body>
</html>"""

    msg.set_content(f"Real email delivery configured successfully! Recipient: {recipient_email}")
    msg.add_alternative(html_content, subtype="html")

    if smtp_port == 465:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    print(f"[OK] Live test email sent successfully to: {recipient_email}")

def update_env(smtp_host, smtp_port, smtp_user, smtp_pass):
    if not ENV_PATH.exists():
        content = ""
    else:
        content = ENV_PATH.read_text(encoding="utf-8")

    settings = {
        "SMTP_HOST": smtp_host,
        "SMTP_PORT": str(smtp_port),
        "SMTP_USERNAME": smtp_user,
        "SMTP_PASSWORD": smtp_pass,
        "SMTP_FROM": smtp_user,
        "DEV_EXPOSE_OTP": "false"  # Real emails are working, no need to expose code on screen
    }

    lines = content.splitlines()
    updated_keys = set()
    new_lines = []

    for line in lines:
        matched = False
        for k, v in settings.items():
            if line.startswith(f"{k}="):
                new_lines.append(f"{k}={v}")
                updated_keys.add(k)
                matched = True
                break
        if not matched:
            new_lines.append(line)

    for k, v in settings.items():
        if k not in updated_keys:
            new_lines.append(f"{k}={v}")

    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"[OK] Updated configuration in: {ENV_PATH}")

def main():
    print("=" * 70)
    print("Institutional Document Compliance & Audit System - Email Setup")
    print("=" * 70)
    print("\nTo send real OTPs to your Gmail inbox, you need a Google App Password.")
    print("How to get a Google App Password in 1 minute:")
    print("  1. Open: https://myaccount.google.com/security")
    print("  2. Ensure '2-Step Verification' is turned ON.")
    print("  3. Open: https://myaccount.google.com/apppasswords")
    print("  4. Name it 'Institutional Audit' and copy the 16-character password.\n")

    default_user = "nikhithabadolla0509@gmail.com"
    email_input = input(f"Enter your Gmail address [{default_user}]: ").strip()
    email = email_input if email_input else default_user

    smtp_pass = input("Enter your 16-character Google App Password (without spaces): ").strip().replace(" ", "")

    if not smtp_pass:
        print("[!] No password provided. Exiting.")
        return

    recipient_input = input(f"Send test email to [{email}]: ").strip()
    recipient = recipient_input if recipient_input else email

    try:
        send_test_email("smtp.gmail.com", 587, email, smtp_pass, recipient)
        update_env("smtp.gmail.com", 587, email, smtp_pass)
        print("\n" + "=" * 70)
        print("🎉 SUCCESS! Real email delivery is now fully configured and active.")
        print("Check your inbox to see the verification test message.")
        print("=" * 70)
    except Exception as e:
        print(f"\n[!] Failed to connect to SMTP server: {e}")
        print("Please check that:")
        print("  1. 2-Step Verification is enabled on your Google account.")
        print("  2. You used a 16-character App Password (not your regular Gmail password).")

if __name__ == "__main__":
    main()
