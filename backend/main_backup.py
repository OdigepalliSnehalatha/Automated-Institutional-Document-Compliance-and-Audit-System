from fastapi import FastAPI, Depends, HTTPException
from pydantic import Field
from typing import Literal
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from backend.database import get_connection
from passlib.context import  CryptContext
import jwt
from datetime import datetime, timedelta, timezone
class InstitutionCreate(BaseModel):
    name: str
    email: str 
class LoginRequest(BaseModel):
    email: str
    password: str
app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)
JWT_SECRET = "change-this-secret-key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

def require_role(required_role: str):
       def role_checker(current_user: dict = Depends(get_current_user)):
           if current_user.get("role") != required_role:
              raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )
           return current_user
       return role_checker
@app.get("/")
def home():
    return {"message": "Compliance Audit System API is running!"}


@app.get("/institution")
def get_institution(current_user: dict = Depends(get_current_user)):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, email, created_at
            FROM institution
            ORDER BY id ASC
        """)
        rows = cursor.fetchall()

    connection.close()

    institution = []

    for row in rows:
        institution.append({
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "created_at": row[3]
        })

    return {
        "institution": institution
        }
@app.get("/institutions/{institution_id}")
def get_institution(
    institution_id: int,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, name, email
        FROM institution
        WHERE id = %s
        """,
        (institution_id,)
    )

    institution = cursor.fetchone()

    cursor.close()
    connection.close()

    if institution is None:
        raise HTTPException(
            status_code=404,
            detail="Institution not found"
        )

    return {
        "id": institution[0],
        "name": institution[1],
        "email": institution[2]
    }
@app.post("/institution")
def create_institution(
    name: str,
    email: str,
    current_user: dict=
    Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO institution (name, email)
            VALUES (%s, %s)
            RETURNING id, name, email, created_at
            """,
            (name,email)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "created_at": row[3]
    }
@app.put("/institution/{institution_id}")
def update_institution(
    institution_id: int,
    name: str,
    email: str,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE institution
            SET name = %s,
                email = %s
            WHERE id = %s
            RETURNING id, name, email, created_at
            """,
            (name, email, institution_id)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Institution not found"
        )

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "created_at": row[3]
    }
@app.delete("/institution/{institution_id}")
def delete_institution(
    institution_id: int,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM institution
            WHERE id = %s
            RETURNING id, name, email
            """,
            (institution_id,)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Institution not found")

    return {
        "message": "Institution deleted successfully",
        "id": row[0],
        "name": row[1],
        "email": row[2]
    }
@app.get("/audits")
def get_audits(current_user: dict = Depends(get_current_user)):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, institution_id, audit_date, status, score, created_at
            FROM audits
            ORDER BY id ASC
        """)
        rows = cursor.fetchall()

    connection.close()

    audits = []

    for row in rows:
        audits.append({
            "id": row[0],
            "institution_id": row[1],
            "audit_date": row[2],
            "status": row[3],
            "score": row[4],
            "created_at": row[5]
        })

    return {"audits": audits}
