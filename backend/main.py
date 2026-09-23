from backend.database import get_connection
import os
import re
import json
import secrets
import hashlib
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

import bcrypt
import fitz
import psycopg2
from psycopg2.extras import RealDictCursor

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    File,
    Form,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware


# ============================================================
# CONFIGURATION
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:sneha%40429reddy@localhost:5432/mydatabase"
)

SESSION_SECRET = os.getenv(
    "SESSION_SECRET",
    "alits-local-session-key-2026-change-later-9f7K2mP4"
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5

ALLOWED_ROLES = {
    "Auditor",
    "HOD",
    "Faculty",
}


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Institutional Document Structure System",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SESSION AUTHENTICATION
# ============================================================

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="session",
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=False,
)


# ============================================================
# SESSION TEST
# ============================================================

@app.get("/test-session")
def test_session(request: Request):
    request.session["test"] = "hello"

    return {
        "message": "Session test created",
        "session": dict(request.session),
    }


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return psycopg2.connect(DATABASE_URL)


# ============================================================
# PASSWORD / OTP HELPERS
# ============================================================

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash.encode("utf-8"),
        )
    except Exception:
        return False


def hash_otp(otp: str) -> str:
    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def send_otp_email(
    email: str,
    institution_name: str,
    otp: str,
):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv(
        "SMTP_FROM",
        smtp_username or "",
    )

    if not smtp_host or not smtp_username or not smtp_password:
        raise RuntimeError(
            "SMTP configuration is missing."
        )

    message = EmailMessage()

    message["Subject"] = (
        "Your institutional system login OTP"
    )

    message["From"] = smtp_from
    message["To"] = email

    message.set_content(
        f"""
Your login OTP is: {otp}

Institution: {institution_name}

This OTP expires in {OTP_EXPIRY_MINUTES} minutes.

If you did not request this login, ignore this email.
"""
    )

    with smtplib.SMTP(
        smtp_host,
        smtp_port,
    ) as server:

        server.starttls()

        server.login(
            smtp_username,
            smtp_password,
        )

        server.send_message(message)


# ============================================================
# AUTHENTICATION
# ============================================================

class OTPRequest(BaseModel):
    institution_name: str
    role: str
    email: str
    password: str


class OTPVerifyRequest(BaseModel):
    institution_name: str
    role: str
    email: str
    otp: str


def get_current_user(request: Request):
    user = request.session.get("user")

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    return user


def require_roles(*roles):
    def checker(
        current_user: dict = Depends(
            get_current_user
        ),
    ):
        if current_user.get("role") not in roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission for this operation.",
            )

        return current_user

    return checker


def check_department_access(
    current_user: dict,
    department_id: int,
):
    role = current_user.get("role")
    user_department_id = current_user.get(
        "department_id"
    )

    if role in {"Auditor", "HOD", "Faculty"}:
        if user_department_id is None:
            raise HTTPException(
                status_code=403,
                detail="User is not assigned to a department.",
            )

        if int(user_department_id) != int(
            department_id
        ):
            raise HTTPException(
                status_code=403,
                detail="You cannot access another department.",
            )


