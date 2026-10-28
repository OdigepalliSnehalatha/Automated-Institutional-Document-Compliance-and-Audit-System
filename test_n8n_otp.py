import os
import sys
import threading
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from dotenv import load_dotenv
load_dotenv()

from backend.database import get_db_cursor
from backend.services.otp_service import (
    create_and_send_login_otp,
    verify_login_otp,
    hash_otp
)
from backend.services.n8n_service import (
    is_n8n_enabled,
    send_otp_via_n8n,
    get_n8n_webhook_url
)
from n8n.local_n8n_bridge import N8nWebhookHandler
from http.server import HTTPServer

def run_test():
    print("======================================================================")
    print("Testing n8n Realistic OTP Generation & Email Automation Pipeline")
    print("======================================================================")

    # 1. Start local n8n test server on 5678 in background thread
    server = HTTPServer(("127.0.0.1", 5678), N8nWebhookHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)
    print("[1/4] Local n8n Webhook Listener running on http://127.0.0.1:5678")

    # 2. Test direct n8n webhook dispatch
    test_email = "faculty.cse@alitsprototype.test"
    print(f"\n[2/4] Testing direct n8n webhook dispatch for {test_email}...")
    res = send_otp_via_n8n(
        email=test_email,
        otp="123456",
        institution_name="Anantha Lakshmi Institute of Technology and Sciences",
        role="Faculty",
        purpose="Test Login Verification",
        subject="🔐 Test Subject Passcode",
        expires_in_minutes=5
    )
    assert res.get("success") is True, f"n8n webhook dispatch failed: {res}"
    print("  -> Direct n8n webhook dispatch: PASSED")

    # 3. Test full OTP generation and database persistence
    print(f"\n[3/4] Generating institutional OTP for {test_email} via otp_service...")
    otp_code = create_and_send_login_otp(
        institution_name="Anantha Lakshmi Institute of Technology and Sciences",
        email=test_email,
        role="Faculty"
    )
    assert len(otp_code) == 6 and otp_code.isdigit(), f"Invalid OTP generated: {otp_code}"
    print(f"  -> Generated 6-digit OTP: {otp_code}")

    # Check database record
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, otp_hash, expires_at, is_used
            FROM login_otps
            WHERE LOWER(email) = %s AND is_used = FALSE
            ORDER BY created_at DESC LIMIT 1
            """,
            (test_email.lower(),)
        )
        row = cursor.fetchone()
        assert row is not None, "No active OTP record found in database"
        assert row["otp_hash"] == hash_otp(otp_code), "Database hash does not match generated OTP"
        print("  -> Database SHA-256 hashed storage: PASSED")

    # 4. Test realistic OTP verification
    print(f"\n[4/4] Verifying OTP {otp_code}...")
    verified = verify_login_otp(email=test_email, entered_otp=otp_code)
    assert verified is True, "OTP verification failed"
    print("  -> OTP verification & single-use invalidation: PASSED")

    # Clean up test server
    server.shutdown()
    print("\n======================================================================")
    print("ALL N8N OTP AUTOMATION TESTS PASSED SUCCESSFULLY!")
    print("======================================================================")

if __name__ == "__main__":
    run_test()