@app.get("/audits/{audit_id}")
def get_audit(
    audit_id: int,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, institution_id, audit_date, status, score
        FROM audits
        WHERE id = %s
        """,
        (audit_id,)
    )

    audit = cursor.fetchone()

    cursor.close()
    connection.close()

    if audit is None:
        raise HTTPException(
            status_code=404,
            detail="Audit not found"
        )

    return {
        "id": audit[0],
        "institution_id": audit[1],
        "audit_date": audit[2],
        "status": audit[3],
        "score": audit[4]
    }
class AuditCreate(BaseModel):
    institution_id: int
    audit_date: str
    status:Literal["Completed"]
    score: float = Field(...,ge=0,le=100)
class AuditFindingCreate(BaseModel):
    audit_id: int
    requirement_id: int
    finding: str =Field(...,min_length=1)
    severity: Literal["Low", "Medium", "High"]
    recommendation: str=Field(...,min_length=1)
@app.post("/audits")
def create_audit(
    audit: AuditCreate,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT id FROM institution WHERE id = %s",
                (audit.institution_id,)
            )

            institution = cursor.fetchone()

            if institution is None:
                raise HTTPException(
                    status_code=404,
                    detail="Institution not found"
                )

            cursor.execute(
                """
                INSERT INTO audits
                    (institution_id, audit_date, status, score)
                VALUES
                    (%s, %s, %s, %s)
                RETURNING id, institution_id, audit_date, status, score, created_at
                """,
                (
                    audit.institution_id,
                    audit.audit_date,
                    audit.status,
                    audit.score
                )
            )

            row = cursor.fetchone()

        connection.commit()

        return {
            "id": row[0],
            "institution_id": row[1],
            "audit_date": row[2],
            "status": row[3],
            "score": row[4],
            "created_at": row[5]
        }

    finally:
        connection.close()
    

@app.put("/audits/{audit_id}")
def update_audit(
    audit_id: int,
    institution_id: int,
    audit_date: str,
    status: str,
    score: float,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE audits
            SET institution_id = %s,
                audit_date = %s,
                status = %s,
                score = %s
            WHERE id = %s
            RETURNING id, institution_id, audit_date, status, score, created_at
            """,
            (institution_id, audit_date, status, score, audit_id)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Audit not found"
        )

    return {
        "id": row[0],
        "institution_id": row[1],
        "audit_date": row[2],
        "status": row[3],
        "score": row[4],
        "created_at": row[5]
    }
@app.delete("/audits/{audit_id}")
def delete_audit(
    audit_id: int,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM audits
            WHERE id = %s
            RETURNING id
            """,
            (audit_id,)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Audit not found"
        )

    return {
        "message": "Audit deleted successfully",
        "id": row[0]
    }
@app.get("/compliance-requirements")
def get_compliance_requirements( 
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, title, description, category, created_at
            FROM compliance_requirements
            ORDER BY id ASC
        """)
        rows = cursor.fetchall()

    connection.close()

    requirements = []

    for row in rows:
        requirements.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "category": row[3],
            "created_at": row[4]
        })

    return {"compliance_requirements": requirements}
@app.get("/compliance-requirements/{requirement_id}")
def get_compliance_requirement(
    requirement_id: int,
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, description, category, created_at
            FROM compliance_requirements
            WHERE id = %s
            """,
            (requirement_id,)
        )
        row = cursor.fetchone()

    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Compliance requirement not found"
        )

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "category": row[3],
        "created_at": row[4]
    }
@app.post("/compliance-requirements")
def create_compliance_requirement(
    title: str,
    description: str,
    category: str,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO compliance_requirements
                (title, description, category)
            VALUES
                (%s, %s, %s)
            RETURNING id, title, description, category, created_at
            """,
            (title, description, category)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "category": row[3],
        "created_at": row[4]
    }
@app.put("/compliance-requirements/{requirement_id}")
def update_compliance_requirement(
    requirement_id: int,
    title: str,
    description: str,
    category: str,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE compliance_requirements
            SET title = %s,
                description = %s,
                category = %s
            WHERE id = %s
            RETURNING id, title, description, category, created_at
            """,
            (title, description, category, requirement_id)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Compliance requirement not found"
        )

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "category": row[3],
        "created_at": row[4]
    }
@app.delete("/compliance-requirements/{requirement_id}")
def delete_compliance_requirement(
    requirement_id: int,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM compliance_requirements
            WHERE id = %s
            RETURNING id
            """,
            (requirement_id,)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Compliance requirement not found"
        )

    return {
        "message": "Compliance requirement deleted successfully",
        "id": row[0]
    }
@app.get("/compliance-checks")
def get_compliance_checks(
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, audit_id, requirement_id, status, evidence, checked_at
            FROM compliance_checks
            ORDER BY id ASC
            """
        )
        rows = cursor.fetchall()

    connection.close()

    checks = []

    for row in rows:
        checks.append({
            "id": row[0],
            "audit_id": row[1],
            "requirement_id": row[2],
            "status": row[3],
            "evidence": row[4],
            "checked_at": row[5]
        })

    return {"compliance_checks": checks}
@app.get("/compliance-checks/{check_id}")
def get_compliance_check(
    check_id: int,
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, audit_id, requirement_id, status, evidence, checked_at
            FROM compliance_checks
            WHERE id = %s
            """,
            (check_id,)
        )
        row = cursor.fetchone()

    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Compliance check not found"
        )

    return {
        "id": row[0],
        "audit_id": row[1],
        "requirement_id": row[2],
        "status": row[3],
        "evidence": row[4],
        "checked_at": row[5]
    }