@app.post("/auth/request-otp")
def request_otp(data: OTPRequest):
    if data.role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Invalid role.",
        )

    institution_name = (
        data.institution_name.strip()
    )

    email = data.email.strip().lower()

    connection = get_connection()

    try:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                SELECT
                    u.id,
                    u.email,
                    u.password_hash,
                    u.role,
                    u.department_id,
                    i.id AS institution_id,
                    i.name AS institution_name
                FROM users u
                JOIN institution i
                    ON i.id = u.institution_id
                WHERE LOWER(u.email) = %s
                  AND LOWER(i.name) = LOWER(%s)
                """,
                (
                    email,
                    institution_name,
                ),
            )

            user = cursor.fetchone()

            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid login details.",
                )

            if user["role"] not in ALLOWED_ROLES:
                raise HTTPException(
                    status_code=403,
                    detail="This user role is not enabled.",
                )

            if user["role"] != data.role:
                raise HTTPException(
                    status_code=401,
                    detail="Selected role does not match the registered role.",
                )

            if not verify_password(
                data.password,
                user["password_hash"],
            ):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid login details.",
                )

            otp = generate_otp()
            otp_hash = hash_otp(otp)

            expires_at = (
                datetime.now()
                + timedelta(
                    minutes=OTP_EXPIRY_MINUTES
                )
            )

            cursor.execute(
                """
                UPDATE login_otps
                SET is_used = TRUE
                WHERE LOWER(email) = LOWER(%s)
                  AND LOWER(role) = LOWER(%s)
                  AND is_used = FALSE
                """,
                (
                    email,
                    data.role,
                ),
            )

            cursor.execute(
                """
                INSERT INTO login_otps
                (
                    institution_name,
                    email,
                    role,
                    otp_hash,
                    expires_at,
                    attempts,
                    is_used
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    0,
                    FALSE
                )
                """,
                (
                    user["institution_name"],
                    email,
                    data.role,
                    otp_hash,
                    expires_at,
                ),
            )

            connection.commit()

            send_otp_email(
                email,
                user["institution_name"],
                otp,
            )

            return {
                "message": "OTP sent successfully."
            }

    finally:
        connection.close()



@app.post("/verify-otp")
def verify_otp(
    otp_data: VerifyOTPRequest,
    request: Request
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # ---------------------------------------------------------
        # 1. Find the latest unused OTP
        # ---------------------------------------------------------
        cursor.execute(
            """
            SELECT
                id,
                otp_hash,
                expires_at,
                attempts,
                is_used
            FROM login_otps
            WHERE LOWER(email) = LOWER(%s)
              AND role = %s
              AND LOWER(institution_name) = LOWER(%s)
              AND is_used = FALSE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                otp_data.email,
                otp_data.role,
                otp_data.institution_name,
            ),
        )

        otp_record = cursor.fetchone()

        if not otp_record:
            raise HTTPException(
                status_code=400,
                detail="No valid OTP found. Please request a new OTP.",
            )

        otp_id = otp_record[0]
        otp_hash = otp_record[1]
        expires_at = otp_record[2]
        attempts = otp_record[3]
        is_used = otp_record[4]

        # ---------------------------------------------------------
        # 2. Check whether OTP is already used
        # ---------------------------------------------------------
        if is_used:
            raise HTTPException(
                status_code=400,
                detail="This OTP has already been used.",
            )

        # ---------------------------------------------------------
        # 3. Check OTP expiration
        # ---------------------------------------------------------
        if datetime.now() > expires_at:
            raise HTTPException(
                status_code=400,
                detail="OTP has expired. Please request a new OTP.",
            )

        # ---------------------------------------------------------
        # 4. Check maximum attempts
        # ---------------------------------------------------------
        if attempts >= MAX_OTP_ATTEMPTS:
            raise HTTPException(
                status_code=400,
                detail="Maximum OTP attempts exceeded. Please request a new OTP.",
            )

        # ---------------------------------------------------------
        # 5. Verify OTP
        # ---------------------------------------------------------
        entered_otp_hash = hash_otp(otp_data.otp)

        if not secrets.compare_digest(
            entered_otp_hash,
            otp_hash,
        ):
            cursor.execute(
                """
                UPDATE login_otps
                SET attempts = attempts + 1
                WHERE id = %s
                """,
                (otp_id,),
            )

            conn.commit()

            raise HTTPException(
                status_code=400,
                detail="Invalid OTP.",
            )

        # ---------------------------------------------------------
        # 6. Get the authenticated user
        # ---------------------------------------------------------
        cursor.execute(
            """
            SELECT
                u.id,
                u.email,
                u.role,
                u.institution_id,
                u.department_id,
                d.name AS department_name,
                i.name AS institution_name
            FROM users u
            LEFT JOIN departments d
                ON u.department_id = d.id
            LEFT JOIN institution i
                ON u.institution_id = i.id
            WHERE LOWER(u.email) = LOWER(%s)
              AND u.role = %s
              AND u.institution_id = (
                  SELECT id
                  FROM institution
                  WHERE LOWER(name) = LOWER(%s)
                  LIMIT 1
              )
            LIMIT 1
            """,
            (
                otp_data.email,
                otp_data.role,
                otp_data.institution_name,
            ),
        )

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User authentication failed.",
            )

        # ---------------------------------------------------------
        # 7. Extract user information
        # ---------------------------------------------------------
        user_id = user[0]
        email = user[1]
        role = user[2]
        institution_id = user[3]
        department_id = user[4]
        department_name = user[5]
        institution_name = user[6]

        # ---------------------------------------------------------
        # 8. Mark OTP as used
        # ---------------------------------------------------------
        cursor.execute(
            """
            UPDATE login_otps
            SET is_used = TRUE
            WHERE id = %s
            """,
            (otp_id,),
        )

        conn.commit()

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        print("VERIFY OTP ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail="An error occurred while verifying the OTP.",
        )

    finally:
        cursor.close()
        conn.close()

    # -------------------------------------------------------------
    # 9. Create session
    # -------------------------------------------------------------
    request.session.clear()

    request.session["user"] = {
        "id": user_id,
        "email": email,
        "role": role,
        "institution_id": institution_id,
        "institution_name": institution_name,
        "department_id": department_id,
        "department_name": department_name,
    }

    print(
        "SESSION CREATED:",
        request.session["user"]
    )

    # -------------------------------------------------------------
    # 10. Return successful response
    # -------------------------------------------------------------
    return {
        "message": "OTP verified successfully.",
        "authenticated": True,
    }
@app.get("/auth/me")
def auth_me(request: Request):
    user = get_current_user(request)

    return {
        "authenticated": True,
        "user": user,
    }

@app.post("/auth/logout")
def logout(request: Request):
    request.session.clear()

    return {
        "message": "Logged out successfully."
    }


# ============================================================
# BASIC
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Institutional Document Structure System API"
    }


# ============================================================
# INSTITUTIONS
# ============================================================

@app.get("/institutions")
def get_institutions(
    current_user: dict = Depends(
        get_current_user
    ),
):
    connection = get_connection()

    try:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                SELECT id, name
                FROM institution
                ORDER BY name
                """
            )

            return cursor.fetchall()

    finally:
        connection.close()


# ============================================================
# DOCUMENT TYPES
# ============================================================

@app.get("/document-types")
def get_document_types(
    current_user: dict = Depends(
        get_current_user
    ),
):
    connection = get_connection()

    try:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    is_active
                FROM document_types
                WHERE is_active = TRUE
                  AND name IN
                  (
                      'Course Structure',
                      'Question Bank',
                      'Question Paper'
                  )
                ORDER BY id
                """
            )

            return cursor.fetchall()

    finally:
        connection.close()


