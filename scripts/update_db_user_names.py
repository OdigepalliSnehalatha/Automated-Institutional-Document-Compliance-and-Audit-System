import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import get_db_cursor

with get_db_cursor(commit=True) as cursor:
    cursor.execute("UPDATE users SET name = 'Admin' WHERE role = 'Admin'")
    cursor.execute("UPDATE users SET name = 'HOD' WHERE role = 'HOD'")
    cursor.execute("UPDATE users SET name = 'Auditor' WHERE role = 'Auditor'")
    cursor.execute("UPDATE users SET name = 'Faculty' WHERE email IN ('faculty.cse@alits.ac.in', 'faculty.cse@alitsprototype.test')")
    cursor.execute("SELECT id, email, role, name FROM users WHERE role IN ('Admin', 'HOD', 'Auditor', 'Faculty') ORDER BY role, id")
    print("Updated users in DB:")
    for r in cursor.fetchall():
        print(f"{r['email']} | {r['role']} | Name: {r['name']}")