@app.post("/compliance-checks")
def create_compliance_check(
    audit_id: int,
    requirement_id: int,
    status: str,
    evidence: str,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO compliance_checks
                (audit_id, requirement_id, status, evidence)
            VALUES
                (%s, %s, %s, %s)
            RETURNING
                id, audit_id, requirement_id, status, evidence, checked_at
            """,
            (audit_id, requirement_id, status, evidence)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    return {
        "id": row[0],
        "audit_id": row[1],
        "requirement_id": row[2],
        "status": row[3],
        "evidence": row[4],
        "checked_at": row[5]
    }
@app.put("/compliance-checks/{check_id}")
def update_compliance_check(
    check_id: int,
    audit_id: int,
    requirement_id: int,
    status: str,
    evidence: str,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE compliance_checks
            SET audit_id = %s,
                requirement_id = %s,
                status = %s,
                evidence = %s
            WHERE id = %s
            RETURNING
                id, audit_id, requirement_id, status, evidence, checked_at
            """,
            (audit_id, requirement_id, status, evidence, check_id)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Compliance check not found"
        )

    return {
        "id": row[0],
        "audit_id": row[1],
        "requirement_id": row[2],
        "status": row[3],
        "evidence": row[4],
        "checked_at": row[5]
    }
@app.delete("/compliance-checks/{check_id}")
def delete_compliance_check(
    check_id: int,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM compliance_checks
            WHERE id = %s
            RETURNING id
            """,
            (check_id,)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Compliance check not found"
        )

    return {
        "message": "Compliance check deleted successfully",
        "id": row[0]
    }
@app.get("/documents")
def get_documents(
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, institution_id, file_name, file_path, uploaded_at
            FROM documents
            ORDER BY id ASC
            """
        )
        rows = cursor.fetchall()

    connection.close()

    documents = []

    for row in rows:
        documents.append({
            "id": row[0],
            "institution_id": row[1],
            "file_name": row[2],
            "file_path": row[3],
            "uploaded_at": row[4]
        })

    return {"documents": documents}
@app.get("/documents/{document_id}")
def get_document(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, institution_id, file_name, file_path, uploaded_at
            FROM documents
            WHERE id = %s
            """,
            (document_id,)
        )
        row = cursor.fetchone()

    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "id": row[0],
        "institution_id": row[1],
        "file_name": row[2],
        "file_path": row[3],
        "uploaded_at": row[4]
    }
@app.post("/documents")
def create_document(
    institution_id: int,
    file_name: str,
    file_path: str,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO documents
                (institution_id, file_name, file_path)
            VALUES
                (%s, %s, %s)
            RETURNING
                id, institution_id, file_name, file_path, uploaded_at
            """,
            (institution_id, file_name, file_path)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    return {
        "id": row[0],
        "institution_id": row[1],
        "file_name": row[2],
        "file_path": row[3],
        "uploaded_at": row[4]
    }
@app.put("/documents/{document_id}")
def update_document(
    document_id: int,
    institution_id: int,
    file_name: str,
    file_path: str,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE documents
            SET institution_id = %s,
                file_name = %s,
                file_path = %s
            WHERE id = %s
            RETURNING
                id, institution_id, file_name, file_path, uploaded_at
            """,
            (institution_id, file_name, file_path, document_id)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "id": row[0],
        "institution_id": row[1],
        "file_name": row[2],
        "file_path": row[3],
        "uploaded_at": row[4]
    }
@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM documents
            WHERE id = %s
            RETURNING id
            """,
            (document_id,)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "message": "Document deleted successfully",
        "id": row[0]
    }
@app.get("/audit-findings")
def get_audit_findings(current_user: dict = Depends(get_current_user)):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                id,
                audit_id,
                requirement_id,
                finding,
                severity,
                recommendation
            FROM audit_findings
            ORDER BY id ASC
        """)
        rows = cursor.fetchall()

    connection.close()

    findings = []

    for row in rows:
        findings.append({
            "id": row[0],
            "audit_id": row[1],
            "requirement_id": row[2],
            "finding": row[3],
            "severity": row[4],
            "recommendation": row[5]
        })

    return {"audit_findings": findings}
@app.get("/audit-findings/{finding_id}")
def get_audit_finding(
    finding_id: int,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, audit_id, requirement_id, finding, severity, recommendation
        FROM audit_findings
        WHERE id = %s
        """,
        (finding_id,)
    )

    finding = cursor.fetchone()

    cursor.close()
    connection.close()

    if finding is None:
        raise HTTPException(
            status_code=404,
            detail="Audit finding not found"
        )

    return {
        "id": finding[0],
        "audit_id": finding[1],
        "requirement_id": finding[2],
        "finding": finding[3],
        "severity": finding[4],
        "recommendation": finding[5]
    }