# ============================================================
# FORMATS
# ============================================================

class FormatCreate(BaseModel):
    institution_id: int
    department_id: int
    document_type_id: int
    format_name: str
    instructions: str | None = None


class FormatRequirementCreate(BaseModel):
    format_id: int
    requirement_name: str
    requirement_type: str
    requirement_value: str | None = None
    is_required: bool = True
    display_order: int = 1


@app.post("/formats")
def create_format(
    data: FormatCreate,
    current_user: dict = Depends(
        require_roles("Auditor")
    ),
):
    check_department_access(
        current_user,
        data.department_id,
    )

    connection = get_connection()

    try:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                INSERT INTO document_formats
                (
                    institution_id,
                    department_id,
                    document_type_id,
                    format_name,
                    instructions,
                    created_by
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING *
                """,
                (
                    data.institution_id,
                    data.department_id,
                    data.document_type_id,
                    data.format_name.strip(),
                    data.instructions,
                    current_user["id"],
                ),
            )

            result = cursor.fetchone()

            connection.commit()

            return {
                "message": "Format created successfully.",
                "format": result,
            }

    finally:
        connection.close()


@app.post("/format-requirements")
def create_format_requirement(
    data: FormatRequirementCreate,
    current_user: dict = Depends(
        require_roles("Auditor")
    ),
):
    connection = get_connection()

    try:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                SELECT
                    df.department_id
                FROM document_formats df
                WHERE df.id = %s
                """,
                (data.format_id,),
            )

            format_record = cursor.fetchone()

            if not format_record:
                raise HTTPException(
                    status_code=404,
                    detail="Format not found.",
                )

            check_department_access(
                current_user,
                format_record[
                    "department_id"
                ],
            )

            cursor.execute(
                """
                INSERT INTO format_requirements
                (
                    format_id,
                    requirement_name,
                    requirement_type,
                    requirement_value,
                    is_required,
                    display_order
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING *
                """,
                (
                    data.format_id,
                    data.requirement_name.strip(),
                    data.requirement_type,
                    data.requirement_value,
                    data.is_required,
                    data.display_order,
                ),
            )

            result = cursor.fetchone()

            connection.commit()

            return result

    finally:
        connection.close()


# ============================================================
# GET FORMATS
# ============================================================

@app.get("/formats")
def get_formats(
    department_id: int | None = None,
    current_user: dict = Depends(
        get_current_user
    ),
):
    connection = get_connection()

    try:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            # Auditor, HOD and Faculty can only access
            # formats belonging to their department.
            if current_user["role"] in {
                "Auditor",
                "HOD",
                "Faculty",
            }:

                if department_id is None:
                    department_id = current_user[
                        "department_id"
                    ]

                check_department_access(
                    current_user,
                    department_id,
                )

            if department_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="Department is required.",
                )

            cursor.execute(
                """
                SELECT
                    df.id,
                    df.institution_id,
                    df.department_id,
                    df.document_type_id,
                    df.format_name,
                    df.instructions,
                    df.created_by,
                    df.created_at,
                    df.updated_at,
                    dt.name AS document_type_name
                FROM document_formats df
                JOIN document_types dt
                    ON dt.id = df.document_type_id
                WHERE df.department_id = %s
                ORDER BY df.created_at DESC
                """,
                (department_id,),
            )

            formats = cursor.fetchall()

            for item in formats:

                cursor.execute(
                    """
                    SELECT
                        id,
                        format_id,
                        requirement_name,
                        requirement_type,
                        requirement_value,
                        is_required,
                        display_order
                    FROM format_requirements
                    WHERE format_id = %s
                    ORDER BY display_order
                    """,
                    (item["id"],),
                )

                item["requirements"] = (
                    cursor.fetchall()
                )

            return formats

    finally:
        connection.close()


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pdf_pages(file_path: str):

    document = fitz.open(file_path)

    pages = []

    try:

        for page_number, page in enumerate(
            document,
            start=1,
        ):

            pages.append(
                {
                    "page": page_number,
                    "text": page.get_text("text"),
                }
            )

        return pages

    finally:

        document.close()


def extract_pdf_text(file_path: str):

    pages = extract_pdf_pages(
        file_path
    )

    return "\n".join(
        page["text"]
        for page in pages
    )


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalized(text: str):

    return re.sub(
        r"\s+",
        " ",
        text.lower().strip(),
    )


def contains_text(
    document_text: str,
    expected: str,
):

    if not expected:
        return False

    return (
        normalized(expected)
        in normalized(document_text)
    )


# ============================================================
# STRUCTURAL QUESTION COUNT
# ============================================================

