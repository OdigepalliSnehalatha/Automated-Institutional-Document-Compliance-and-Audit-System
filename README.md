# Automated Institutional Document Compliance and Audit System

A full-stack, session-authenticated web application designed for higher education institutions to automate the structural verification, compliance validation, and secure management of academic documents (such as **Course Structures**, **Question Banks**, and **Question Papers**).

The system enforces a **strict structural compliance engine**—evaluating document layout, sections, question counts, marks distributions, and institutional headers—without judging academic meaning or subject correctness.

---

## 🏛️ Project Overview

In institutional accreditation and academic audits, standard document formats (e.g., examination papers, syllabi, question banks) must strictly adhere to regulatory and university structural guidelines. Manual verification of every page, section heading, question count, and marks pattern is tedious and error-prone.

This system provides:
1. **Auditor Structural Format Builder**: A non-technical, dynamic requirement builder where the Auditor defines master structural specifications and standard rules.
2. **Faculty PDF Upload & Instant Verification**: Faculty upload PDFs which are immediately analyzed against the Auditor's active format.
3. **Strict Decision Rule**: A document is strictly **`ACCEPTED`** if and only if **100%** of mandatory structural rules pass. Even a single violation results in **`REJECTED`** with exact requirement-by-requirement diagnostics.
4. **Controlled Access & Preservation**: Original uploaded PDFs are preserved immutably with safe UUID identifiers. Only strictly **`ACCEPTED`** PDFs can be viewed and downloaded by the **Auditor** and department **HOD**.

---

## 👥 User Roles & Responsibilities

| Role | Responsibilities | Permissions |
| :--- | :--- | :--- |
| **Auditor** | Defines institutional document structures, creates/edits master formats, audits submissions across all departments. | Create/Edit/Delete Formats, View All Submissions, View Structural Comparisons, View & Download Accepted PDFs. |
| **HOD** | Monitors department document submissions and compliance status. | View Department Submissions, View Structural Comparisons, View & Download Accepted Department PDFs. |
| **Faculty** | Submits academic PDFs (Course Structures, Question Banks, Question Papers) for structural validation. | Upload PDFs, Trigger Structural Analysis, View Own Submission Status & Detailed Failure Diagnostics. |

---

## 🏗️ Architecture & Technology Stack

### Architecture Diagram
```
                     +---------------------------------------+
                     |    React 19 + Vite Frontend (SPA)     |
                     |  (Auditor, HOD, & Faculty Dashboards) |
                     +---------------------------------------+
                                         │
                         HTTP Session Cookie (Lax)
                         withCredentials: true
                                         ▼
                     +---------------------------------------+
                     |       FastAPI Application Core        |
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

### Technologies Used
- **Backend**: Python 3.10+, FastAPI, Starlette Sessions, PyMuPDF (`fitz`), Psycopg2, BCrypt, Pydantic v2.
- **Frontend**: React 19, Vite, Axios, Pure Modern Responsive CSS Design System.
- **Database**: PostgreSQL (Relational schema, foreign keys, JSONB for analysis results).
- **Authentication**: Starlette SessionMiddleware (HTTP-only session cookies, SHA-256 hashed OTPs with expiry & attempt limits, BCrypt password hashing). **No JWT / No localStorage tokens**.

---

## 🗄️ Database Schema & Relationships

The database utilizes relational integrity across 6 primary tables:
- `institution`: Registered universities/colleges (e.g. ID `6`: *Anantha Lakshmi Institute of Technology and Sciences*).
- `departments`: Department branches (`CSE`, `CSD`, `CSM`, `ECE`, `ME`, `CE`, etc.) linked to `institution_id`.
- `users`: User profiles with `email`, `password_hash`, `role` (`Auditor`, `HOD`, `Faculty`), `department_id`, and `institution_id`.
- `document_types`: Active types: `Course Structure`, `Question Bank`, `Question Paper`.
- `document_formats`: Master templates defined by Auditors containing `format_name`, `instructions`, `document_type_id`, `department_id` (nullable for institution-wide formats), and `institution_id`.
- `format_requirements`: Dynamic structural rules linked to a format:
  - `requirement_name`: e.g. "Part A Question Count", "College Header", "Unit 1 Heading"
  - `requirement_type`: `text`, `heading`, `section`, `field`, `question_count`, `marks`, `header`, `footer`, `arrangement`
  - `requirement_value`: Expected pattern (e.g., `5`, `10 marks`, `Mid Examination`)
  - `is_required`: Boolean (mandatory vs optional)
  - `display_order`: Integer sequence
- `documents`: Uploaded records storing `file_name` (original), `file_path` (safe UUID file), `uploaded_by`, `analysis_status` (`PENDING`, `ACCEPTED`, `REJECTED`), `analysis_result` (JSONB), and timestamps.
- `login_otps`: OTP authentication logs with `otp_hash`, `expires_at`, `attempts`, and `is_used`.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- PostgreSQL running locally (default database: `mydatabase`)

### 2. Database Setup & Migration
Verify that your PostgreSQL instance is running on `localhost:5432` with user `postgres`.
Run the database migration script:
```powershell
python database/apply_migration.py
```

### 3. Backend Setup
Install Python dependencies:
```powershell
pip install fastapi uvicorn pymupdf python-multipart psycopg2 bcrypt pydantic httpx
```

Start the FastAPI backend server:
```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend API documentation is available at: `http://127.0.0.1:8000/docs`.

