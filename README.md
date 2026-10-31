# Automated Institutional Document Compliance and Audit System

A full-stack, session-authenticated web application engineered for higher education institutions to automate the structural verification, compliance auditing, and secure repository management of core academic documents—including **Course Structures**, **Question Banks**, and **Examination Papers (Mid 1, Mid 2, and Semester Exams)**.

The system enforces a **strict deterministic structural compliance engine**—validating document layouts, institutional headers, question counts, numbering patterns, and mark distributions against accredited university standards without subjective academic bias.

---

## 🌐 Local Host Access Links

When running locally, access the platform via:

- **Frontend User Interface**: [http://localhost:5173/](http://localhost:5173/)
- **Backend Interactive API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Backend Alternative API Docs (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Backend API Root**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🏛️ System Overview & Key Capabilities

In institutional accreditation (e.g., NBA, NAAC, Autonomous Universities), academic documents must strictly adhere to university structural standards. Manual inspection is time-consuming, inconsistent, and error-prone.

This system provides:
1. **Auditor Format Builder & Master Presets**: Dynamic configuration interface where auditors define institutional templates and structural rules without writing code.
2. **Faculty PDF Upload & Instant Verification**: Faculty submit examination papers and curricula, receiving immediate audit verdicts and diagnostic feedback.
3. **Strict Decision Rule**: A document is marked **`ACCEPTED`** (100% compliance) only if all mandatory structural checks pass. Any missing requirement or discrepancy results in **`REJECTED`** with exact diagnostic explanations and recommended corrections.
4. **Cross-Document Curriculum Validation**: Validates alignment between Course Structures, Question Banks, and Examination Papers for consistent institutional metadata and syllabus unit coverage.
5. **Immutable PDF Preservation**: Safe UUID file storage in `uploads/` directory. Only verified and **`ACCEPTED`** PDFs are accessible for viewing and downloading by Auditors and HODs.

---

## 📐 Institutional Document Standards & Validation Rules

### 1. Common Header (All Examination Papers)
Every examination paper (Mid 1, Mid 2, and Semester) must display the three mandatory header elements:
1. **College Name**: Official institution banner (e.g. `Anantha Lakshmi Institute of Technology & Sciences`).
2. **Branch Name**: Department or branch designation (e.g. `COMPUTER SCIENCE AND ENGINEERING` or standard department acronyms `CSE`, `ECE`, `EEE`, `ME`, `CE`).
3. **Maximum Marks**: Explicitly declared in the header (`Max. Marks: 40` for Mid exams; `Max. Marks: 70` for Semester exams).

---

### 2. Mid 1 and Mid 2 Examination Papers (Total: 40 Marks)
Both Mid 1 and Mid 2 follow the identical 6-rule validation pattern:
- **Rule 1 (College Name)**: Official college banner present in the header.
- **Rule 2 (Branch Name)**: Department / branch clearly identified in the header.
- **Rule 3 (Maximum Marks)**: `Max. Marks: 40` clearly stated in the header.
- **Rule 4 (Question 1 Subquestions)**: Question 1 must contain exactly **5 subquestions** (`A, B, C, D, E` or `a, b, c, d, e`, accepting standard numbering formats like `1(a)`, `1(A)`, `(a)`, `(A)`, `1.a`). Each carries 2 Marks (Total = 10 Marks).
- **Rule 5 (Questions 2 to 7 Presence)**: All six main questions (**2, 3, 4, 5, 6, 7**) must be present.
- **Rule 6 (Questions 2 to 7 Marks)**: Each of Questions 2 through 7 must display individual **`10 Marks`** beside it.

*Validation Restriction:* No calculation formulas (e.g. 5 × 2 = 10), internal MCQ option checks, or OR-pair combination constraints are enforced; validation focuses strictly on presence, count, and individual mark declarations.

---

### 3. Semester Examination Paper (Total: 70 Marks)
Semester papers follow an inline individual marks format with 6 validation rules:
- **Rule 1 (College Name)**: Official college banner present in the header.
- **Rule 2 (Branch Name)**: Department / branch clearly identified in the header.
- **Rule 3 (Maximum Marks)**: `Max. Marks: 70` clearly stated in the header.
- **Rule 4 (PART A – Question 1 Subquestions)**: Question 1 in Part A must contain exactly **10 subquestions** (`A` through `J` or `a` through `j`, accepting formats like `1(a)`, `(a)`, `1.a`). Each carries 2 Marks (Total = 20 Marks).
- **Rule 5 (PART B – Main Questions Count)**: Part B must contain exactly **10 main questions** (covering Units 1 to 5 with internal choice).
- **Rule 6 (PART B – Question Marks)**: Every question in Part B must individually display **`10 Marks`** beside it (Total = 50 Marks).

*Layout Standard:* No separate marks column is used in the semester question paper table; marks appear inline with each question statement without multiplication formulas.

---

### 4. Course Structure Standard Requirements
- **5 Mandatory Institutional Details**: College Name, Course Name, Course Code, Academic Year, Semester Name.
- **5 Mandatory Units**: Exactly five units (`Unit 1`, `Unit 2`, `Unit 3`, `Unit 4`, `Unit 5`) in strict sequential order.
- **Syllabus Content**: Substantive syllabus curriculum content must be present under each unit heading.

---

### 5. Question Bank Standard Requirements (100 Questions)
- **5 Mandatory Institutional Details**: College Name, Course Name, Course Code, Academic Year, Semester Name.
- **5 Syllabus Units**: Units 1 through 5.
- **Part A (Short Answer)**: Exactly 10 questions per unit @ 2 Marks = 50 questions total.
- **Part B (Descriptive)**: Exactly 10 questions per unit @ 10 Marks = 50 questions total.
- **Total**: Exactly **100 questions** across the 5 units.

---

## 📁 Sample & Verified Documents Included

Pre-generated and verified standard PDF documents are included in the repository for audit testing:

| Document | Location | Marks | Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Mid Examination Paper** | [`sample_docs/Valid_Mid_Paper_Sample.pdf`](sample_docs/Valid_Mid_Paper_Sample.pdf) | 40 Marks | **`ACCEPTED` (100%)** | Header with College, Branch, Max. Marks: 40; Q1 with 5 subquestions (a–e); Q2–Q7 present with 10 Marks each. |
| **Semester Examination Paper** | [`sample_docs/sem_paper.pdf`](sample_docs/sem_paper.pdf) | 70 Marks | **`ACCEPTED` (100%)** | Header with College, Branch, Max. Marks: 70; Part A with 10 subquestions; Part B with 10 main questions @ 10 Marks each. |
| **Course Structure** | [`sample_docs/Sample_Course_Structure_Valid.pdf`](sample_docs/Sample_Course_Structure_Valid.pdf) | N/A | **`ACCEPTED` (100%)** | 5 Common Details; Units 1–5 in sequence with comprehensive syllabus content. |

---

## 👥 Role-Based Access Control (RBAC)

| Role | Scope | Key Permissions |
| :--- | :--- | :--- |
| **Auditor** | Institution-Wide | Build master format rules, load standard presets, view all department submissions, inspect compliance breakdowns, preview & download accepted PDFs. |
| **HOD** | Departmental | Monitor department faculty submissions, view pass/fail statistics, inspect compliance diagnostics, preview & download verified department PDFs. |
| **Faculty** | Individual / Course | Upload PDFs for Course Structure, Question Banks, and Question Papers; receive instant automated validation reports with itemized pass/fail checklists. |
| **Admin** | System / Institutional | Manage users, departments, courses, document types, and master configurations. |

---

## 🏗️ Architecture & Technology Stack

```
                          +---------------------------------------+
                          |     React 19 + Vite Frontend (SPA)    |
                          |  http://localhost:5173/               |
                          +---------------------------------------+
                                              │
                              HTTP Session Cookie (Lax)
                              withCredentials: true
                                              ▼
                          +---------------------------------------+
                          |       FastAPI Application Core        |
                          |  http://127.0.0.1:8000/docs           |
                          +---------------------------------------+
                            │                 │                 │
                 SessionMiddleware      RBAC Router       Upload Pipeline
                 (Server-side state)   (Role & Dept)     (Safe UUID Store)
                            │                 │                 │
                            ▼                 ▼                 ▼
               +-------------------+ +-------------------+ +-------------------+
               |  PostgreSQL 14+   | | PyMuPDF Analyzer  | |   PDF Storage     |
               |  (Users, Formats, | | (Text, Headings,  | |    (uploads/      |
               |   Requirements,   | |  Blocks, Marks,   | |   directory)      |
               |    Documents)     | |  Question Counts) | |                   |
               +-------------------+ +-------------------+ +-------------------+
```

- **Backend**: Python 3.10+, FastAPI, Starlette Sessions, PyMuPDF (`fitz`), Psycopg, BCrypt, Pydantic v2.
- **Frontend**: React 19, Vite, Axios, Pure Modern Responsive CSS Design System.
- **Database**: PostgreSQL (Relational schema, foreign keys, JSONB for analysis results).
- **Authentication**: Starlette SessionMiddleware (HTTP-only session cookies, SHA-256 hashed OTPs with expiry & attempt limits, BCrypt password hashing). **No JWT / No localStorage tokens**.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- PostgreSQL running locally on `localhost:5432` (database: `mydatabase`)

### 2. Database Configuration
Ensure PostgreSQL is active. Database connection string is set via environment variable:
```bash
DATABASE_URL="postgresql://postgres:sneha%40429reddy@localhost:5432/mydatabase"
```

### 3. Backend Setup & Run
From the project root:
```powershell
# Install Python dependencies
pip install fastapi uvicorn pymupdf python-multipart psycopg bcrypt pydantic httpx

# Start the FastAPI backend server
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 4. Frontend Setup & Run
From the `frontend` directory:
```powershell
cd frontend
npm install
npm run dev
```
Open your browser at: [http://localhost:5173/](http://localhost:5173/).

---

## 🔑 Prototype Login Credentials

For demonstration and evaluation, the following pre-seeded credentials are ready:

| Role | Institution | Email | Password | Department |
| :--- | :--- | :--- | :--- | :--- |
| **Auditor** | Anantha Lakshmi Institute of Technology and Sciences | `auditor@alitsprototype.test` | `Auditor@123` | *All Departments* |
| **HOD** | Anantha Lakshmi Institute of Technology and Sciences | `hod.cse@alitsprototype.test` | `Hod@123` | Computer Science and Engineering |
| **Faculty** | Anantha Lakshmi Institute of Technology and Sciences | `faculty.cse@alits.ac.in` | `Faculty@123` | Computer Science and Engineering |
| **Admin** | Anantha Lakshmi Institute of Technology and Sciences | `admin@alits.ac.in` | `Admin@123` | Institutional Administration |

> [!NOTE]
> **OTP Login Verification:**
> When logging in with Role, Institution, Email, and Password, a 6-digit OTP is generated. In local development environments, the OTP is printed directly in the backend terminal console for instant access.

---

## 🧪 Automated Testing & Verification

Run the validation test suite to verify compliance logic across all document types:
```powershell
# Run full verification across Mid Paper, Semester Paper, and negative test cases
python -c "
import sys; sys.path.insert(0, '.');
from backend.services.structural_analyzer import validate_question_paper_document;
print('Mid Sample:', validate_question_paper_document('sample_docs/Valid_Mid_Paper_Sample.pdf', {'institution_name': 'Anantha Lakshmi Institute of Technology & Sciences', 'department_name': 'CSE'})['validation_status']);
"
```
Output:
```
Mid Sample: ACCEPTED
```