def count_questions_in_section(
    text: str,
):

    patterns = [
        r"(?m)^\s*(?:q(?:uestion)?\s*)?\d+[\.\):\-]",
        r"(?m)^\s*\(\s*[a-z]\s*\)",
    ]

    matches = []

    for pattern in patterns:

        matches.extend(
            re.findall(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
        )

    return len(matches)


def find_section(
    text: str,
    section_name: str,
):

    pattern = (
        rf"\b{re.escape(section_name)}\b"
    )

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return ""

    return text[match.start():]


# ============================================================
# REQUIREMENT CHECKING
# ============================================================

def check_format_requirement(
    requirement,
    document_text,
):

    requirement_type = requirement[
        "requirement_type"
    ]

    requirement_value = (
        requirement["requirement_value"]
        or ""
    )

    requirement_name = normalized(
        requirement["requirement_name"]
    )

    # --------------------------------------------------------
    # REQUIRED ELEMENT
    # --------------------------------------------------------

    if requirement_type == "required":

        if requirement_name == "college header":

            first_page_text = document_text[
                :3000
            ]

            passed = bool(
                first_page_text.strip()
            )

            return (
                passed,
                "Found"
                if passed
                else "College header not found",
            )

        if requirement_name == "part a":

            passed = bool(
                re.search(
                    r"\bpart\s*a\b",
                    document_text,
                    re.IGNORECASE,
                )
            )

            return (
                passed,
                "Found"
                if passed
                else "Part A not found",
            )

        if requirement_name == "part b":

            passed = bool(
                re.search(
                    r"\bpart\s*b\b",
                    document_text,
                    re.IGNORECASE,
                )
            )

            return (
                passed,
                "Found"
                if passed
                else "Part B not found",
            )

        if requirement_name == "body":

            passed = len(
                document_text.strip()
            ) > 100

            return (
                passed,
                "Found"
                if passed
                else "Body not found",
            )

        if requirement_name == "footer":

            lines = [
                line.strip()
                for line in document_text.splitlines()
                if line.strip()
            ]

            passed = len(lines) > 0

            return (
                passed,
                "Found"
                if passed
                else "Footer not found",
            )

        passed = bool(
            document_text.strip()
        )

        return (
            passed,
            "Found"
            if passed
            else "Required element not found",
        )

    # --------------------------------------------------------
    # TEXT / SECTION
    # --------------------------------------------------------

    if requirement_type == "text":

        if requirement_name == "semester":

            passed = bool(
                re.search(
                    r"\bsemester\b",
                    document_text,
                    re.IGNORECASE,
                )
            )

            return (
                passed,
                "Found"
                if passed
                else "Semester not found",
            )

        if requirement_name == "b.tech":

            passed = bool(
                re.search(
                    r"\bb\.?\s*tech\b",
                    document_text,
                    re.IGNORECASE,
                )
            )

            return (
                passed,
                "Found"
                if passed
                else "B.Tech not found",
            )

        if requirement_name == "examination type":

            passed = contains_text(
                document_text,
                requirement_value,
            )

            return (
                passed,
                requirement_value
                if passed
                else "Examination type does not match",
            )

        keyword_map = {

            "subject name": [
                "subject name",
                "subject",
            ],

            "subject code": [
                "subject code",
                "course code",
            ],

            "branch": [
                "branch",
            ],

            "department": [
                "department",
            ],

            "time": [
                "time",
            ],

            "maximum marks": [
                "maximum marks",
                "max marks",
                "max. marks",
            ],
        }

        for field_name, variants in keyword_map.items():

            if field_name in requirement_name:

                passed = any(
                    normalized(
                        variant
                    )
                    in normalized(
                        document_text
                    )
                    for variant in variants
                )

                return (
                    passed,
                    "Found"
                    if passed
                    else f"{field_name.title()} not found",
                )

        if requirement_value:

            passed = contains_text(
                document_text,
                requirement_value,
            )

            return (
                passed,
                "Found"
                if passed
                else "Required text not found",
            )

        return (
            True,
            "Text section present",
        )

    # --------------------------------------------------------
    # QUESTION COUNT
    # --------------------------------------------------------

    if requirement_type == "question_count":

        try:

            expected_count = int(
                requirement_value
            )

        except (TypeError, ValueError):

            return (
                False,
                "Invalid question count",
            )

        if "part a" in requirement_name:

            section_text = find_section(
                document_text,
                "Part A",
            )

        elif "part b" in requirement_name:

            section_text = find_section(
                document_text,
                "Part B",
            )

        else:

            section_text = document_text

        actual_count = count_questions_in_section(
            section_text
        )

        passed = (
            actual_count == expected_count
        )

        return (
            passed,
            f"Expected {expected_count}, found {actual_count}",
        )

    # --------------------------------------------------------
    # MARKS
    # --------------------------------------------------------

    if requirement_type == "marks":

        try:

            expected_marks = float(
                re.search(
                    r"\d+(?:\.\d+)?",
                    requirement_value,
                ).group()
            )

        except (AttributeError, ValueError):

            return (
                False,
                "Invalid marks requirement",
            )

        if "part a" in requirement_name:

            section_text = find_section(
                document_text,
                "Part A",
            )

        elif "part b" in requirement_name:

            section_text = find_section(
                document_text,
                "Part B",
            )

        else:

            section_text = document_text

        marks_found = re.findall(
            r"\b(\d+(?:\.\d+)?)\s*marks?\b",
            section_text,
            flags=re.IGNORECASE,
        )

        if not marks_found:

            return (
                False,
                "Marks not found",
            )

        actual_marks = [
            float(value)
            for value in marks_found
        ]

        passed = (
            expected_marks in actual_marks
        )

        return (
            passed,
            f"Expected {expected_marks:g} marks"
            if not passed
            else f"{expected_marks:g} marks found",
        )

    # --------------------------------------------------------
    # ARRANGEMENT / STRUCTURE
    # --------------------------------------------------------

    if requirement_type in {
        "arrangement",
        "structure",
    }:

        if "part a" in requirement_name:

            passed = bool(
                re.search(
                    r"\bpart\s*a\b",
                    document_text,
                    re.IGNORECASE,
                )
            )

        elif "part b" in requirement_name:

            passed = bool(
                re.search(
                    r"\bpart\s*b\b",
                    document_text,
                    re.IGNORECASE,
                )
            )

        else:

            passed = True

        return (
            passed,
            "Structure present"
            if passed
            else "Expected structure not found",
        )

    # --------------------------------------------------------
    # UNKNOWN TYPE
    # --------------------------------------------------------

    return (
        True,
        "Checked",
    )


# ============================================================
# STRUCTURAL ANALYSIS
# ============================================================

def analyze_against_format(
    requirements,
    document_text,
):

    comparison = []

    all_required_passed = True

    for requirement in requirements:

        passed, uploaded_value = (
            check_format_requirement(
                requirement,
                document_text,
            )
        )

        if (
            requirement["is_required"]
            and not passed
        ):

            all_required_passed = False

        comparison.append(
            {
                "requirement_name":
                    requirement[
                        "requirement_name"
                    ],

                "requirement_type":
                    requirement[
                        "requirement_type"
                    ],

                "master_value":
                    requirement[
                        "requirement_value"
                    ],

                "uploaded_value":
                    uploaded_value,

                "required":
                    requirement[
                        "is_required"
                    ],

                "result":
                    "MATCH"
                    if passed
                    else "FAIL",
            }
        )

    final_result = (
        "ACCEPTED"
        if all_required_passed
        else "REJECTED"
    )

    return {
        "final_result": final_result,
        "comparison": comparison,
    }


# ------------------------------------------------------------
# SESSION MIDDLEWARE
# ------------------------------------------------------------

app.add_middleware(
    SessionMiddleware,
    secret_key="CHANGE_THIS_TO_A_RANDOM_SECRET"
)


# ------------------------------------------------------------
# REQUEST MODELS
# ------------------------------------------------------------

class LoginRequest(BaseModel):
    institution_name: str
    role: str
    email: str
    password: str


class VerifyOTPRequest(BaseModel):
    institution_name: str
    role: str
    email: str
    otp: str


# ------------------------------------------------------------
# OTP HELPERS
# ------------------------------------------------------------

def hash_otp(otp: str) -> str:
    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


# ------------------------------------------------------------
# GET CURRENT SESSION USER
# ------------------------------------------------------------

def get_current_user(request: Request):
    user = request.session.get("user")

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    return user


# ------------------------------------------------------------
# ROLE CHECK
# ------------------------------------------------------------

def require_roles(*allowed_roles):

    def checker(request: Request):
        user = get_current_user(request)

        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this resource."
            )

        return user

    return checker