@app.post("/audit-findings")
def create_audit_finding(
    audit_finding: AuditFindingCreate,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # Check that the audit exists
            cursor.execute(
                "SELECT id FROM audits WHERE id = %s",
                (audit_finding.audit_id,)
            )

            audit = cursor.fetchone()

            if audit is None:
                raise HTTPException(
                    status_code=404,
                    detail="Audit not found"
                )

            # Check that the compliance requirement exists
            cursor.execute(
                "SELECT id FROM compliance_requirements WHERE id = %s",
                (audit_finding.requirement_id,)
            )

            requirement = cursor.fetchone()

            if requirement is None:
                raise HTTPException(
                    status_code=404,
                    detail="Compliance requirement not found"
                )

            cursor.execute(
                """
                INSERT INTO audit_findings
                    (audit_id, requirement_id, finding, severity, recommendation)
                VALUES
                    (%s, %s, %s, %s, %s)
                RETURNING id, audit_id, requirement_id, finding, severity, recommendation
                """,
                (
                    audit_finding.audit_id,
                    audit_finding.requirement_id,
                    audit_finding.finding,
                    audit_finding.severity,
                    audit_finding.recommendation
                )
            )

            row = cursor.fetchone()

        connection.commit()

        return {
            "id": row[0],
            "audit_id": row[1],
            "requirement_id": row[2],
            "finding": row[3],
            "severity": row[4],
            "recommendation": row[5]
        }

    finally:
        connection.close()
        
    
@app.put("/audit-findings/{finding_id}")
def update_audit_finding(
    finding_id: int,
    audit_id: int,
    requirement_id: int,
    finding: str,
    severity: str,
    recommendation: str,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE audit_findings
            SET audit_id = %s,
                requirement_id = %s,
                finding = %s,
                severity = %s,
                recommendation = %s
            WHERE id = %s
            RETURNING
                id, audit_id, requirement_id, finding, severity, recommendation
            """,
            (
                audit_id,
                requirement_id,
                finding,
                severity,
                recommendation,
                finding_id
            )
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Audit finding not found"
        )

    return {
        "id": row[0],
        "audit_id": row[1],
        "requirement_id": row[2],
        "finding": row[3],
        "severity": row[4],
        "recommendation": row[5]
    }
        
@app.delete("/audit-findings/{finding_id}")
def delete_audit_finding(
    finding_id: int,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM audit_findings
            WHERE id = %s
            RETURNING id
            """,
            (finding_id,)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Audit finding not found"
        )

    return {
        "message": "Audit finding deleted successfully",
        "id": row[0]
    }
@app.get("/audit-reports/{report_id}")
def get_audit_report(
    report_id: int,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM audit_reports WHERE id = %s",
        (report_id,)
    )

    report = cursor.fetchone()

    cursor.close()
    connection.close()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Audit report not found"
        )

    return report
