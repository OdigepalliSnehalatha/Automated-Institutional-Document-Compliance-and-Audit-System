#!/usr/bin/env python3
"""
Institutional Document Compliance and Audit System
One-Time Secure Admin Setup Utility

Usage:
    python setup_admin.py
    or
    python setup_admin.py --name "Dr. K. S. Sharma" --email "principal@alits.ac.in" --institution "Anantha Lakshmi Institute of Technology and Sciences"
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from dotenv import load_dotenv
load_dotenv()

from backend.database import get_db_cursor

def setup_first_admin(admin_name: str, admin_email: str, institution_name: str, clean_prototypes: bool = False):
    admin_name = admin_name.strip()
    admin_email = admin_email.strip().lower()
    institution_name = institution_name.strip()

    if not admin_name:
        raise ValueError("Admin name cannot be empty.")
    if not admin_email or "@" not in admin_email:
        raise ValueError("A valid official email is required.")
    if not institution_name:
        raise ValueError("Institution name cannot be empty.")

    with get_db_cursor(commit=True) as cursor:
        # 1. Ensure institution exists
        cursor.execute("SELECT id, name FROM institution WHERE LOWER(name) = LOWER(%s)", (institution_name,))
        inst = cursor.fetchone()
        if not inst:
            cursor.execute(
                "INSERT INTO institution (name, email) VALUES (%s, %s) RETURNING id, name",
                (institution_name, admin_email)
            )
            inst = cursor.fetchone()
            print(f"[+] Created institution: '{inst['name']}' (ID: {inst['id']})")
        else:
            print(f"[*] Found existing institution: '{inst['name']}' (ID: {inst['id']})")

        inst_id = inst["id"]

        # 2. Check if user already exists
        cursor.execute(
            "SELECT id, name, email, role, is_active FROM users WHERE LOWER(email) = %s AND institution_id = %s",
            (admin_email, inst_id)
        )
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.execute(
                "UPDATE users SET name = %s, role = 'Admin', is_active = TRUE WHERE id = %s RETURNING id, name, email, role, is_active",
                (admin_name, existing_user["id"])
            )
            user = cursor.fetchone()
            print(f"[OK] Existing user updated and designated as active Administrator:")
        else:
            cursor.execute(
                """
                INSERT INTO users (institution_id, name, email, role, is_active)
                VALUES (%s, %s, %s, 'Admin', TRUE)
                RETURNING id, name, email, role, is_active
                """,
                (inst_id, admin_name, admin_email)
            )
            user = cursor.fetchone()
            print(f"[OK] Successfully initialized Primary Administrator:")

        print(f"    - ID: {user['id']}")
        print(f"    - Name: {user['name']}")
        print(f"    - Official Email: {user['email']}")
        print(f"    - Role: {user['role']}")
        print(f"    - Active Status: {'Active' if user['is_active'] else 'Inactive'}")

        # 3. Optional prototype account cleanup
        if clean_prototypes:
            cursor.execute("UPDATE document_formats SET created_by = %s WHERE created_by IN (SELECT id FROM users WHERE email LIKE '%%@alitsprototype.test')", (user["id"],))
            cursor.execute("UPDATE documents SET uploaded_by = %s WHERE uploaded_by IN (SELECT id FROM users WHERE email LIKE '%%@alitsprototype.test')", (user["id"],))
            cursor.execute("DELETE FROM login_otps WHERE email LIKE '%%@alitsprototype.test'")
            cursor.execute("DELETE FROM users WHERE email LIKE '%%@alitsprototype.test'")
            print(f"[OK] Reassigned prototype records to Admin and permanently removed legacy prototype accounts (*@alitsprototype.test).")

    print("\n[+] Admin setup completed successfully!")
    print(f"[*] To log in, open the portal, select 'Admin', and enter {admin_email}.")
    print("[*] An OTP will be securely sent to this official email via the configured SMTP service.\n")

def main():
    parser = argparse.ArgumentParser(description="One-Time Administrator Setup Utility")
    parser.add_argument("--name", help="Full name of the institution Administrator")
    parser.add_argument("--email", help="Official email address for login verification")
    parser.add_argument("--institution", help="Name of the Institution")
    parser.add_argument("--clean-demo", action="store_true", help="Remove legacy prototype accounts")
    args = parser.parse_args()

    print("=================================================================")
    print(" Institutional Document Compliance & Audit System: Admin Setup ")
    print("=================================================================\n")

    # Get default institution from DB if available
    default_inst = "Anantha Lakshmi Institute of Technology and Sciences"
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT name FROM institution ORDER BY id LIMIT 1")
            row = cursor.fetchone()
            if row:
                default_inst = row["name"]
    except Exception:
        pass

    inst_name = args.institution
    if not inst_name:
        inst_input = input(f"Enter Institution Name [{default_inst}]: ").strip()
        inst_name = inst_input if inst_input else default_inst

    name = args.name
    if not name:
        name = input("Enter Administrator Full Name (e.g., Dr. K. S. Sharma): ").strip()
        while not name:
            name = input("Name cannot be empty. Please enter Administrator Full Name: ").strip()

    email = args.email
    if not email:
        email = input("Enter Administrator Official Email (for OTP login): ").strip().lower()
        while not email or "@" not in email:
            email = input("Please enter a valid email address: ").strip().lower()

    clean_demo = args.clean_demo
    if not clean_demo and not (args.name and args.email):
        clean_input = input("Purge prototype demo accounts (*@alitsprototype.test)? [y/N]: ").strip().lower()
        clean_demo = clean_input == "y"

    setup_first_admin(name, email, inst_name, clean_prototypes=clean_demo)

if __name__ == "__main__":
    main()