# ------------------------------------------------------------
# SEND OTP
# ------------------------------------------------------------

def send_login_otp(email: str, otp: str):
    """
    Development-only OTP handler.

    The OTP is printed in the backend terminal for testing.
    It is not returned in the API response.
    """

    print("=" * 50)
    print(f"OTP generated for: {email}")
    print(f"OTP: {otp}")
    print("=" * 50)

# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------

@app.post("/login")
def login(login_data: LoginRequest):

    allowed_roles = {
        "Auditor",
        "HOD",
        "Faculty"
    }

    if login_data.role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Invalid role."
        )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                u.id,
                u.email,
                u.password_hash,
                u.role,
                u.department_id,
                d.name AS department_name,
                i.name AS institution_name
            FROM users u
            LEFT JOIN departments d
                ON u.department_id = d.id
            LEFT JOIN institution i
                ON u.institution_id = i.id
            WHERE LOWER(u.email) = LOWER(%s)
            """,
            (login_data.email,)
        )

        user = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid login credentials."
        )

    user_id = user[0]
    email = user[1]
    password_hash = user[2]
    database_role = user[3]
    department_id = user[4]
    department_name = user[5]
    database_institution = user[6]

    # Check institution
    if not database_institution:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to an institution."
        )

    if (
        database_institution.strip().lower()
        != login_data.institution_name.strip().lower()
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid login credentials."
        )

    # Check role
    if database_role != login_data.role:
        raise HTTPException(
            status_code=401,
            detail="Invalid login credentials."
        )

    # Check password
    if not verify_password(
        login_data.password,
        password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid login credentials."
        )

    # Generate OTP
    otp = generate_otp()
    otp_hash = hash_otp(otp)

    expires_at = datetime.utcnow() + timedelta(minutes=5)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Invalidate previous OTPs
        cursor.execute(
            """
            UPDATE login_otps
            SET is_used = TRUE
            WHERE LOWER(email) = LOWER(%s)
              AND role = %s
              AND LOWER(institution_name) = LOWER(%s)
              AND is_used = FALSE
            """,
            (
                email,
                database_role,
                database_institution
            )
        )

        # Store new OTP
        cursor.execute(
            """
            INSERT INTO login_otps (
                institution_name,
                email,
                role,
                otp_hash,
                expires_at,
                attempts,
                is_used
            )
            VALUES (%s, %s, %s, %s, %s, 0, FALSE)
            """,
            (
                database_institution,
                email,
                database_role,
                otp_hash,
                expires_at
            )
        )

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    # Development mode:
    # OTP will appear in the backend terminal.
    send_login_otp(
        email,
        otp
    )

    return {
        "message": "OTP sent to your registered email.",
        "requires_otp": True,
        "email": email
    }


@app.post("/verify-otp")
def verify_otp(
    otp_data: VerifyOTPRequest,
    request: Request
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # ----------------------------------------------------
        # Find latest unused OTP
        # ----------------------------------------------------
        cursor.execute(
            """
            SELECT
                id,
                otp_hash,
                expires_at,
                attempts,
                is_used
            FROM login_otps
            WHERE LOWER(email) = LOWER(%s)
              AND role = %s
              AND LOWER(institution_name) = LOWER(%s)
              AND is_used = FALSE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                otp_data.email,
                otp_data.role,
                otp_data.institution_name,
            ),
        )

        otp_record = cursor.fetchone()

        if not otp_record:
            raise HTTPException(
                status_code=401,
                detail="OTP not found or already used.",
            )

        otp_id = otp_record[0]
        stored_hash = otp_record[1]
        expires_at = otp_record[2]
        attempts = otp_record[3] or 0

        # ----------------------------------------------------
        # Check attempts
        # ----------------------------------------------------
        if attempts >= 5:
            cursor.execute(
                """
                UPDATE login_otps
                SET is_used = TRUE
                WHERE id = %s
                """,
                (otp_id,),
            )
            conn.commit()

            raise HTTPException(
                status_code=401,
                detail="Too many OTP attempts.",
            )

        # ----------------------------------------------------
        # Check expiry
        # ----------------------------------------------------
        if datetime.utcnow() > expires_at:
            cursor.execute(
                """
                UPDATE login_otps
                SET is_used = TRUE
                WHERE id = %s
                """,
                (otp_id,),
            )
            conn.commit()

            raise HTTPException(
                status_code=401,
                detail="OTP has expired.",
            )

        # ----------------------------------------------------
        # Verify OTP
        # ----------------------------------------------------
        submitted_hash = hash_otp(otp_data.otp)

        if not secrets.compare_digest(
            submitted_hash,
            stored_hash,
        ):
            cursor.execute(
                """
                UPDATE login_otps
                SET attempts = attempts + 1
                WHERE id = %s
                """,
                (otp_id,),
            )
            conn.commit()

            raise HTTPException(
                status_code=401,
                detail="Invalid OTP.",
            )

        # ----------------------------------------------------
        # Get user
        # ----------------------------------------------------
        cursor.execute(
            """
            SELECT
                u.id,
                u.email,
                u.role,
                u.department_id,
                u.institution_id,
                d.name AS department_name,
                i.name AS institution_name
            FROM users u
            LEFT JOIN departments d
                ON u.department_id = d.id
            LEFT JOIN institution i
                ON u.institution_id = i.id
            WHERE LOWER(u.email) = LOWER(%s)
            LIMIT 1
            """,
            (otp_data.email,),
        )

        user = cursor.fetchone()

        if not user:
            conn.rollback()

            raise HTTPException(
                status_code=401,
                detail="User account not found.",
            )

        user_id = user[0]
        email = user[1]
        role = user[2]
        department_id = user[3]
        institution_id = user[4]
        department_name = user[5]
        institution_name = user[6]

        # ----------------------------------------------------
        # Validate role
        # ----------------------------------------------------
        if role != otp_data.role:
            conn.rollback()

            raise HTTPException(
                status_code=401,
                detail="Invalid user role.",
            )

        # ----------------------------------------------------
        # Validate institution
        # ----------------------------------------------------
        if not institution_name:
            conn.rollback()

            raise HTTPException(
                status_code=401,
                detail="User is not linked to an institution.",
            )

        if (
            institution_name.strip().lower()
            != otp_data.institution_name.strip().lower()
        ):
            conn.rollback()

            raise HTTPException(
                status_code=401,
                detail="Invalid institution.",
            )

        # ----------------------------------------------------
        # Mark OTP as used
        # ----------------------------------------------------
        cursor.execute(
            """
            UPDATE login_otps
            SET is_used = TRUE
            WHERE id = %s
            """,
            (otp_id,),
        )

        conn.commit()

    except HTTPException:
        raise

    except Exception as e:
        conn.rollback()
        print("VERIFY OTP ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail="OTP verification failed.",
        )

    finally:
        cursor.close()
        conn.close()

    # --------------------------------------------------------
    # CREATE SESSION
    # --------------------------------------------------------
    request.session.clear()

    request.session["user"] = {
        "id": user_id,
        "email": email,
        "role": role,
        "institution_id": institution_id,
        "institution_name": institution_name,
        "department_id": department_id,
        "department_name": department_name,
    }

    # Useful for confirming the session was created.
    # The actual session data is stored in the signed cookie.
    print(
        "SESSION CREATED:",
        {
            "user_id": user_id,
            "email": email,
            "role": role,
            "institution_id": institution_id,
        },
    )

    return {
        "message": "OTP verified successfully.",
        "authenticated": True,
    }
