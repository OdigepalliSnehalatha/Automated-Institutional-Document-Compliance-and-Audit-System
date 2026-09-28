# Project Guide Review & Viva Defense Notes

**Project Title:** Automated Institutional Document Compliance and Audit System  
**Domain:** Enterprise Web Applications, Document Processing, Institutional Compliance  
**Tech Stack:** FastAPI (Python 3.10+), PyMuPDF (`pymupdf`), React 19, Vite, PostgreSQL  

---

## 🎯 1. Problem Statement & Motivation
* **Problem:** In engineering colleges and universities, accreditation bodies (NBA, NAAC, Autonomous Academic Councils) mandate strict structural standards for syllabi, question papers, and question banks. Academic audits require manual checking of every paper for mandatory headers, section breakdown, question count per unit, and marks schemes. This process is time-consuming, prone to human oversight, and delays examination clearance.
* **Solution:** An automated system where Auditors define dynamic structural rules, Faculty submit PDFs for instantaneous structural analysis, and the system strictly accepts or rejects documents with requirement-by-requirement diagnostics.

---

## 💡 2. Key Architectural Decisions (Why this design?)

### Q: Why structural analysis instead of semantic / AI text generation?
> **Answer:**
> Academic compliance is inherently **deterministic and structural**, not subjective. Accreditation audits require checking whether:
> - College header and examination details exist.
> - Required sections (e.g. Part A, Part B, Units 1–5) are present.
> - Question counts (e.g. 5 questions in Mid, 10 in Semester) match the approved pattern.
> - Marks distribution (e.g. 2 marks per question in Part A) matches regulatory guidelines.
> 
> Evaluating subjective meaning or answers with AI/LLMs introduces hallucination, unpredictable variance, and unnecessary cost. PyMuPDF-based deterministic structural comparison ensures 100% precision, zero false passes, and reproducible audit logs.

### Q: Why strict Boolean ACCEPTED/REJECTED rather than a percentage score?
> **Answer:**
> In formal academic regulations, there is no such thing as an examination paper that is "80% compliant." If Part B is missing or question marks do not total the required scheme, the paper is invalid. Therefore, the decision rule is strictly Boolean:
> $$\text{Decision} = \begin{cases} \text{ACCEPTED} & \text{if } \forall r \in R_{\text{required}}, \text{Status}(r) = \text{PASS} \\ \text{REJECTED} & \text{otherwise} \end{cases}$$

### Q: Why Session Cookies instead of JWT stored in LocalStorage?
> **Answer:**
> - LocalStorage is vulnerable to Cross-Site Scripting (XSS) token theft.
> - JWTs cannot be revoked instantly on server-side logout without maintaining a token blacklist.
> - Starlette `SessionMiddleware` utilizes signed HTTP-only cookies with `SameSite=Lax`. Sessions can be destroyed instantly on the server (`request.session.clear()`), providing enterprise-grade security.

---

## 🔄 3. End-to-End System Workflow

```
[Auditor]
   │
   ├─► Log in via Email + Password + 6-digit OTP
   ├─► Open Format Builder (GUI)
   ├─► Selects Document Type (Course Structure / Question Bank / Question Paper)
   ├─► Loads 1-Click Standard Preset or enters custom structural rules
   └─► Persists format in PostgreSQL (`document_formats` & `format_requirements`)

[Faculty]
   │
   ├─► Log in via Department Credentials + OTP
   ├─► Selects Document Type & uploads PDF
   ├─► PDF is stored with safe UUID filename in `uploads/` (original preserved)
   ├─► System extracts text blocks, headers, footers, and section markers via PyMuPDF
   ├─► Compares extracted features against Auditor's active format requirements
   └─► Strictly evaluates ACCEPTED or REJECTED with full checklist diagnostics

[HOD & Auditor]
   │
   ├─► Log in via Role Credentials + OTP
   ├─► Review department / institutional submissions
   ├─► Inspect structural comparison breakdown
   └─► View & Download verified ACCEPTED official PDFs (Rejected downloads blocked with 403)
```

---

## 🛡️ 4. Security & Role Permissions Matrix

| Endpoint | Description | Auditor | HOD | Faculty | Unauthenticated |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `POST /login` | Submit credentials & dispatch OTP | ✅ | ✅ | ✅ | ✅ |
| `POST /verify-otp` | Verify OTP & create session | ✅ | ✅ | ✅ | ✅ |
| `GET /auth/me` | Restore authenticated session | ✅ | ✅ | ✅ | ❌ (401) |
| `POST /formats` | Define/edit structural format | ✅ | ❌ (403) | ❌ (403) | ❌ (401) |
| `POST /documents/upload` | Upload PDF for verification | ❌ | ❌ | ✅ | ❌ (401) |
| `POST /documents/{id}/analyze` | Trigger structural analysis | ✅ | ✅ | ✅ (Own) | ❌ (401) |
| `GET /documents/{id}/view` | View PDF in browser | ✅ | ✅ (Dept) | ✅ (Own) | ❌ (401) |
| `GET /documents/{id}/download` | Download accepted PDF | ✅ | ✅ (Dept) | ❌ (403) | ❌ (401) |

---

## 📊 5. Demonstration Checklist for Review Day

1. **Start Servers:** Double-click `start_all.bat` (launches backend on `:8000` and frontend on `:5173`).
2. **Show Format Builder:** Log in as Auditor (`auditor@alitsprototype.test` / `Auditor@123`). Load standard presets for Mid Examination (Part A 5x2M, Part B 6x10M).
3. **Show Faculty Upload & Instant Analysis:** Log in as Faculty (`faculty.cse@alitsprototype.test` / `Faculty@123`).
   - Upload `Sample_Mid_Question_Paper_Valid.pdf` $\rightarrow$ Show **ACCEPTED** result.
   - Upload `Sample_Question_Paper_Defective.pdf` $\rightarrow$ Show **REJECTED** result with diagnostic reasons.
4. **Show HOD Oversight & Download:** Log in as HOD (`hod.cse@alitsprototype.test` / `Hod@123`). Show that accepted PDF can be downloaded, and show that rejected PDF is prevented from download.
5. **Show Code Architecture:** Show modular backend structure (`backend/routes`, `backend/services`, `backend/models`) and automated tests (`test_e2e_workflow.py`).
