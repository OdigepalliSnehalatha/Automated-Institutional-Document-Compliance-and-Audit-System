from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from backend.services.auth_service import get_current_user
from backend.database import get_db_cursor

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

@router.post("/chat")
def handle_ai_chat(data: ChatRequest, current_user: dict = Depends(get_current_user)):
    user_msg = data.message.strip()
    user_role = current_user.get("role")
    user_name = current_user.get("name") or "Colleague"
    user_id = current_user.get("id")
    inst_id = current_user.get("institution_id")
    dept_id = current_user.get("department_id")
    dept_name = current_user.get("department_name") or "General"
    inst_name = current_user.get("institution_name") or "Institution"

    lower_query = user_msg.lower()

    # Universal Academic Knowledge Checks (Mid, Resume, JNTUK Curricula)
    if any(k in lower_query for k in ["resume", "cv", "curriculum vitae"]):
        return {
            "response": (
                "📄 **Institutional Resume / Curriculum Vitae Standard (10 Mandatory Points)**:\n\n"
                "1. **Candidate Full Name & Header**: Legal name & engineering qualification prominently placed at top.\n"
                "2. **Contact Information & Location**: Active 10-digit telephone, institutional/personal email, and city/state.\n"
                "3. **Professional Summary / Objective**: 2–4 concise lines articulating domain expertise and technical focus.\n"
                "4. **Educational Qualifications**: Chronological records (B.Tech, Inter/Diploma, SSC) with Institute, Year & CGPA/%.\n"
                "5. **Technical Skills**: Structured categories (Languages, Frameworks, Databases, Developer Tools).\n"
                "6. **Academic Projects**: Title, tech stack utilized, personal contribution, and verifiable outcomes.\n"
                "7. **Work Experience / Internships**: Industry internships, company name, role, and key milestones.\n"
                "8. **Certifications & Badges**: Accredited industrial/NPTEL/Coursera credentials with year.\n"
                "9. **Achievements & Extracurricular**: Hackathons, paper presentations, awards, and technical societies.\n"
                "10. **Declaration & Signature**: Formal declaration affirming authenticity with Place, Date & Signature.\n\n"
                "💡 *Resumes must achieve at least 80% compliance across these 10 criteria for institutional acceptance.*"
            )
        }

    if any(k in lower_query for k in ["mid 1", "mid 2", "mid-1", "mid-2", "mid exam", "i-mid", "ii-mid", "40 mark", "40m"]):
        return {
            "response": (
                "📝 **ALITS Autonomous Regulations (R-24) Question Paper Standard**:\n\n"
                "- **Institutional Header**: Anantha Lakshmi Institute of Technology & Sciences (AUTONOMOUS), Near S.K. University, Ananthapuramu- 515721\n"
                "- **Examination Title**: 'I-MID Examinations' (Mid 1) or 'II-MID Examinations' (Mid 2)\n"
                "- **Time Duration**: Exactly `110 Min`\n"
                "- **Maximum Marks**: Exactly `40 Marks`\n"
                "- **General Instruction**: 'Answer all questions'\n"
                "- **Structure**: Unified continuous examination layout without 'Part A' or 'Part B' subheadings.\n"
                "- **Unit Syllabus Coverage**:\n"
                "  • **Mid-1**: Covers Unit-I, Unit-II, and Unit-III (Part)\n"
                "  • **Mid-2**: Covers Unit-III (Part), Unit-IV, and Unit-V\n\n"
                "💡 *All papers must include Bloom's Taxonomy Cognitive Levels (L1-L4) and Course Outcomes (CO1-CO5) for every question.*"
            )
        }

    if any(k in lower_query for k in ["jntu", "jntuk", "curriculum", "syllabus", "branches", "all subjects", "all semesters"]):
        return {
            "response": (
                "🎓 **JNTUK & ALITS Autonomous Curriculum (1-1 Sem to 4-2 Sem)**:\n\n"
                "- **All 9 Engineering Branches Configured**:\n"
                "  1. Computer Science & Engineering (CSE)\n"
                "  2. Computer Science & Design (CSD)\n"
                "  3. Computer Science & Machine Learning (CSM)\n"
                "  4. CSE - Artificial Intelligence & ML (CSE-AIML)\n"
                "  5. Computer Artificial Intelligence (CAI)\n"
                "  6. Electronics & Communication Engineering (ECE)\n"
                "  7. Electrical & Electronics Engineering (EEE)\n"
                "  8. Mechanical Engineering (ME)\n"
                "  9. Civil Engineering (CE)\n\n"
                "- **Curricular Structure**:\n"
                "  • **1st Year (1-1 & 1-2)**: Foundational mathematics, physics, chemistry, C programming, basic electrical/electronics, drawing, and engineering workshops.\n"
                "  • **2nd to 4th Year (2-1 to 4-2)**: Core specializations, professional electives, open electives, industrial internships, and major capstone projects.\n"
                "  • **Total Courses Seeded**: 494 verified departmental courses with assigned faculty."
            )
        }


    with get_db_cursor() as cursor:
        # =========================================================
        # 1. ADMIN ROLE CONTEXT & RESPONSES
        # =========================================================
        if user_role == "Admin":
            if any(k in lower_query for k in ["institution", "info", "college", "summary", "about"]):
                cursor.execute("SELECT name, email, created_at FROM institution WHERE id = %s", (inst_id,))
                inst_row = cursor.fetchone() or {}
                cursor.execute("SELECT COUNT(*) AS c FROM departments WHERE institution_id = %s", (inst_id,))
                dep_c = cursor.fetchone()["c"]
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) FILTER (WHERE role = 'Faculty') AS f,
                        COUNT(*) FILTER (WHERE role = 'HOD') AS h,
                        COUNT(*) FILTER (WHERE role = 'Auditor') AS a
                    FROM users WHERE institution_id = %s
                    """,
                    (inst_id,)
                )
                u_row = cursor.fetchone() or {}
                cursor.execute("SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE analysis_status = 'ACCEPTED') AS acc FROM documents WHERE institution_id = %s", (inst_id,))
                d_row = cursor.fetchone() or {}
                rate = round((d_row['acc'] / d_row['total'] * 100), 1) if d_row['total'] > 0 else 0.0

                return {
                    "response": (
                        f"🏛️ **Institutional Overview for {inst_name}**:\n\n"
                        f"- **Institution Head Email:** `{inst_row.get('email', 'N/A')}`\n"
                        f"- **Total Active Engineering Branches:** {dep_c} (CSE, CSD, CSM, CSE-AIML, ECE, ME, CE, CAI)\n"
                        f"- **Registered Personnel:** {u_row.get('f', 0)} Faculty, {u_row.get('h', 0)} HODs, {u_row.get('a', 0)} Auditors\n"
                        f"- **Total Document Submissions:** {d_row.get('total', 0)} ({d_row.get('acc', 0)} Accepted)\n"
                        f"- **Overall Compliance Rate:** {rate}%\n\n"
                        f"You can manage institution details, view all department directories, and monitor compliance directly from the Admin Sidebar."
                    )
                }

            elif any(k in lower_query for k in ["faculty", "hod", "auditor", "personnel", "staff", "users", "registered"]):
                cursor.execute(
                    """
                    SELECT role, COUNT(*) AS count
                    FROM users WHERE institution_id = %s
                    GROUP BY role
                    """,
                    (inst_id,)
                )
                counts = {r["role"]: r["count"] for r in cursor.fetchall()}
                return {
                    "response": (
                        f"👥 **Institutional Personnel Registry**:\n\n"
                        f"- **Faculty Members:** {counts.get('Faculty', 0)}\n"
                        f"- **Department Heads (HODs):** {counts.get('HOD', 0)}\n"
                        f"- **Compliance Auditors:** {counts.get('Auditor', 0)}\n"
                        f"- **System Administrators:** {counts.get('Admin', 0)}\n\n"
                        f"All staff are mapped to their respective departments and authentication records."
                    )
                }

            elif any(k in lower_query for k in ["pending", "activity", "activities", "tasks", "status"]):
                cursor.execute(
                    """
                    SELECT COUNT(*) AS pending, COUNT(*) AS rejected, COUNT(*) AS accepted, COUNT(*) AS total
                    FROM documents WHERE institution_id = %s
                    """,
                    (inst_id,)
                )
                st = cursor.fetchone() or {}
                return {
                    "response": (
                        f"📊 **Current Institutional Document Activity**:\n\n"
                        f"- **Total Documents Uploaded:** {st.get('total', 0)}\n"
                        f"- **Verified & Accepted:** {st.get('accepted', 0)}\n"
                        f"- **Strictly Rejected (Defective):** {st.get('rejected', 0)}\n"
                        f"- **Pending Analysis:** {st.get('pending', 0)}\n\n"
                        f"You can view the full institutional documents list under **All Documents** in your sidebar."
                    )
                }

            elif any(k in lower_query for k in ["branch", "branches", "departments", "cai"]):
                cursor.execute("SELECT code, name FROM departments WHERE institution_id = %s ORDER BY id", (inst_id,))
                depts = cursor.fetchall()
                dept_list = "\n".join([f"- **{d['code']}**: {d['name']}" for d in depts])
                return {
                    "response": (
                        f"🏢 **Active Engineering Branches ({len(depts)})**:\n\n"
                        f"{dept_list}\n\n"
                        f"Note: **CAI** (Computer Artificial Intelligence) is actively integrated for multi-branch compliance."
                    )
                }

            else:
                return {
                    "response": (
                        f"Hello Admin {user_name}! As the Institution Head, you have executive oversight across {inst_name}.\n\n"
                        f"Here are topics I can help you with:\n"
                        f"• Ask **'Show institution information'** for high-level metrics and details.\n"
                        f"• Ask **'How many faculty are registered?'** for personnel breakdown.\n"
                        f"• Ask **'What are the pending activities?'** for audit progress.\n"
                        f"• Ask **'List all engineering branches'** for active departments."
                    )
                }

        # =========================================================
        # 2. FACULTY ROLE CONTEXT & RESPONSES
        # =========================================================
        elif user_role == "Faculty":
            if any(k in lower_query for k in ["task", "assigned", "my document", "my upload", "submission", "status"]):
                cursor.execute(
                    """
                    SELECT file_name, analysis_status, uploaded_at 
                    FROM documents 
                    WHERE uploaded_by = %s 
                    ORDER BY uploaded_at DESC LIMIT 5
                    """,
                    (user_id,)
                )
                my_docs = cursor.fetchall()
                if not my_docs:
                    return {
                        "response": (
                            f"You haven't uploaded any documents yet, {user_name}.\n\n"
                            f"To get started, click **'Upload & Verify'** in your sidebar. Select your document type (Question Paper, Course Structure, or Question Bank), choose the branch (such as CAI or CSE), and upload your PDF."
                        )
                    }
                doc_lines = "\n".join([f"- **{d['file_name']}**: Status is `{d['analysis_status'] or 'PENDING'}`" for d in my_docs])
                return {
                    "response": (
                        f"📄 **Your Recent Submissions ({len(my_docs)})**:\n\n"
                        f"{doc_lines}\n\n"
                        f"Tip: If any document is `REJECTED`, click the **Breakdown** button in your dashboard to view the exact missing structural rules!"
                    )
                }

            elif any(k in lower_query for k in ["question paper", "qp", "mid", "semester", "part a", "part b", "marks"]):
                return {
                    "response": (
                        f"📝 **Question Paper Structural Requirements**:\n\n"
                        f"To achieve an **`ACCEPTED`** decision, your Question Paper PDF must satisfy:\n"
                        f"1. **Header**: College Name, B.Tech, Semester, Subject Name & Code, Branch, Max Marks, Time.\n"
                        f"2. **Mid Examination Pattern**:\n"
                        f"   - **Part A**: 5 questions, each carrying 2 marks (total 10 marks).\n"
                        f"   - **Part B**: 6 questions, each carrying 10 marks (total 60 marks).\n"
                        f"3. **Semester Examination Pattern**:\n"
                        f"   - **Part A**: 10 questions of 2 marks.\n"
                        f"   - **Part B**: 10 questions of 10 marks.\n"
                        f"4. **Boolean Rule**: Missing any single question or section results in strict **`REJECTED`**."
                    )
                }

            elif any(k in lower_query for k in ["course", "structure", "syllabus", "unit"]):
                return {
                    "response": (
                        f"📚 **Course Structure Formatting Rules**:\n\n"
                        f"1. **Institute Header**: College name and department at the top.\n"
                        f"2. **Course Details**: Course Name and Course Code.\n"
                        f"3. **Curriculum Units**: All five units must be present:\n"
                        f"   - **Unit 1 Heading** followed by Unit 1 Topics\n"
                        f"   - **Unit 2 Heading** followed by Unit 2 Topics\n"
                        f"   - **Unit 3 Heading** followed by Unit 3 Topics\n"
                        f"   - **Unit 4 Heading** followed by Unit 4 Topics\n"
                        f"   - **Unit 5 Heading** followed by Unit 5 Topics\n"
                        f"Missing any unit heading or topic section will cause structural rejection."
                    )
                }

            elif any(k in lower_query for k in ["rejected", "fail", "reason", "diagnostic"]):
                cursor.execute(
                    """
                    SELECT file_name, analysis_result 
                    FROM documents 
                    WHERE uploaded_by = %s AND analysis_status = 'REJECTED'
                    ORDER BY analyzed_at DESC LIMIT 1
                    """,
                    (user_id,)
                )
                last_rej = cursor.fetchone()
                if last_rej:
                    return {
                        "response": (
                            f"⚠️ **Last Rejected Document Diagnostics**:\n\n"
                            f"File: **{last_rej['file_name']}**\n\n"
                            f"The system strictly enforces 100% compliance. If any mandatory header, section (Part A / Part B), question count, or marks pattern is missing or unformatted, the entire PDF is marked `REJECTED`.\n\n"
                            f"Check the **Breakdown** button next to your document to see the exact failed rules in red."
                        )
                    }
                else:
                    return {
                        "response": "Great news! You have no rejected documents recorded."
                    }

            else:
                return {
                    "response": (
                        f"Hello {user_name}! I am your Faculty Compliance Assistant.\n\n"
                        f"Feel free to ask me:\n"
                        f"• **'What tasks are assigned to me?'** to check your uploaded documents.\n"
                        f"• **'Explain question paper requirements'** for Part A and Part B rules.\n"
                        f"• **'Explain course structure rules'** for Units 1-5 requirements.\n"
                        f"• **'Why was my document rejected?'** for common compliance issues."
                    )
                }

        # =========================================================
        # 3. HOD ROLE CONTEXT & RESPONSES
        # =========================================================
        elif user_role == "HOD":
            if any(k in lower_query for k in ["department", "dept", "overview", "info", "summary"]):
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE analysis_status = 'ACCEPTED') AS accepted,
                        COUNT(*) FILTER (WHERE analysis_status = 'REJECTED') AS rejected,
                        COUNT(*) FILTER (WHERE analysis_status = 'PENDING' OR analysis_status IS NULL) AS pending
                    FROM documents 
                    WHERE department_id = %s
                    """,
                    (dept_id,)
                )
                st = cursor.fetchone() or {}
                return {
                    "response": (
                        f"🏛️ **Department Overview for {dept_name}**:\n\n"
                        f"- **Total Faculty Submissions:** {st.get('total', 0)}\n"
                        f"- **Strictly Accepted:** {st.get('accepted', 0)}\n"
                        f"- **Strictly Rejected:** {st.get('rejected', 0)}\n"
                        f"- **Pending Analysis:** {st.get('pending', 0)}\n\n"
                        f"You can review all department submissions and download verified accepted PDFs from your sidebar."
                    )
                }

            elif any(k in lower_query for k in ["pending", "review", "waiting"]):
                cursor.execute(
                    """
                    SELECT file_name, u.name AS uploader 
                    FROM documents d
                    LEFT JOIN users u ON u.id = d.uploaded_by
                    WHERE d.department_id = %s AND (d.analysis_status = 'PENDING' OR d.analysis_status IS NULL)
                    LIMIT 5
                    """,
                    (dept_id,)
                )
                pend = cursor.fetchall()
                if not pend:
                    return {"response": "There are currently no pending document analyses in your department."}
                p_lines = "\n".join([f"- **{p['file_name']}** (by {p['uploader'] or 'Faculty'})" for p in pend])
                return {
                    "response": f"⏳ **Pending Submissions in {dept_name} ({len(pend)})**:\n\n{p_lines}"
                }

            elif any(k in lower_query for k in ["accepted", "download", "verified"]):
                cursor.execute(
                    "SELECT COUNT(*) AS c FROM documents WHERE department_id = %s AND analysis_status = 'ACCEPTED'",
                    (dept_id,)
                )
                acc_c = cursor.fetchone()["c"]
                return {
                    "response": (
                        f"✓ **Verified Compliant Documents for {dept_name}**:\n\n"
                        f"There are **{acc_c}** officially accepted PDFs in your department.\n\n"
                        f"As HOD, you are authorized to download these records. Navigate to **Accepted Official PDFs** in your sidebar to view or download them."
                    )
                }

            else:
                return {
                    "response": (
                        f"Hello HOD {user_name}! I am your Department Audit Assistant for {dept_name}.\n\n"
                        f"You can ask me:\n"
                        f"• **'Show my department information'** for submission statistics.\n"
                        f"• **'What activities are pending?'** to see unanalyzed submissions.\n"
                        f"• **'How many submissions are accepted?'** for verified documents."
                    )
                }

        # =========================================================
        # 4. AUDITOR ROLE CONTEXT & RESPONSES
        # =========================================================
        elif user_role == "Auditor":
            if any(k in lower_query for k in ["status", "audit", "overview", "progress"]):
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE analysis_status = 'ACCEPTED') AS accepted,
                        COUNT(*) FILTER (WHERE analysis_status = 'REJECTED') AS rejected,
                        COUNT(*) FILTER (WHERE analysis_status = 'PENDING' OR analysis_status IS NULL) AS pending
                    FROM documents 
                    WHERE institution_id = %s
                    """,
                    (inst_id,)
                )
                st = cursor.fetchone() or {}
                cursor.execute("SELECT COUNT(*) AS f FROM document_formats WHERE institution_id = %s", (inst_id,))
                fc = cursor.fetchone()["f"]
                return {
                    "response": (
                        f"📊 **Institutional Audit Status**:\n\n"
                        f"- **Total Submissions Audited:** {st.get('total', 0)}\n"
                        f"- **Strictly Accepted:** {st.get('accepted', 0)}\n"
                        f"- **Strictly Rejected:** {st.get('rejected', 0)}\n"
                        f"- **Pending Analysis:** {st.get('pending', 0)}\n"
                        f"- **Master Formats Defined:** {fc}\n\n"
                        f"Remember: The system uses a strict Boolean decision policy (100% compliance required for acceptance)."
                    )
                }

            elif any(k in lower_query for k in ["format", "preset", "rule", "builder", "template"]):
                return {
                    "response": (
                        f"⚙️ **Structural Format Templates**:\n\n"
                        f"As Auditor, you configure the compliance rules that faculty submissions are checked against:\n"
                        f"1. **Course Structure Template**: Units 1–5 headings and topic section rules.\n"
                        f"2. **Question Bank Template**: Units 1–5 Part A (10 x 2M) and Part B (10 x 10M).\n"
                        f"3. **Mid Examination Question Paper Template**: Part A (5 x 2M) + Part B (6 x 10M).\n"
                        f"4. **Semester Examination Question Paper Template**: Part A (10 x 2M) + Part B (10 x 10M).\n\n"
                        f"Use the **Format Builder** in your sidebar to create or activate templates with 1 click."
                    )
                }

            elif any(k in lower_query for k in ["review", "pending", "queue"]):
                cursor.execute(
                    """
                    SELECT d.id, d.file_name, dept.code AS dept_code, u.name AS uploader
                    FROM documents d
                    LEFT JOIN departments dept ON dept.id = d.department_id
                    LEFT JOIN users u ON u.id = d.uploaded_by
                    WHERE d.institution_id = %s AND (d.analysis_status = 'PENDING' OR d.analysis_status IS NULL)
                    LIMIT 5
                    """,
                    (inst_id,)
                )
                pend = cursor.fetchall()
                if not pend:
                    return {"response": "All uploaded documents have been structurally analyzed. No pending documents in the queue."}
                p_lines = "\n".join([f"- **{p['file_name']}** ({p['dept_code']}, by {p['uploader']})" for p in pend])
                return {
                    "response": f"📋 **Documents Awaiting Review ({len(pend)})**:\n\n{p_lines}"
                }

            else:
                return {
                    "response": (
                        f"Hello Auditor {user_name}! I am your Structural Audit Assistant.\n\n"
                        f"You can ask me:\n"
                        f"• **'What is the current audit status?'** for institution-wide compliance stats.\n"
                        f"• **'Which documents need review?'** to see pending submissions.\n"
                        f"• **'What format presets are available?'** for rule templates.\n"
                        f"• **'Explain the Boolean compliance decision rule'** for structural logic."
                    )
                }

        else:
            return {
                "response": "Hello! I am your Institutional Compliance Assistant. How may I help you today?"
            }