# ------------------------------------------------------------
# CURRENT USER
# ------------------------------------------------------------



# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@app.post("/documents")
async def upload_document(
    institution_id: int = Form(...),
    department_id: int = Form(...),
    document_type_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(
        require_roles(
            "Auditor",
            "Faculty",
        )
    ),
):

    check_department_access(
        current_user,
        department_id,
    )

    if institution_id != int(
        current_user["institution_id"]
    ):

        raise HTTPException(
            status_code=403,
            detail="Invalid institution.",
        )

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )

    if not file.filename.lower().endswith(
        ".pdf"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    safe_filename = re.sub(
        r"[^A-Za-z0-9_.-]",
        "_",
        file.filename,
    )

    unique_filename = (
        f"{secrets.token_hex(8)}_"
        f"{safe_filename}"
    )

    file_path = (
        UPLOAD_DIR / unique_filename
    )

    with open(
        file_path,
        "wb",
    ) as output_file:

        while True:

            chunk = await file.read(
                1024 * 1024
            )

            if not chunk:
                break

            output_file.write(chunk)

    connection = get_connection()

    try:

        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                INSERT INTO documents
                (
                    institution_id,
                    department_id,
                    document_type_id,
                    file_name,
                    file_path,
                    uploaded_by
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING *
                """,
                (
                    institution_id,
                    department_id,
                    document_type_id,
                    file.filename,
                    str(file_path),
                    current_user["id"],
                ),
            )

            document = cursor.fetchone()

            connection.commit()

            return {
                "message":
                    "Document uploaded successfully.",

                "document":
                    document,
            }

    finally:

        connection.close()


# ============================================================
# ANALYZE DOCUMENT
# ============================================================

@app.post(
    "/documents/{document_id}/analyze"
)
def analyze_document(
    document_id: int,
    current_user: dict = Depends(
        require_roles(
            "Auditor",
            "Faculty",
        )
    ),
):
    connection = get_connection()

    try:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            # ------------------------------------------------
            # GET DOCUMENT
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    d.*,
                    dt.name AS document_type_name
                FROM documents d
                JOIN document_types dt
                    ON dt.id = d.document_type_id
                WHERE d.id = %s
                """,
                (document_id,),
            )

            document = cursor.fetchone()

            if not document:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found.",
                )

            # ------------------------------------------------
            # DEPARTMENT ACCESS
            # ------------------------------------------------

            check_department_access(
                current_user,
                document["department_id"],
            )

            # ------------------------------------------------
            # FILE CHECK
            # ------------------------------------------------

            file_path = Path(
                document["file_path"]
            )

            if not file_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail="PDF file not found.",
                )

            # ------------------------------------------------
            # GET LATEST AUDITOR FORMAT
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT *
                FROM document_formats
                WHERE institution_id = %s
                  AND department_id = %s
                  AND document_type_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (
                    document["institution_id"],
                    document["department_id"],
                    document["document_type_id"],
                ),
            )

            format_record = cursor.fetchone()

            if not format_record:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "No Auditor-defined format "
                        "exists for this document."
                    ),
                )

            # ------------------------------------------------
            # GET FORMAT REQUIREMENTS
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT *
                FROM format_requirements
                WHERE format_id = %s
                ORDER BY display_order
                """,
                (format_record["id"],),
            )

            requirements = cursor.fetchall()

            if not requirements:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "No structural requirements "
                        "are defined for this format."
                    ),
                )

            # ------------------------------------------------
            # EXTRACT PDF TEXT
            # ------------------------------------------------

            document_text = extract_pdf_text(
                str(file_path)
            )

            # ------------------------------------------------
            # STRUCTURAL COMPARISON
            # ------------------------------------------------

            result = analyze_against_format(
                requirements,
                document_text,
            )

            # ------------------------------------------------
            # SAVE ANALYSIS RESULT
            # ------------------------------------------------

            cursor.execute(
                """
                UPDATE documents
                SET
                    analysis_status = %s,
                    analysis_result = %s,
                    analyzed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    result["final_result"],
                    json.dumps(
                        result["comparison"]
                    ),
                    document_id,
                ),
            )

            connection.commit()

            # ------------------------------------------------
            # RETURN RESULT
            # ------------------------------------------------

            return {
                "document_id": document_id,
                "document_type": document[
                    "document_type_name"
                ],
                "final_result": result[
                    "final_result"
                ],
                "comparison": result[
                    "comparison"
                ],
            }

    finally:
        connection.close()