@app.post("/audit-reports")
def create_audit_report(
    audit_id: int,
    report_name: str,
    report_path: str,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # Check that the audit exists
            cursor.execute(
                "SELECT id FROM audits WHERE id = %s",
                (audit_id,)
            )

            audit = cursor.fetchone()

            if audit is None:
                raise HTTPException(
                    status_code=404,
                    detail="Audit not found"
                )

            cursor.execute(
                """
                INSERT INTO audit_reports
                    (audit_id, report_name, report_path)
                VALUES
                    (%s, %s, %s)
                RETURNING id, audit_id, report_name, report_path, generated_at
                """,
                (
                    audit_id,
                    report_name,
                    report_path
                )
            )

            row = cursor.fetchone()

        connection.commit()

        return {
            "id": row[0],
            "audit_id": row[1],
            "report_name": row[2],
            "report_path": row[3],
            "generated_at": row[4]
        }

    finally:
        connection.close()
   
@app.get("/audit-reports")
def get_audit_reports(
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM audit_reports"
    )

    reports = cursor.fetchall()

    cursor.close()
    connection.close()

    return reports

@app.put("/audit-reports/{report_id}")
def update_audit_report(
    report_id: int,
    audit_id: int,
    report_name: str,
    report_path: str,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE audit_reports
            SET audit_id = %s,
                report_name = %s,
                report_path = %s
            WHERE id = %s
            RETURNING
                id, audit_id, report_name, report_path, generated_at
            """,
            (audit_id, report_name, report_path, report_id)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Audit report not found"
        )

    return {
        "id": row[0],
        "audit_id": row[1],
        "report_name": row[2],
        "report_path": row[3],
        "generated_at": row[4]
    }
@app.delete("/audit-reports/{report_id}")
def delete_audit_report(
    report_id: int,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM audit_reports
            WHERE id = %s
            RETURNING id
            """,
            (report_id,)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Audit report not found"
        )

    return {
        "message": "Audit report deleted successfully",
        "id": row[0]
    }
@app.get("/users")
def get_users(current_user: dict = Depends(get_current_user)):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                id,
                name,
                email,
                role,
                created_at
            FROM users
            ORDER BY id ASC
        """)
        rows = cursor.fetchall()

    connection.close()

    users = []

    for row in rows:
        users.append({
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "role": row[3],
            "created_at": row[4]
        })

    return {"users": users}
@app.get("/users/{user_id}")
def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, name, email, role
        FROM users
        WHERE id = %s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "id": user[0],
        "name": user[1],
        "email": user[2],
        "role": user[3]
    }
@app.post("/users")
def create_user(
    name: str,
    email: str,
    role: str,
    password: str,
    current_user: dict = Depends(require_role("Auditor"))
):
    if len(password.encode("utf-8")) > 72:
        return {"message": "Password must be 72 bytes or fewer"}

    connection = get_connection()

    password_hash = pwd_context.hash(password)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users
                (name, email, role, password_hash)
            VALUES
                (%s, %s, %s, %s)
            RETURNING
                id, name, email, role, created_at
            """,
            (name, email, role, password_hash)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "role": row[3],
        "created_at": row[4]
    }


@app.put("/users/{user_id}")
def update_user(
    user_id: int,
    name: str,
    email: str,
    role: str,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE users
            SET name = %s,
                email = %s,
                role = %s
            WHERE id = %s
            RETURNING
                id, name, email, role, created_at
            """,
            (name, email, role, user_id)
        )

        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "role": row[3],
        "created_at": row[4]
    }
@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: dict = Depends(require_role("Auditor"))
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM users
            WHERE id = %s
            RETURNING id
            """,
            (user_id,)
        )
        row = cursor.fetchone()

    connection.commit()
    connection.close()

    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "message": "User deleted successfully",
        "id": row[0]
    }
@app.post("/login")
def login_user(login: LoginRequest):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                role,
                password_hash
            FROM users
            WHERE email = %s
            """,
            (login.email,)
        )
        row = cursor.fetchone()

    connection.close()

    if row is None:
        return {"message": "Invalid email or password"}

    if not row[4]:
        return {"message": "Password not configured for this user"}

    if not verify_password(login.password, row[4]):
        return {"message": "Invalid email or password"}

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_EXPIRE_MINUTES
    )

    token = jwt.encode(
        {
            "sub": str(row[0]),
            "email": row[2],
            "role": row[3],
            "exp": expires_at
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "role": row[3]
    }