import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db_cursor
from backend.services.auth_service import hash_password

prototype_accounts = [
    # Quick demo buttons in UI
    ("admin.alits@alitsprototype.test", "Admin@123", "Institutional Administrator", "Admin", None),
    ("auditor.alits@alitsprototype.test", "Auditor@123", "Institutional Compliance Auditor", "Auditor", None),
    ("hod.cse@alitsprototype.test", "HOD@123", "Dr. K. Ramesh (HOD CSE)", "HOD", 1),
    ("faculty.cse@alitsprototype.test", "Faculty@123", "Prof. S. Sharma (Faculty CSE)", "Faculty", 1),

    # Institutional standard domain accounts
    ("admin@alits.ac.in", "Admin@123", "Institutional Administrator", "Admin", None),
    ("auditor@alits.ac.in", "Auditor@123", "Institutional Compliance Auditor", "Auditor", None),
    ("hod.cse@alits.ac.in", "HOD@123", "Dr. K. Ramesh (HOD CSE)", "HOD", 1),
    ("faculty.cse@alits.ac.in", "Faculty@123", "Prof. S. Sharma (Faculty CSE)", "Faculty", 1),
]

def seed_accounts():
    print("Seeding institutional prototype accounts...")
    with get_db_cursor(commit=True) as cursor:
        # Ensure ALITS institution exists
        cursor.execute("SELECT id FROM institution WHERE id = 6")
        inst = cursor.fetchone()
        if not inst:
            cursor.execute("SELECT id FROM institution LIMIT 1")
            inst = cursor.fetchone()
        inst_id = inst["id"] if inst else 1

        for email, pwd, name, role, dept_id in prototype_accounts:
            pwd_hash = hash_password(pwd)
            cursor.execute("SELECT id FROM users WHERE LOWER(email) = %s", (email.lower(),))
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    """
                    UPDATE users
                    SET password_hash = %s, name = %s, role = %s, department_id = %s, institution_id = %s, is_active = TRUE
                    WHERE id = %s
                    """,
                    (pwd_hash, name, role, dept_id, inst_id, existing["id"])
                )
                print(f"Updated: {email} ({role})")
            else:
                cursor.execute(
                    """
                    INSERT INTO users (institution_id, department_id, name, email, password_hash, role, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                    """,
                    (inst_id, dept_id, name, email.lower(), pwd_hash, role)
                )
                print(f"Created: {email} ({role})")
    print("Prototype account seeding complete.")

if __name__ == "__main__":
    seed_accounts()