# ============================================================
# GET DOCUMENTS
# ============================================================

@app.get("/documents")
def get_documents(
    current_user: dict = Depends(
        get_current_user
    ),
):
    connection = get_connection()

    try:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            # ----------------------------------------------
            # AUDITOR / HOD
            # ----------------------------------------------

            if current_user["role"] in {
                "Auditor",
                "HOD",
            }:

                cursor.execute(
                    """
                    SELECT
                        d.id,
                        d.file_name,
                        d.department_id,
                        d.document_type_id,
                        d.analysis_status,
                        d.analyzed_at,
                        dt.name AS document_type_name
                    FROM documents d
                    JOIN document_types dt
                        ON dt.id = d.document_type_id
                    WHERE d.institution_id = %s
                      AND d.department_id = %s
                    ORDER BY d.id DESC
                    """,
                    (
                        current_user[
                            "institution_id"
                        ],
                        current_user[
                            "department_id"
                        ],
                    ),
                )

            # ----------------------------------------------
            # FACULTY
            # ----------------------------------------------

            else:

                cursor.execute(
                    """
                    SELECT
                        d.id,
                        d.file_name,
                        d.department_id,
                        d.document_type_id,
                        d.analysis_status,
                        d.analyzed_at,
                        dt.name AS document_type_name
                    FROM documents d
                    JOIN document_types dt
                        ON dt.id = d.document_type_id
                    WHERE d.institution_id = %s
                      AND d.department_id = %s
                      AND d.uploaded_by = %s
                    ORDER BY d.id DESC
                    """,
                    (
                        current_user[
                            "institution_id"
                        ],
                        current_user[
                            "department_id"
                        ],
                        current_user["id"],
                    ),
                )

            return cursor.fetchall()

    finally:
        connection.close()


