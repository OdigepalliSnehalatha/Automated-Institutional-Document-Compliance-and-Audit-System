import bcrypt
from database import get_connection

INSTITUTION_ID = 6
CSE_DEPARTMENT_ID = 1

users = [
    (
        "Prototype Auditor",
        "auditor@alitsprototype.test",
        "Auditor@123",
        "Auditor",
        None,
    ),
    (
        "Prototype HOD",
        "hod.cse@alitsprototype.test",
        "Hod@123",
        "HOD",
        CSE_DEPARTMENT_ID,
    ),
    (
        "Prototype Faculty",
        "faculty.cse@alitsprototype.test",
        "Faculty@123",
        "Faculty",
        CSE_DEPARTMENT_ID,
    ),
]

conn = get_connection()
cur = conn.cursor()

try:
    for name, email, password, role, department_id in users:

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cur.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                role,
                created_at,
                password_hash,
                department_id,
                institution_id
            )
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s)
            """,
            (
                name,
                email,
                role,
                password_hash,
                department_id,
                INSTITUTION_ID,
            ),
        )

        print(f"Created: {role} - {email}")

    conn.commit()
    print("All prototype users created successfully.")

except Exception as e:
    conn.rollback()
    print("Setup failed:", e)

finally:
    cur.close()
    conn.close()