### 4. Frontend Setup
From the `frontend` folder:
```powershell
cd frontend
npm install
npm run dev
```
Open your browser and navigate to: `http://localhost:5173`.

---

## 🔑 Prototype Credentials

For college demonstration and evaluation, the following pre-seeded credentials are ready to use:

| Role | Institution | Email | Password | Department |
| :--- | :--- | :--- | :--- | :--- |
| **Auditor** | Anantha Lakshmi Institute of Technology and Sciences | `auditor@alitsprototype.test` | `Auditor@123` | *All Departments* |
| **HOD** | Anantha Lakshmi Institute of Technology and Sciences | `hod.cse@alitsprototype.test` | `Hod@123` | CSE |
| **Faculty** | Anantha Lakshmi Institute of Technology and Sciences | `faculty.cse@alitsprototype.test` | `Faculty@123` | CSE |

> [!NOTE]
> **OTP Login Flow:**
> When logging in, enter the Institution, Role, Email, and Password. The system dispatches a 6-digit OTP. In local development/demo environments, the OTP is printed directly in the **backend terminal console** for instant verification.

---

## 📋 Major Workflows

### 1. Auditor: Format Definition
1. Login as **Auditor** (`auditor@alitsprototype.test` / `Auditor@123`).
2. Navigate to the **Format Builder** tab.
3. Select Document Type:
   - **Course Structure**: Load standard template with College Name, Course Details, and Units 1–5 Headings & Topics.
   - **Question Bank**: Load standard template for Units 1–5 with Part A (10 × 2M) and Part B (10 × 10M).
   - **Question Paper**: Select Examination Pattern (**Mid Examination** vs **Semester Examination**) to load standard rules for questions and marks patterns.
4. Click **Save Structural Format**. The format and rules are persisted in the PostgreSQL database.

### 2. Faculty: PDF Upload & Verification
1. Login as **Faculty** (`faculty.cse@alitsprototype.test` / `Faculty@123`).
2. Select Document Type and choose a PDF file.
3. Click **Upload & Run Structural Analysis**.
4. The system:
   - Stores the PDF immutably in `uploads/` with a UUID.
   - Extracts document layout and text blocks using PyMuPDF.
   - Evaluates each requirement against structural extractors.
   - Sets status to **`ACCEPTED`** (if 100% mandatory rules pass) or **`REJECTED`** (if any rule fails).
5. Click **Breakdown** to view the requirement checklist with green checkmarks or red crossmarks with exact failure reasons.

### 3. HOD & Auditor: Review & Download
1. Login as **HOD** (`hod.cse@alitsprototype.test` / `Hod@123`) or **Auditor**.
2. View all submitted documents and their decisions.
3. Access the **Accepted PDFs** tab.
4. Preview the document inline or download the official verified PDF.
5. *Security guarantee:* Attempting to download a rejected document is rejected with `403 Forbidden`.

---

## 🧪 Automated Testing

A comprehensive end-to-end test suite validates all workflows, role security, decision rules, and session lifecycle:
```powershell
python test_e2e_workflow.py
python test_course_structure.py
```

Tests verify:
- Invalid credentials, wrong institution, and wrong role rejection (401).
- Bad OTP and expired OTP rejection (400).
- Session creation and restoration via `/auth/me`.
- Auditor master format creation and persistence.
- Faculty PDF upload and PyMuPDF structural analysis.
- Strict ACCEPTED decision when all rules pass.
- Strict REJECTED decision when any rule fails (with diagnostics).
- HOD and Auditor authorized download of accepted PDFs.
- Rejection enforcement (rejected PDFs cannot be downloaded).
- Logout session destruction.

---

## 🎓 Guide Review & Presentation Summary

When presenting to your college project guide, emphasize these architectural highlights:
1. **Separation of Structure vs Meaning**: The system does not attempt subjective academic grading or AI hallucination; it uses deterministic structural pattern matching (PyMuPDF geometry, regex tokens, block analysis) to ensure institutional formatting standards are rigorously met.
2. **Strict Boolean Compliance**: Unlike arbitrary percentages, institutional accreditation requires absolute compliance—every mandatory section must exist, question counts must match the exam pattern, and marks schemes must align.
3. **Session-Based Enterprise Security**: Uses HTTP-only cookie sessions with CSRF protection and role-based access control (RBAC), preventing common token leakage vulnerabilities associated with JWT and localStorage.
4. **Dynamic Rule Engine**: Auditors are not programmers—they configure dynamic rules through a user-friendly GUI builder, and the backend engine compiles and evaluates them at runtime.