# ============================================================
# ACCEPTED DOCUMENTS
# AUDITOR + HOD ONLY
# ============================================================

@app.get("/documents/accepted")
def get_accepted_documents(
    current_user: dict = Depends(
        require_roles(
            "Auditor",
            "HOD",
        )
    ),
):
    connection = get_connection()

    try:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                SELECT
                    d.id,
                    d.file_name,
                    d.department_id,
                    d.document_type_id,
                    d.analysis_status,
                    d.analyzed_at,
                    dt.name AS document_type_name
                FROM documents d
                JOIN document_types dt
                    ON dt.id = d.document_type_id
                WHERE d.institution_id = %s
                  AND d.department_id = %s
                  AND d.analysis_status = 'ACCEPTED'
                ORDER BY d.analyzed_at DESC
                """,
                (
                    current_user[
                        "institution_id"
                    ],
                    current_user[
                        "department_id"
                    ],
                ),
            )

            return cursor.fetchall()

    finally:
        connection.close()


# ============================================================
# VIEW ACCEPTED PDF
# AUDITOR + HOD ONLY
# ============================================================

@app.get(
    "/documents/{document_id}/pdf"
)
def view_accepted_pdf(
    document_id: int,
    current_user: dict = Depends(
        require_roles(
            "Auditor",
            "HOD",
        )
    ),
):
    connection = get_connection()

    try:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                SELECT *
                FROM documents
                WHERE id = %s
                """,
                (document_id,),
            )

            document = cursor.fetchone()

            if not document:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found.",
                )

            # ----------------------------------------------
            # DEPARTMENT SECURITY
            # ----------------------------------------------

            check_department_access(
                current_user,
                document[
                    "department_id"
                ],
            )

            # ----------------------------------------------
            # ACCEPTED ONLY
            # ----------------------------------------------

            if (
                document[
                    "analysis_status"
                ]
                != "ACCEPTED"
            ):
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Only accepted documents "
                        "can be viewed."
                    ),
                )

            file_path = Path(
                document["file_path"]
            )

            if not file_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail="PDF file not found.",
                )

            return FileResponse(
                path=str(file_path),
                media_type="application/pdf",
                headers={
                    "Content-Disposition":
                        (
                            'inline; filename="'
                            + document[
                                "file_name"
                            ]
                            + '"'
                        )
                },
            )

    finally:
        connection.close()


# ============================================================
# DOWNLOAD ACCEPTED PDF
# AUDITOR + HOD ONLY
# ============================================================

@app.get(
    "/documents/{document_id}/download"
)
def download_accepted_pdf(
    document_id: int,
    current_user: dict = Depends(
        require_roles(
            "Auditor",
            "HOD",
        )
    ),
):
    connection = get_connection()

    try:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                SELECT *
                FROM documents
                WHERE id = %s
                """,
                (document_id,),
            )

            document = cursor.fetchone()

            if not document:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found.",
                )

            check_department_access(
                current_user,
                document[
                    "department_id"
                ],
            )

            if (
                document[
                    "analysis_status"
                ]
                != "ACCEPTED"
            ):
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Only accepted documents "
                        "can be downloaded."
                    ),
                )

            file_path = Path(
                document["file_path"]
            )

            if not file_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail="PDF file not found.",
                )

            return FileResponse(
                path=str(file_path),
                media_type="application/pdf",
                filename=document[
                    "file_name"
                ],
            )

    finally:
        connection.close()


# ============================================================
# VIEW STRUCTURAL COMPARISON
# AUDITOR + HOD ONLY
# ============================================================

@app.get(
    "/documents/{document_id}/comparison"
)
def get_document_comparison(
    document_id: int,
    current_user: dict = Depends(
        require_roles(
            "Auditor",
            "HOD",
        )
    ),
):
    connection = get_connection()

    try:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    file_name,
                    department_id,
                    document_type_id,
                    analysis_status,
                    analysis_result,
                    analyzed_at
                FROM documents
                WHERE id = %s
                """,
                (document_id,),
            )

            document = cursor.fetchone()

            if not document:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found.",
                )

            check_department_access(
                current_user,
                document[
                    "department_id"
                ],
            )

            if not document[
                "analysis_result"
            ]:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "No structural comparison "
                        "is available."
                    ),
                )

            comparison = document[
                "analysis_result"
            ]

            if isinstance(
                comparison,
                str,
            ):
                comparison = json.loads(
                    comparison
                )

            return {
                "document_id":
                    document["id"],

                "file_name":
                    document["file_name"],

                "final_result":
                    document[
                        "analysis_status"
                    ],

                "comparison":
                    comparison,

                "analyzed_at":
                    document[
                        "analyzed_at"
                    ],
            }

    finally:
        connection.close()


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT 1"
            )

        return {
            "status": "ok",
            "database": "connected",
        }

    finally:

        connection.close()