import sys
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db_cursor
from backend.services.otp_service import hash_otp

INSTITUTION = "Anantha Lakshmi Institute of Technology and Sciences"

def test_admin_flow():
    client = TestClient(app)

    # 1. Admin Login request
    res = client.post("/login", json={
        "institution_name": INSTITUTION,
        "role": "Admin",
        "email": "admin@alitsprototype.test",
        "password": "Admin@123"
    })
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    body = res.json()
    assert body.get("requires_otp") is True
    # Ensure dev_otp is NOT in response (privacy requirement)
    assert "dev_otp" not in body, "dev_otp leaked in login response!"

    # 2. Inject known OTP in DB for automated verification
    known_otp = "852963"
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT id FROM login_otps
            WHERE email = 'admin@alitsprototype.test' AND is_used = FALSE
            ORDER BY id DESC LIMIT 1
            """
        )
        row = cursor.fetchone()
        assert row is not None, "Login OTP was not created in DB"
        cursor.execute(
            "UPDATE login_otps SET otp_hash = %s, attempts = 0 WHERE id = %s",
            (hash_otp(known_otp), row["id"])
        )

    # 3. Verify OTP
    verify_res = client.post("/verify-otp", json={
        "institution_name": INSTITUTION,
        "role": "Admin",
        "email": "admin@alitsprototype.test",
        "otp": known_otp
    })
    assert verify_res.status_code == 200, f"OTP verification failed: {verify_res.text}"
    user_data = verify_res.json().get("user", {})
    assert user_data.get("role") == "Admin", f"Expected Admin role, got {user_data.get('role')}"
    assert "institution_logo" in user_data, "institution_logo missing from auth user"

    # 4. Check /admin/dashboard
    dash_res = client.get("/admin/dashboard")
    assert dash_res.status_code == 200, f"Admin dashboard failed: {dash_res.text}"
    dash_data = dash_res.json()
    assert "metrics" in dash_data
    assert "departments" in dash_data
    assert "institution" in dash_data
    assert dash_data["institution"]["name"] == INSTITUTION
    print(f"  ✓ Admin Dashboard returned metrics: {dash_data['metrics']}")

    # 5. Check /admin/users (personnel directory)
    users_res = client.get("/admin/users")
    assert users_res.status_code == 200, f"Admin users failed: {users_res.text}"
    users_data = users_res.json()
    assert isinstance(users_data, list)
    assert len(users_data) > 0
    print(f"  ✓ Admin Directory found {len(users_data)} institution members")

    # 6. Check /ai/chat for Admin role
    ai_res = client.post("/ai/chat", json={
        "message": "Give me an overview of the departments and faculty in this institution"
    })
    assert ai_res.status_code == 200, f"AI chat failed: {ai_res.text}"
    ai_data = ai_res.json()
    assert "response" in ai_data
    assert len(ai_data["response"]) > 20
    print(f"  ✓ AI Assistant generated role-aware reply: {ai_data['response'][:60]}...")

    # 7. Check Logout
    logout_res = client.post("/logout")
    assert logout_res.status_code == 200

    # 8. Unauthenticated access blocked
    unauth_res = client.get("/admin/dashboard")
    assert unauth_res.status_code == 401
    print("  ✓ Unauthenticated access to Admin Dashboard strictly blocked (401)")

if __name__ == "__main__":
    test_admin_flow()
    print("\n=======================================================")
    print("ALL ADMIN & AI ASSISTANT TESTS PASSED! ✓")
    print("=======================================================")
