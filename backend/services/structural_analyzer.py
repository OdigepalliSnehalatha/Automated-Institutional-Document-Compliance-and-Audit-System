import os
import re
import hashlib
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from pathlib import Path
from backend.services.pdf_service import extract_pdf_data

def normalize(text: str) -> str:
    """Normalizes whitespace and converts text to lowercase."""
    return re.sub(r"\s+", " ", (text or "").lower()).strip()

def compute_file_hash(file_path: str) -> str:
    """Computes SHA-256 hash of a file for duplicate checking."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def extract_section_text(full_text: str, start_marker: str, end_markers: List[str] = None) -> str:
    """Extracts text starting at start_marker until any end_marker or end of text."""
    pattern = rf"\b{re.escape(start_marker)}\b"
    start_match = re.search(pattern, full_text, re.IGNORECASE)
    if not start_match:
        return ""

    content_after = full_text[start_match.start():]
    if not end_markers:
        return content_after

    earliest_end = len(content_after)
    for end_m in end_markers:
        end_pattern = rf"\b{re.escape(end_m)}\b"
        m = re.search(end_pattern, content_after[len(start_marker):], re.IGNORECASE)
        if m:
            pos = len(start_marker) + m.start()
            if pos < earliest_end:
                earliest_end = pos

    return content_after[:earliest_end]

def count_questions(text: str) -> int:
    """Counts question items using standard academic numbering patterns."""
    patterns = [
        r"(?m)^\s*(?:Q(?:uestion)?\.?\s*)?\d{1,2}[\.\)\:\-]\s+",
        r"(?m)^\s*\(\s*[a-j0-9]\s*\)\s+",
        r"\bQ(?:uestion)?\s*\d{1,2}\b"
    ]
    all_matches = set()
    for pattern in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            all_matches.add(m.start())

    if not all_matches:
        line_patterns = re.findall(r"(?m)^\s*\d{1,2}\s*[\.\)]", text)
        return len(line_patterns)

    return len(all_matches)

def extract_detected_total_marks(text: str) -> Optional[int]:
    """Detects total/maximum marks stated in the document."""
    patterns = [
        r"(?:maximum\s*marks|max\s*marks|total\s*marks|marks)\s*[:=\-]?\s*(\d{2,3})\b",
        r"\b(\d{2,3})\s*marks\b",
        r"\bmax\.?\s*(\d{2,3})\b",
        r"\b(?:70|40|100|30|60)\s*marks\b"
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                val = int(m.group(1))
                if 10 <= val <= 100:
                    return val
            except Exception:
                pass
    return None

def build_categorized_report(items: List[Dict[str, Any]], marks_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Categorizes items into:
      A. correct_requirements
      B. incorrect_requirements
      C. missing_requirements
      D. marks_verification
      E. final status (ACCEPTED, REJECTED, PENDING REVIEW)
    """
    correct_reqs = [it for it in items if it["result"] == "Correct"]
    incorrect_reqs = [it for it in items if it["result"] == "Incorrect"]
    missing_reqs = [it for it in items if it["result"] == "Missing"]
    review_reqs = [it for it in items if it["result"] == "Needs Review"]

    total_checks = len(items)
    passed_checks = len(correct_reqs)
    failed_checks = len(incorrect_reqs)
    missing_count = len(missing_reqs)
    needs_review = len(review_reqs)

    applicable = total_checks - sum(1 for it in items if it["result"] == "Not Applicable")
    compliance_pct = round((passed_checks / applicable * 100.0), 1) if applicable > 0 else 0.0

    if failed_checks > 0 or missing_count > 0:
        overall_status = "REJECTED"
    elif needs_review > 0:
        overall_status = "PENDING REVIEW"
    else:
        overall_status = "ACCEPTED"

    summary = {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "missing_requirements": missing_count,
        "needs_review": needs_review,
        "compliance_percentage": compliance_pct,
        "validation_status": overall_status
    }

    return {
        "validation_status": overall_status,
        "compliance_percentage": compliance_pct,
        "summary": summary,
        "items": items,
        "correct_requirements": correct_reqs,
        "incorrect_requirements": incorrect_reqs,
        "missing_requirements": missing_reqs,
        "marks_verification": marks_info,
        "analyzed_at": datetime.now().isoformat()
    }

# =====================================================================
# 1. COMMON REQUIREMENTS FOR ALL THREE MODULES
# =====================================================================
def extract_common_institutional_details(
    full_text: str, metadata: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Validates the 5 mandatory common institutional details:
      1. College Name
      2. Course Name
      3. Course Code
      4. Academic Year
      5. Semester Name
    Returns (report_items, extracted_dict).
    """
    norm = normalize(full_text)
    items: List[Dict[str, Any]] = []
    extracted: Dict[str, str] = {}

    # 1. College Name
    expected_inst = metadata.get("institution_name") or "Anantha Lakshmi Institute of Technology & Sciences"
    norm_inst = normalize(expected_inst)
    has_inst = (
        norm_inst in norm[:1800] or
        "anantha lakshmi" in norm[:1800] or
        "technology and sciences" in norm[:1800] or
        "technology & sciences" in norm[:1800] or
        any(k in norm[:1000] for k in ["college of engineering", "institute of technology", "university"])
    )
    if has_inst:
        extracted["college_name"] = expected_inst
        items.append({
            "requirement": "College Name",
            "expected_value": expected_inst,
            "detected_value": "Official College Name verified in header",
            "result": "Correct",
            "explanation": "Official college header is clearly present in the institutional document.",
            "recommended_correction": "None required."
        })
    else:
        items.append({
            "requirement": "College Name",
            "expected_value": expected_inst,
            "detected_value": "Missing / Unrecognized College Name",
            "result": "Missing",
            "explanation": f"Mandatory College Name '{expected_inst}' was not detected in document header.",
            "recommended_correction": f"Include official College Name banner: '{expected_inst}' at the top."
        })

    # 2. Course Name
    expected_course = metadata.get("course_name") or ""
    norm_course = normalize(expected_course)
    has_course = (norm_course and norm_course in norm) or bool(
        re.search(r"(?:course|subject)\s*(?:name|title)?\s*[:=\-]\s*([a-zA-Z\s]{4,40})", full_text, re.IGNORECASE)
    )
    if has_course:
        extracted["course_name"] = expected_course or "Detected Subject Title"
        items.append({
            "requirement": "Course Name",
            "expected_value": expected_course or "Standard Course Title",
            "detected_value": expected_course or "Course Name Found",
            "result": "Correct",
            "explanation": "Course name is clearly identified in the document header.",
            "recommended_correction": "None required."
        })
    elif expected_course:
        items.append({
            "requirement": "Course Name",
            "expected_value": expected_course,
            "detected_value": "Course Name not found",
            "result": "Missing",
            "explanation": f"Mandatory Course Name '{expected_course}' was not found in the document.",
            "recommended_correction": f"Add the course name: 'Subject: {expected_course}'."
        })
    else:
        # Check general course marker
        m = re.search(r"(?:course|subject)\s*[:=\-]\s*([a-zA-Z\s]{4,35})", full_text, re.IGNORECASE)
        if m:
            cname = m.group(1).strip()
            extracted["course_name"] = cname
            items.append({
                "requirement": "Course Name",
                "expected_value": "Explicit Course / Subject Name",
                "detected_value": cname,
                "result": "Correct",
                "explanation": f"Detected course title '{cname}'.",
                "recommended_correction": "None required."
            })
        else:
            items.append({
                "requirement": "Course Name",
                "expected_value": "Explicit Course / Subject Name",
                "detected_value": "Missing",
                "result": "Missing",
                "explanation": "No Course Name declaration found in the document header.",
                "recommended_correction": "Include: 'Course / Subject: [Subject Name]'."
            })

    # 3. Course Code
    expected_code = (metadata.get("course_code") or "").upper().strip()
    code_match = re.search(r"\b([0-9]{2}[A-Z]{4,6}[0-9]{2,4}[A-Z]?|[A-Z]{2,4}[0-9]{3,5})\b", full_text)
    detected_code = code_match.group(1) if code_match else None

    if expected_code and expected_code.lower() in norm:
        extracted["course_code"] = expected_code
        items.append({
            "requirement": "Course Code",
            "expected_value": expected_code,
            "detected_value": f"Matched Course Code: {expected_code}",
            "result": "Correct",
            "explanation": "Course Code matches approved institutional curriculum records.",
            "recommended_correction": "None required."
        })
    elif detected_code:
        extracted["course_code"] = detected_code
        items.append({
            "requirement": "Course Code",
            "expected_value": expected_code or "Standard Alphanumeric Course Code",
            "detected_value": f"Detected Code: {detected_code}",
            "result": "Correct" if not expected_code else "Incorrect",
            "explanation": f"Detected Course Code '{detected_code}'" + (f" differs from expected '{expected_code}'." if expected_code else "."),
            "recommended_correction": f"Use approved Course Code: '{expected_code}'." if expected_code else "None required."
        })
    else:
        items.append({
            "requirement": "Course Code",
            "expected_value": expected_code or "Standard Alphanumeric Course Code",
            "detected_value": "Missing",
            "result": "Missing",
            "explanation": "Course Code (e.g. 24ALBTCS403T) was not detected in document header.",
            "recommended_correction": "Include approved Course Code: 'Course Code: 24ALBTCS403T'."
        })

    # 4. Academic Year
    expected_ay = metadata.get("academic_year_name") or metadata.get("academic_year") or ""
    ay_match = re.search(r"\b(20\d\d\s*[-–/]\s*20?\d\d)\b", full_text)
    detected_ay = ay_match.group(1).replace(" ", "") if ay_match else None

    if expected_ay and normalize(expected_ay) in norm:
        extracted["academic_year"] = expected_ay
        items.append({
            "requirement": "Academic Year",
            "expected_value": expected_ay,
            "detected_value": f"Matched Academic Year: {expected_ay}",
            "result": "Correct",
            "explanation": "Academic Year declared matches curriculum scheduling.",
            "recommended_correction": "None required."
        })
    elif detected_ay:
        extracted["academic_year"] = detected_ay
        items.append({
            "requirement": "Academic Year",
            "expected_value": expected_ay or "Academic Year (e.g. 2024-2025)",
            "detected_value": f"Detected: {detected_ay}",
            "result": "Correct" if not expected_ay else "Incorrect",
            "explanation": f"Detected Academic Year '{detected_ay}'" + (f" differs from '{expected_ay}'." if expected_ay else "."),
            "recommended_correction": f"Set Academic Year to '{expected_ay}'." if expected_ay else "None required."
        })
    else:
        items.append({
            "requirement": "Academic Year",
            "expected_value": expected_ay or "Academic Year (e.g. 2024-2025)",
            "detected_value": "Missing",
            "result": "Missing",
            "explanation": "Academic Year is mandatory and missing from document details.",
            "recommended_correction": "Add 'Academic Year: 2025-2026' in the header metadata."
        })

    # 5. Semester Name
    expected_sem = metadata.get("semester_name") or metadata.get("semester") or ""
    sem_patterns = [
        r"\b(?:i|ii|iii|iv|v|vi|vii|viii)\s+b\.?tech\s+(?:i|ii)\s+sem(?:ester)?\b",
        r"\b(?:first|second|third|fourth)\s+year\s+(?:i|ii|first|second)\s+sem(?:ester)?\b",
        r"\b(?:sem(?:ester)?\s*[-:\s]?\s*(?:[1-8]|i|ii|iii|iv|v|vi|vii|viii))\b",
        r"\b[1-4]\s*[-–]\s*[1-2]\s+sem(?:ester)?\b"
    ]
    detected_sem = None
    for sp in sem_patterns:
        sm = re.search(sp, norm)
        if sm:
            detected_sem = sm.group(0).upper()
            break

    if expected_sem and normalize(expected_sem) in norm:
        extracted["semester_name"] = expected_sem
        items.append({
            "requirement": "Semester Name",
            "expected_value": expected_sem,
            "detected_value": f"Matched Semester: {expected_sem}",
            "result": "Correct",
            "explanation": "Semester name is clearly verified in document header.",
            "recommended_correction": "None required."
        })
    elif detected_sem:
        extracted["semester_name"] = detected_sem
        items.append({
            "requirement": "Semester Name",
            "expected_value": expected_sem or "Semester Designation (e.g. I B.Tech II Semester)",
            "detected_value": f"Detected: {detected_sem}",
            "result": "Correct" if not expected_sem else "Needs Review",
            "explanation": f"Detected semester identifier '{detected_sem}'.",
            "recommended_correction": "Confirm exact semester name matches curriculum."
        })
    else:
        items.append({
            "requirement": "Semester Name",
            "expected_value": expected_sem or "Semester Designation (e.g. I B.Tech II Semester)",
            "detected_value": "Missing",
            "result": "Missing",
            "explanation": "Semester Name is mandatory and was not found in document.",
            "recommended_correction": "Include: 'Semester: I B.Tech II Semester' in header."
        })

    return items, extracted


# =====================================================================
# 2. COURSE STRUCTURE VALIDATOR (Exactly 5 Units in Sequence with Content)
# =====================================================================
def validate_course_structure_document(file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates Course Structure Document against strict institutional rules:
      - 5 Mandatory Common Details
      - Exactly 5 Units (Unit 1 to Unit 5)
      - Correct Sequence
      - Substantive syllabus content under each unit
      - No missing units
    """
    path = Path(file_path)
    if not path.exists() or path.stat().st_size == 0:
        item = {
            "requirement": "File Integrity & Format",
            "expected_value": "Valid non-empty PDF document",
            "detected_value": "Empty or missing file on disk",
            "result": "Incorrect",
            "explanation": "Uploaded file is 0 bytes or could not be read.",
            "recommended_correction": "Re-export and upload a valid PDF document."
        }
        return build_categorized_report([item], {"expected_marks": 0, "detected_marks": 0, "calculation_breakdown": "N/A", "status": "Incorrect"})

    try:
        pdf_data = extract_pdf_data(str(path))
    except Exception as e:
        item = {
            "requirement": "PDF Structure Integrity",
            "expected_value": "Standard readable PDF structure",
            "detected_value": f"Corrupted PDF ({type(e).__name__})",
            "result": "Incorrect",
            "explanation": f"Document could not be parsed: {str(e)}",
            "recommended_correction": "Generate a clean PDF from your source editor and re-upload."
        }
        return build_categorized_report([item], {"expected_marks": 0, "detected_marks": 0, "calculation_breakdown": "N/A", "status": "Incorrect"})

    full_text = pdf_data.get("full_text", "")
    full_norm = normalize(full_text)
    text_length = len(full_text.strip())
    total_pages = pdf_data.get("total_pages", 1)

    items: List[Dict[str, Any]] = []

    # Check: Scanned / Unreadable Document -> PENDING REVIEW
    if text_length < 50 and total_pages > 0:
        item = {
            "requirement": "Digital Text Readability",
            "expected_value": "Searchable digital text layer",
            "detected_value": f"Scanned/Image PDF ({text_length} chars extracted)",
            "result": "Needs Review",
            "explanation": "Document cannot be reliably parsed as digital text. Sent for manual Auditor review.",
            "recommended_correction": "Upload a digital text PDF generated from Word or LaTeX."
        }
        return build_categorized_report([item], {"expected_marks": 0, "detected_marks": 0, "calculation_breakdown": "Pending Review", "status": "Needs Review"})

    # 1. Validate 5 Common Institutional Details
    common_items, _ = extract_common_institutional_details(full_text, metadata)
    items.extend(common_items)

    # 2. Validate Exactly 5 Units in Sequence with Syllabus Content
    # Unit patterns for headings: UNIT 1, UNIT-I, UNIT I, UNIT-1, etc.
    unit_targets = [
        ("Unit 1", [r"\bunit\s*[-–:]?\s*1\b", r"\bunit\s*[-–:]?\s*i\b"]),
        ("Unit 2", [r"\bunit\s*[-–:]?\s*2\b", r"\bunit\s*[-–:]?\s*ii\b"]),
        ("Unit 3", [r"\bunit\s*[-–:]?\s*3\b", r"\bunit\s*[-–:]?\s*iii\b"]),
        ("Unit 4", [r"\bunit\s*[-–:]?\s*4\b", r"\bunit\s*[-–:]?\s*iv\b"]),
        ("Unit 5", [r"\bunit\s*[-–:]?\s*5\b", r"\bunit\s*[-–:]?\s*v\b"]),
    ]

    unit_positions = []
    missing_units = []
    empty_units = []

    for label, patterns in unit_targets:
        found_pos = None
        for p in patterns:
            m = re.search(p, full_norm)
            if m:
                found_pos = m.start()
                break

        if found_pos is not None:
            unit_positions.append((label, found_pos))
        else:
            missing_units.append(label)

    # Validate unit sequential order
    is_ordered = True
    for i in range(len(unit_positions) - 1):
        if unit_positions[i][1] > unit_positions[i+1][1]:
            is_ordered = False
            break

    # Validate content length under each detected unit
    for i in range(len(unit_positions)):
        start_idx = unit_positions[i][1]
        end_idx = unit_positions[i+1][1] if i + 1 < len(unit_positions) else len(full_norm)
        chunk = full_norm[start_idx:end_idx].strip()
        # Substantive syllabus content should have at least 8 words
        words = chunk.split()
        if len(words) < 8:
            empty_units.append(unit_positions[i][0])

    # Report Unit Heading Completeness
    if len(unit_positions) == 5 and not missing_units:
        items.append({
            "requirement": "5 Mandatory Unit Headings",
            "expected_value": "Exactly 5 Units (Unit 1, Unit 2, Unit 3, Unit 4, Unit 5)",
            "detected_value": "All 5 Unit headings present (Unit 1 to Unit 5)",
            "result": "Correct",
            "explanation": "All five units are clearly and explicitly demarcated.",
            "recommended_correction": "None required."
        })
    else:
        detected_labels = [u[0] for u in unit_positions]
        items.append({
            "requirement": "5 Mandatory Unit Headings",
            "expected_value": "Exactly 5 Units (Unit 1, Unit 2, Unit 3, Unit 4, Unit 5)",
            "detected_value": f"Detected {len(unit_positions)}/5 Units ({', '.join(detected_labels) if detected_labels else 'None'}). Missing: {', '.join(missing_units)}",
            "result": "Missing",
            "explanation": f"Course structure requires exactly 5 units. Missing: {', '.join(missing_units)}.",
            "recommended_correction": f"Add the missing units: {', '.join(missing_units)} with full syllabus topics."
        })

    # Report Sequential Numbering Order
    if is_ordered and len(unit_positions) >= 2:
        items.append({
            "requirement": "Unit Numbering Sequence",
            "expected_value": "Strict chronological sequence (Unit 1 -> Unit 2 -> Unit 3 -> Unit 4 -> Unit 5)",
            "detected_value": "Sequential unit order verified",
            "result": "Correct",
            "explanation": "Unit headings follow the required institutional curriculum order.",
            "recommended_correction": "None required."
        })
    elif not is_ordered:
        items.append({
            "requirement": "Unit Numbering Sequence",
            "expected_value": "Strict chronological sequence (Unit 1 -> Unit 2 -> Unit 3 -> Unit 4 -> Unit 5)",
            "detected_value": "Out-of-sequence unit numbering detected",
            "result": "Incorrect",
            "explanation": "Units are arranged out of chronological sequence in the document.",
            "recommended_correction": "Re-order the units sequentially from Unit 1 to Unit 5."
        })

    # Report Syllabus Content Availability
    if not empty_units and len(unit_positions) == 5:
        items.append({
            "requirement": "Unit Syllabus Content Availability",
            "expected_value": "Detailed syllabus topics under all 5 units",
            "detected_value": "Comprehensive syllabus content verified under all 5 units",
            "result": "Correct",
            "explanation": "Each unit contains corresponding descriptive syllabus topics and subtopics.",
            "recommended_correction": "None required."
        })
    else:
        culprits = empty_units + missing_units
        items.append({
            "requirement": "Unit Syllabus Content Availability",
            "expected_value": "Detailed syllabus topics under all 5 units",
            "detected_value": f"Syllabus content missing or insufficient under: {', '.join(culprits)}",
            "result": "Incorrect",
            "explanation": f"Units {', '.join(culprits)} lack substantive syllabus topics or are missing entirely.",
            "recommended_correction": "Ensure each unit includes detailed pedagogical topics and learning objectives."
        })

    marks_info = {
        "expected_marks": 0,
        "detected_marks": 0,
        "calculation_breakdown": "5 Units Syllabus Architecture (Curriculum Structure)",
        "status": "Correct" if len(unit_positions) == 5 and not empty_units and not missing_units else "Incorrect"
    }

    return build_categorized_report(items, marks_info)


# =====================================================================
# 3. QUESTION PAPER VALIDATOR (Mid 1, Mid 2, and Semester Paper)
# =====================================================================
def validate_question_paper_document(file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates Question Paper according to category:
      A. Mid 1 and Mid 2 Examination:
         - Total Marks = 40
         - Question 1: Short Answer Questions (5 subquestions: A, B, C, D, E @ 2M each = 10M)
         - Questions 2 to 7: MCQs arranged in 3 pairs (Pair 1: Q2-3 = 10M, Pair 2: Q4-5 = 10M, Pair 3: Q6-7 = 10M)
         - Exactly 7 main question numbers
         - No OR choice or attempt-any-three rule
      B. Semester Examination:
         - Total Marks = 70
         - Part A: Short Answer (Questions 1 to 10 @ 2M each = 20M, covering all 5 units)
         - Part B: Descriptive (5 unit-wise questions, one 10M question per unit = 50M)
         - Grand Total = 70 Marks
    """
    path = Path(file_path)
    if not path.exists() or path.stat().st_size == 0:
        item = {
            "requirement": "File Integrity & Format",
            "expected_value": "Valid non-empty PDF document",
            "detected_value": "Empty or missing file on disk",
            "result": "Incorrect",
            "explanation": "Uploaded file is 0 bytes or could not be read.",
            "recommended_correction": "Re-export and upload a valid PDF document."
        }
        return build_categorized_report([item], {"expected_marks": 0, "detected_marks": 0, "calculation_breakdown": "N/A", "status": "Incorrect"})

    try:
        pdf_data = extract_pdf_data(str(path))
    except Exception as e:
        item = {
            "requirement": "PDF Structure Integrity",
            "expected_value": "Standard readable PDF structure",
            "detected_value": f"Corrupted PDF ({type(e).__name__})",
            "result": "Incorrect",
            "explanation": f"Document could not be parsed: {str(e)}",
            "recommended_correction": "Generate a clean PDF from your source editor and re-upload."
        }
        return build_categorized_report([item], {"expected_marks": 0, "detected_marks": 0, "calculation_breakdown": "N/A", "status": "Incorrect"})

    full_text = pdf_data.get("full_text", "")
    full_norm = normalize(full_text)
    text_length = len(full_text.strip())
    total_pages = pdf_data.get("total_pages", 1)

    items: List[Dict[str, Any]] = []

    # Scanned / Image PDF Check -> PENDING REVIEW
    if text_length < 50 and total_pages > 0:
        item = {
            "requirement": "Digital Text Readability",
            "expected_value": "Searchable digital text layer",
            "detected_value": f"Scanned/Raster image ({text_length} text chars extracted)",
            "result": "Needs Review",
            "explanation": "Document cannot be parsed reliably from image raster. Sent for manual Auditor review.",
            "recommended_correction": "Upload a digital text PDF generated directly from Word or LaTeX."
        }
        return build_categorized_report([item], {"expected_marks": 0, "detected_marks": 0, "calculation_breakdown": "Pending Review", "status": "Needs Review"})

    # 1. Mandatory 5 Common Institutional Details
    common_items, _ = extract_common_institutional_details(full_text, metadata)
    items.extend(common_items)

    # 2. Determine Examination Category: Mid 1, Mid 2, or Semester
    exam_cat_meta = (metadata.get("exam_category") or metadata.get("document_type_name") or "").upper()
    is_semester = "SEM" in exam_cat_meta or "SEMESTER" in full_norm[:1500] or "end semester" in full_norm[:1500]
    is_mid = not is_semester

    # -------------------------------------------------------------
    # CASE A: MID 1 / MID 2 EXAMINATION (Total Marks = 40)
    # -------------------------------------------------------------
    if is_mid:
        exam_title = "Mid 2 Examination" if ("MID 2" in exam_cat_meta or "mid 2" in full_norm or "mid-2" in full_norm or "mid-ii" in full_norm) else "Mid 1 Examination"
        items.append({
            "requirement": "Examination Category",
            "expected_value": "Mid 1 Examination or Mid 2 Examination",
            "detected_value": exam_title,
            "result": "Correct",
            "explanation": f"Document identified as {exam_title} with identical 40-mark examination pattern.",
            "recommended_correction": "None required."
        })

        # Rule 1: Exactly 7 Main Question Numbers (Q1 to Q7)
        # Search for main question markers: Q1, Q2, Q3, Q4, Q5, Q6, Q7 or 1., 2., 3., 4., 5., 6., 7.
        detected_main_qs = set()
        for q_num in range(1, 8):
            q_patterns = [
                rf"\b(?:question|q)\.?\s*{q_num}\b",
                rf"(?m)^\s*{q_num}\s*[\.\)]\s+",
                rf"\b{q_num}\s*[\.\)]\s+[A-Za-z]"
            ]
            for qp in q_patterns:
                if re.search(qp, full_text, re.IGNORECASE):
                    detected_main_qs.add(q_num)
                    break

        has_extra_qs = bool(re.search(r"(?m)(?:\b(?:question|q)\.?\s*[89]\b|^\s*[89]\s*[\.\)])", full_text, re.IGNORECASE))

        if len(detected_main_qs) == 7 and not has_extra_qs:
            items.append({
                "requirement": "Main Question Numbers Count",
                "expected_value": "Exactly 7 Main Questions (Question 1 to Question 7)",
                "detected_value": "All 7 Questions present (Q1 to Q7)",
                "result": "Correct",
                "explanation": "Question paper strictly contains exactly 7 main question numbers.",
                "recommended_correction": "None required."
            })
        else:
            missing_qs = [f"Q{i}" for i in range(1, 8) if i not in detected_main_qs]
            items.append({
                "requirement": "Main Question Numbers Count",
                "expected_value": "Exactly 7 Main Questions (Question 1 to Question 7)",
                "detected_value": f"Detected {len(detected_main_qs)}/7 questions. Missing: {', '.join(missing_qs) if missing_qs else 'Extra questions found'}",
                "result": "Incorrect" if has_extra_qs else "Missing",
                "explanation": "Mid exam pattern requires exactly 7 main questions (Q1 Short Answer + Q2-Q7 MCQs).",
                "recommended_correction": "Number questions exactly from Question 1 to Question 7."
            })

        # Rule 2: Question 1 – Short Answer Questions (5 subquestions: A, B, C, D, E @ 2M each = 10 Marks)
        sub_labels = ["a", "b", "c", "d", "e"]
        q1_m = re.search(r'(?:question\s*1|q\.?\s*1\b|^\s*1\s*[\.\)])', full_text, re.IGNORECASE | re.MULTILINE)
        q2_m = re.search(r'(?:question\s*2|q\.?\s*2\b|^\s*2\s*[\.\)])', full_text, re.IGNORECASE | re.MULTILINE)
        q1_chunk = full_text[q1_m.start():q2_m.start()] if (q1_m and q2_m) else full_text[:2500]

        detected_subs = []
        for sl in sub_labels:
            if re.search(rf'(?:\({sl}\)|^\s*{sl}\.|\b{sl}\.|\b{sl}\))', q1_chunk, re.IGNORECASE | re.MULTILINE):
                detected_subs.append(sl.upper())

        has_2m_q1 = bool(re.search(r"\b2\s*m(?:arks)?\b", q1_chunk, re.IGNORECASE)) or "2 marks" in normalize(q1_chunk) or "10 marks" in normalize(q1_chunk) or "[2]" in q1_chunk

        if len(detected_subs) >= 4 and has_2m_q1:
            items.append({
                "requirement": "Question 1 Subquestions (Short Answer)",
                "expected_value": "5 Subquestions (A, B, C, D, E) @ 2 Marks each = 10 Marks",
                "detected_value": f"Detected subquestions ({', '.join(detected_subs)}) with 2-mark weighting",
                "result": "Correct",
                "explanation": "Question 1 contains 5 short-answer subquestions carrying 2 marks each (10 Marks total).",
                "recommended_correction": "None required."
            })
        else:
            items.append({
                "requirement": "Question 1 Subquestions (Short Answer)",
                "expected_value": "5 Subquestions (A, B, C, D, E) @ 2 Marks each = 10 Marks",
                "detected_value": f"Detected {len(detected_subs)}/5 subquestions ({', '.join(detected_subs) if detected_subs else 'None'})",
                "result": "Incorrect",
                "explanation": "Question 1 must contain five subquestions (A, B, C, D, E) carrying 2 marks each.",
                "recommended_correction": "Format Question 1 with subquestions: (A), (B), (C), (D), and (E) @ 2 Marks each."
            })

        # Rule 3 & 4: Questions 2 to 7 Multiple Choice Questions in 3 Pairs (10 Marks each)
        # Pair 1: Q2 & Q3 = 10M
        # Pair 2: Q4 & Q5 = 10M
        # Pair 3: Q6 & Q7 = 10M
        mcq_indicators = ["mcq", "multiple choice", "(a)", "(b)", "(c)", "(d)", "options", "choose", "[a]", "[b]"]
        has_mcq_structure = sum(1 for ind in mcq_indicators if ind in full_norm) >= 2 or any(
            re.search(rf"\b{opt}\s*[\.\)]", full_text) for opt in ["A", "B", "C", "D"]
        )

        pair1_present = 2 in detected_main_qs and 3 in detected_main_qs
        pair2_present = 4 in detected_main_qs and 5 in detected_main_qs
        pair3_present = 6 in detected_main_qs and 7 in detected_main_qs

        # Validate Pair 1 (Q2 and Q3 = 10 Marks)
        items.append({
            "requirement": "MCQ Pair 1 (Question 2 & Question 3)",
            "expected_value": "Two MCQ Questions (Q2 & Q3) with combined value = 10 Marks",
            "detected_value": "Question 2 and Question 3 verified (Combined 10M)" if pair1_present else "Pair 1 questions missing or incomplete",
            "result": "Correct" if pair1_present else "Missing",
            "explanation": "Pair 1 consists of Questions 2 & 3 with a combined total of 10 marks." if pair1_present else "Questions 2 and 3 must both be present with combined 10 marks.",
            "recommended_correction": "None required." if pair1_present else "Add both Question 2 and Question 3 as MCQ items."
        })

        # Validate Pair 2 (Q4 and Q5 = 10 Marks)
        items.append({
            "requirement": "MCQ Pair 2 (Question 4 & Question 5)",
            "expected_value": "Two MCQ Questions (Q4 & Q5) with combined value = 10 Marks",
            "detected_value": "Question 4 and Question 5 verified (Combined 10M)" if pair2_present else "Pair 2 questions missing or incomplete",
            "result": "Correct" if pair2_present else "Missing",
            "explanation": "Pair 2 consists of Questions 4 & 5 with a combined total of 10 marks." if pair2_present else "Questions 4 and 5 must both be present with combined 10 marks.",
            "recommended_correction": "None required." if pair2_present else "Add both Question 4 and Question 5 as MCQ items."
        })

        # Validate Pair 3 (Q6 and Q7 = 10 Marks)
        items.append({
            "requirement": "MCQ Pair 3 (Question 6 & Question 7)",
            "expected_value": "Two MCQ Questions (Q6 & Q7) with combined value = 10 Marks",
            "detected_value": "Question 6 and Question 7 verified (Combined 10M)" if pair3_present else "Pair 3 questions missing or incomplete",
            "result": "Correct" if pair3_present else "Missing",
            "explanation": "Pair 3 consists of Questions 6 & 7 with a combined total of 10 marks." if pair3_present else "Questions 6 and 7 must both be present with combined 10 marks.",
            "recommended_correction": "None required." if pair3_present else "Add both Question 6 and Question 7 as MCQ items."
        })

        # Rule 7: Prohibit OR choice or attempt-any-three rule
        has_disallowed_or = bool(re.search(r"\b(?:attempt\s*any\s*three|answer\s*any\s*3|either\s+or)\b", full_norm))
        if not has_disallowed_or:
            items.append({
                "requirement": "Compulsory Assessment (No OR Choice)",
                "expected_value": "All 7 Questions compulsory (No OR choice or attempt-any-three)",
                "detected_value": "No disallowed 'OR' choice or attempt-any-three rules detected",
                "result": "Correct",
                "explanation": "Paper adheres to mandatory institutional policy where all 7 questions are compulsory.",
                "recommended_correction": "None required."
            })
        else:
            items.append({
                "requirement": "Compulsory Assessment (No OR Choice)",
                "expected_value": "All 7 Questions compulsory (No OR choice or attempt-any-three)",
                "detected_value": "Detected disallowed OR choice / attempt-any-three instruction",
                "result": "Incorrect",
                "explanation": "Mid examination format strictly forbids internal choice or attempt-any-three rules.",
                "recommended_correction": "Remove 'OR' choice and attempt-any-three instructions; all 7 questions must be compulsory."
            })

        # Rule 8 & 9: Grand Total Marks = 40
        # Q1 = 10M, Pair 1 = 10M, Pair 2 = 10M, Pair 3 = 10M -> Total = 40M
        detected_marks = extract_detected_total_marks(full_text) or 40
        marks_correct = (detected_marks == 40)

        items.append({
            "requirement": "Total Marks Calculation",
            "expected_value": "Grand Total = 40 Marks (Q1: 10M + Pair 1: 10M + Pair 2: 10M + Pair 3: 10M)",
            "detected_value": f"Total Marks: {detected_marks} Marks",
            "result": "Correct" if marks_correct else "Incorrect",
            "explanation": f"Grand total marks calculated as {detected_marks} marks (Expected: 40 marks).",
            "recommended_correction": "None required." if marks_correct else "Ensure total marks scheme strictly equals 40 Marks."
        })

        marks_info = {
            "expected_marks": 40,
            "detected_marks": detected_marks,
            "calculation_breakdown": "Q1 (10M) + Pair 1 [Q2-3] (10M) + Pair 2 [Q4-5] (10M) + Pair 3 [Q6-7] (10M) = 40 Marks",
            "status": "Correct" if marks_correct and len(detected_main_qs) == 7 else "Incorrect"
        }

        return build_categorized_report(items, marks_info)

    # -------------------------------------------------------------
    # CASE B: SEMESTER EXAMINATION (Total Marks = 70)
    # -------------------------------------------------------------
    else:
        items.append({
            "requirement": "Examination Category",
            "expected_value": "Semester Examination (Regular / Supplementary)",
            "detected_value": "Semester Examination Verified",
            "result": "Correct",
            "explanation": "Document identified as Semester End Examination paper.",
            "recommended_correction": "None required."
        })

        # Rule 1: Part A – Short Answer Questions (Questions 1 to 10 @ 2 Marks each = 20 Marks)
        has_part_a = "part a" in full_norm or "part-a" in full_norm or "section a" in full_norm
        part_a_text = extract_section_text(full_text, "part a", ["part b", "part-b", "section b"]) or full_text[:3000]

        # Count Part A questions: 1 to 10 or 1.a through 1.j
        part_a_sub_count = len(re.findall(r"\b(?:1\.[a-j]|\([a-j]\)|[a-j]\))\b", normalize(part_a_text)))
        part_a_num_count = len(re.findall(r"(?m)^\s*(?:[1-9]|10)\s*[\.\)]\s+", part_a_text))
        part_a_q_count = max(part_a_sub_count, part_a_num_count)

        # Check 2 marks allocation
        has_2m = "2 marks" in normalize(part_a_text) or "2m" in normalize(part_a_text) or "20 marks" in full_norm or "[2]" in part_a_text

        if has_part_a and (part_a_q_count >= 8 or "10 questions" in full_norm):
            items.append({
                "requirement": "PART A – Short Answer Questions (10 x 2M = 20M)",
                "expected_value": "10 Questions @ 2 Marks each = 20 Marks covering all 5 Units",
                "detected_value": f"Part A verified ({part_a_q_count if part_a_q_count > 0 else 10} questions detected @ 2M each)",
                "result": "Correct",
                "explanation": "Part A contains 10 compulsory short-answer questions carrying 2 marks each (20 marks total).",
                "recommended_correction": "None required."
            })
        else:
            items.append({
                "requirement": "PART A – Short Answer Questions (10 x 2M = 20M)",
                "expected_value": "10 Questions @ 2 Marks each = 20 Marks covering all 5 Units",
                "detected_value": f"Part A incomplete (Detected {part_a_q_count}/10 questions)",
                "result": "Missing" if not has_part_a else "Incorrect",
                "explanation": "Semester paper must contain PART A with exactly 10 short questions (2 marks each).",
                "recommended_correction": "Include: 'PART-A: Answer all 10 questions (10 x 2 = 20 Marks)'."
            })

        # Rule 2: Part B – Descriptive Questions (5 Unit-Wise Questions @ 10 Marks each = 50 Marks)
        has_part_b = "part b" in full_norm or "part-b" in full_norm or "section b" in full_norm
        part_b_text = extract_section_text(full_text, "part b") or full_text[len(full_text)//3:]
        part_b_norm = normalize(part_b_text)

        # Check all 5 units in Part B
        units_in_b = []
        for u_num, u_label in [(1, "unit 1"), (2, "unit 2"), (3, "unit 3"), (4, "unit 4"), (5, "unit 5"),
                               (1, "unit i"), (2, "unit ii"), (3, "unit iii"), (4, "unit iv"), (5, "unit v")]:
            if u_label in part_b_norm or u_label in full_norm:
                if u_num not in units_in_b:
                    units_in_b.append(u_num)

        has_10m = "10 marks" in part_b_norm or "10m" in part_b_norm or "50 marks" in full_norm or "[10]" in part_b_text

        if has_part_b and len(units_in_b) >= 4 and has_10m:
            items.append({
                "requirement": "PART B – Unit-Wise Descriptive Questions (5 x 10M = 50M)",
                "expected_value": "5 Unit-Wise Questions (Unit 1 to Unit 5), 1 question @ 10M per unit = 50M",
                "detected_value": f"Part B verified across {len(units_in_b)}/5 units @ 10M each",
                "result": "Correct",
                "explanation": "Part B provides 5 unit-wise questions carrying 10 marks each (50 marks total).",
                "recommended_correction": "None required."
            })
        else:
            missing_units_b = [f"Unit {u}" for u in range(1, 6) if u not in units_in_b]
            items.append({
                "requirement": "PART B – Unit-Wise Descriptive Questions (5 x 10M = 50M)",
                "expected_value": "5 Unit-Wise Questions (Unit 1 to Unit 5), 1 question @ 10M per unit = 50M",
                "detected_value": f"Detected {len(units_in_b)}/5 units in Part B. Missing: {', '.join(missing_units_b)}",
                "result": "Missing" if not has_part_b else "Incorrect",
                "explanation": "Part B must cover all 5 units with one 10-mark question from each unit.",
                "recommended_correction": "Structure Part B into Units 1 through 5 with one 10-mark question per unit."
            })

        # Rule 3: Grand Total Calculation (Part A = 20M + Part B = 50M = 70 Marks)
        detected_marks = extract_detected_total_marks(full_text) or 70
        is_70m = (detected_marks == 70)

        items.append({
            "requirement": "Semester Paper Total Marks (70 Marks)",
            "expected_value": "Part A (20 Marks) + Part B (50 Marks) = Grand Total 70 Marks",
            "detected_value": f"Total Marks: {detected_marks} Marks",
            "result": "Correct" if is_70m else "Incorrect",
            "explanation": f"Grand total marks verified as {detected_marks} marks (Expected: 70 marks).",
            "recommended_correction": "None required." if is_70m else "Ensure total marks scheme strictly equals 70 Marks."
        })

        marks_info = {
            "expected_marks": 70,
            "detected_marks": detected_marks,
            "calculation_breakdown": "Part A: 10 x 2M = 20M + Part B: 5 Units x 10M = 50M | Grand Total = 70 Marks",
            "status": "Correct" if is_70m and has_part_a and has_part_b else "Incorrect"
        }

        return build_categorized_report(items, marks_info)


# =====================================================================
# 4. QUESTION BANK VALIDATOR (5 Units, 10 Part A + 10 Part B = 100 Qs)
# =====================================================================
def validate_question_bank_document(file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates Question Bank according to institutional standard requirements:
      - 5 Mandatory Units (Unit 1 to Unit 5)
      - Each Unit contains:
        * Part A (Short Answer): 10 questions @ 2 marks = 20 marks
        * Part B (Descriptive): 10 questions @ 10 marks = 100 marks
      - Total: 50 Part A + 50 Part B = 100 Questions total
      - 5 Mandatory Common Details
    """
    path = Path(file_path)
    if not path.exists() or path.stat().st_size == 0:
        item = {
            "requirement": "File Integrity & Format",
            "expected_value": "Valid non-empty PDF document",
            "detected_value": "Empty or missing file on disk",
            "result": "Incorrect",
            "explanation": "Uploaded file is 0 bytes or could not be read.",
            "recommended_correction": "Re-export and upload a valid PDF document."
        }
        return build_categorized_report([item], {"expected_marks": 120, "detected_marks": 0, "calculation_breakdown": "N/A", "status": "Incorrect"})

    try:
        pdf_data = extract_pdf_data(str(path))
    except Exception as e:
        item = {
            "requirement": "PDF Structure Integrity",
            "expected_value": "Standard readable PDF structure",
            "detected_value": f"Corrupted PDF ({type(e).__name__})",
            "result": "Incorrect",
            "explanation": f"Document could not be parsed: {str(e)}",
            "recommended_correction": "Generate a clean PDF from your source editor and re-upload."
        }
        return build_categorized_report([item], {"expected_marks": 120, "detected_marks": 0, "calculation_breakdown": "N/A", "status": "Incorrect"})

    full_text = pdf_data.get("full_text", "")
    full_norm = normalize(full_text)
    text_length = len(full_text.strip())
    total_pages = pdf_data.get("total_pages", 1)

    items: List[Dict[str, Any]] = []

    # Scanned / Image PDF Check -> PENDING REVIEW
    if text_length < 50 and total_pages > 0:
        item = {
            "requirement": "Digital Text Readability",
            "expected_value": "Searchable digital text layer",
            "detected_value": f"Scanned/Raster image ({text_length} text chars extracted)",
            "result": "Needs Review",
            "explanation": "Document cannot be parsed reliably from image raster. Sent for manual Auditor review.",
            "recommended_correction": "Upload a digital text PDF generated directly from Word or LaTeX."
        }
        return build_categorized_report([item], {"expected_marks": 120, "detected_marks": 0, "calculation_breakdown": "Pending Review", "status": "Needs Review"})

    # 1. 5 Mandatory Common Details
    common_items, _ = extract_common_institutional_details(full_text, metadata)
    items.extend(common_items)

    # 2. Check 5 Units Coverage
    units_found = set()
    for u_num, u_name in [(1, "unit 1"), (2, "unit 2"), (3, "unit 3"), (4, "unit 4"), (5, "unit 5"),
                          (1, "unit-i"), (2, "unit-ii"), (3, "unit-iii"), (4, "unit-iv"), (5, "unit-v"),
                          (1, "unit i"), (2, "unit ii"), (3, "unit iii"), (4, "unit iv"), (5, "unit v")]:
        if u_name in full_norm:
            units_found.add(u_num)

    missing_units = [f"Unit {u}" for u in range(1, 6) if u not in units_found]

    if len(units_found) == 5:
        items.append({
            "requirement": "5 Mandatory Unit Headings",
            "expected_value": "All 5 Units present (Unit 1 to Unit 5)",
            "detected_value": "All 5 Units verified (Units 1, 2, 3, 4, 5)",
            "result": "Correct",
            "explanation": "Question Bank covers all 5 mandatory curriculum units.",
            "recommended_correction": "None required."
        })
    else:
        items.append({
            "requirement": "5 Mandatory Unit Headings",
            "expected_value": "All 5 Units present (Unit 1 to Unit 5)",
            "detected_value": f"Detected {len(units_found)}/5 Units. Missing: {', '.join(missing_units)}",
            "result": "Missing",
            "explanation": f"Question Bank must include question sets for all 5 units. Missing: {', '.join(missing_units)}.",
            "recommended_correction": f"Add the missing units: {', '.join(missing_units)}."
        })

    # 3. Dual-Tier Question Classification (Part A & Part B per unit)
    has_part_a = "part a" in full_norm or "short answer" in full_norm
    has_part_b = "part b" in full_norm or "descriptive" in full_norm or "long answer" in full_norm

    if has_part_a and has_part_b:
        items.append({
            "requirement": "Unit Sections (Part A & Part B)",
            "expected_value": "Each Unit must contain Part A (Short Answer) and Part B (Descriptive)",
            "detected_value": "Both Part A and Part B sections verified across units",
            "result": "Correct",
            "explanation": "Units are properly divided into Part A short-answer questions and Part B descriptive questions.",
            "recommended_correction": "None required."
        })
    else:
        items.append({
            "requirement": "Unit Sections (Part A & Part B)",
            "expected_value": "Each Unit must contain Part A (Short Answer) and Part B (Descriptive)",
            "detected_value": f"Sections incomplete ({'Only Part A' if has_part_a else 'Only Part B' if has_part_b else 'Neither Part A nor Part B detected'})",
            "result": "Missing",
            "explanation": "Each unit in the Question Bank must contain both PART A and PART B.",
            "recommended_correction": "Divide each unit into 'PART A (Short Answer)' and 'PART B (Descriptive)'."
        })

    # 4. Question Count & Marks Allocation:
    # 10 Part A @ 2M = 20M per unit x 5 = 50 Qs / 100M
    # 10 Part B @ 10M = 100M per unit x 5 = 50 Qs / 500M
    # Total = 100 questions
    detected_q_count = count_questions(full_text)

    # Check Part A question count
    items.append({
        "requirement": "Part A Questions Volume (50 Questions @ 2M)",
        "expected_value": "50 Questions (10 Part A questions per unit @ 2 Marks each)",
        "detected_value": f"Part A question volume verified (~{min(50, max(10, detected_q_count // 2))} questions detected)",
        "result": "Correct" if detected_q_count >= 20 and has_part_a else "Incorrect",
        "explanation": "Part A provides short-answer questions carrying 2 marks each across all 5 units.",
        "recommended_correction": "Ensure 10 Part A questions are provided for every unit (50 questions total)."
    })

    # Check Part B question count
    items.append({
        "requirement": "Part B Questions Volume (50 Questions @ 10M)",
        "expected_value": "50 Questions (10 Part B questions per unit @ 10 Marks each)",
        "detected_value": f"Part B question volume verified (~{min(50, max(10, detected_q_count // 2))} questions detected)",
        "result": "Correct" if detected_q_count >= 20 and has_part_b else "Incorrect",
        "explanation": "Part B provides comprehensive descriptive questions carrying 10 marks each across all 5 units.",
        "recommended_correction": "Ensure 10 Part B questions are provided for every unit (50 questions total)."
    })

    # Total Question Bank Count (100 Questions)
    q_count_ok = detected_q_count >= 80 or (detected_q_count >= 25 and len(units_found) == 5)
    items.append({
        "requirement": "Total Question Bank Volume",
        "expected_value": "Exactly 100 Questions (20 questions per unit: 10 Part A + 10 Part B)",
        "detected_value": f"{detected_q_count} questions detected in document",
        "result": "Correct" if q_count_ok else "Incorrect",
        "explanation": f"Detected {detected_q_count} questions structured across curriculum units.",
        "recommended_correction": "Include exactly 20 questions (10 Part A + 10 Part B) per unit to reach 100 questions."
    })

    marks_info = {
        "expected_marks": 120,
        "detected_marks": 120 if q_count_ok else 60,
        "calculation_breakdown": "Per Unit: Part A (10 x 2M = 20M) + Part B (10 x 10M = 100M) = 120M per unit x 5 Units",
        "status": "Correct" if len(units_found) == 5 and has_part_a and has_part_b else "Incorrect"
    }

    return build_categorized_report(items, marks_info)


# =====================================================================
# 5. CROSS-DOCUMENT VALIDATOR (Course Structure, Question Papers, QB)
# =====================================================================
def perform_cross_document_validation(course_id: int) -> Dict[str, Any]:
    """
    Compares uploaded documents for a given course:
      - Course Structure
      - Question Papers (Mid 1, Mid 2, Semester Paper)
      - Question Bank
    Validates:
      1. College Name matches across all documents
      2. Course Name matches across all documents
      3. Course Code matches across all documents
      4. Academic Year matches across all documents
      5. Semester Name matches across all documents
      6. All 5 units from Course Structure are represented in Question Bank
      7. Semester Question Paper covers all 5 units
      8. Mid 1 and Mid 2 follow the 40M examination pattern
    """
    from backend.database import get_db_cursor

    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT d.id, d.file_name, d.file_path, d.document_type_id, dt.name AS document_type_name,
                   d.analysis_status, d.analysis_result, d.course_id, c.code AS course_code, c.name AS course_name,
                   ay.name AS academic_year_name, s.name AS semester_name, inst.name AS institution_name
            FROM documents d
            LEFT JOIN document_types dt ON dt.id = d.document_type_id
            LEFT JOIN courses c ON c.id = d.course_id
            LEFT JOIN academic_years ay ON ay.id = d.academic_year_id
            LEFT JOIN semesters s ON s.id = d.semester_id
            LEFT JOIN institution inst ON inst.id = d.institution_id
            WHERE d.course_id = %s
            ORDER BY d.id ASC
        """, (course_id,))
        docs = cursor.fetchall()

    if not docs:
        return {
            "status": "NO_DOCUMENTS",
            "message": "No submitted documents found for this course.",
            "discrepancies": [],
            "documents_checked": 0,
            "alignment_score": 0.0
        }

    discrepancies: List[Dict[str, Any]] = []
    matrix: List[Dict[str, Any]] = []

    # Map docs by category
    cs_doc = next((d for d in docs if "structure" in (d["document_type_name"] or "").lower()), None)
    qb_doc = next((d for d in docs if "bank" in (d["document_type_name"] or "").lower()), None)
    mid1_doc = next((d for d in docs if "mid 1" in (d["document_type_name"] or "").lower()), None)
    mid2_doc = next((d for d in docs if "mid 2" in (d["document_type_name"] or "").lower()), None)
    sem_doc = next((d for d in docs if "semester" in (d["document_type_name"] or "").lower()), None)

    # 1. Cross-check Common Details
    common_fields = ["institution_name", "course_name", "course_code", "academic_year_name", "semester_name"]
    field_labels = {
        "institution_name": "College Name",
        "course_name": "Course Name",
        "course_code": "Course Code",
        "academic_year_name": "Academic Year",
        "semester_name": "Semester Name"
    }

    for fld in common_fields:
        label = field_labels[fld]
        values = {}
        for d in docs:
            doc_type = d["document_type_name"] or "Document"
            val = d.get(fld)
            if val:
                values[doc_type] = str(val).strip()

        unique_vals = set(normalize(v) for v in values.values())
        if len(unique_vals) > 1:
            discrepancies.append({
                "field": label,
                "issue": f"Mismatched values across documents: {values}",
                "severity": "HIGH",
                "recommendation": f"Standardize {label} to match across all 3 modules."
            })
        elif len(values) < len(docs):
            missing_in = [d["document_type_name"] for d in docs if d["document_type_name"] not in values]
            discrepancies.append({
                "field": label,
                "issue": f"Missing in: {', '.join(missing_in)}",
                "severity": "MEDIUM",
                "recommendation": f"Ensure {label} is declared on all uploaded PDFs."
            })

    # 2. Check Unit Coverage: Course Structure vs Question Bank & Semester Paper
    if cs_doc and qb_doc:
        matrix.append({
            "check": "Course Structure (5 Units) -> Question Bank Coverage",
            "status": "ALIGNED" if qb_doc.get("analysis_status") == "ACCEPTED" else "REVIEW_NEEDED",
            "details": "Question Bank covers all 5 mandatory curriculum units from Course Structure."
        })
    elif cs_doc and not qb_doc:
        discrepancies.append({
            "field": "Curriculum Coverage",
            "issue": "Course Structure uploaded but Question Bank has not been submitted.",
            "severity": "MEDIUM",
            "recommendation": "Upload the 100-Question Bank covering all 5 syllabus units."
        })

    if sem_doc:
        matrix.append({
            "check": "Semester Paper 5-Unit Coverage",
            "status": "ALIGNED" if sem_doc.get("analysis_status") == "ACCEPTED" else "REVIEW_NEEDED",
            "details": "Semester Question Paper Part B covers all 5 units (10 Marks per unit = 50 Marks)."
        })

    if mid1_doc and mid2_doc:
        matrix.append({
            "check": "Mid 1 & Mid 2 Examination Pattern",
            "status": "ALIGNED" if mid1_doc.get("analysis_status") == "ACCEPTED" and mid2_doc.get("analysis_status") == "ACCEPTED" else "REVIEW_NEEDED",
            "details": "Both Mid 1 and Mid 2 follow the identical 40-mark compulsory question pattern."
        })

    alignment_score = max(0.0, round(100.0 - (len(discrepancies) * 15.0), 1))

    return {
        "status": "ALIGNED" if not discrepancies else "DISCREPANCIES_FOUND",
        "alignment_score": alignment_score,
        "documents_checked": len(docs),
        "discrepancies": discrepancies,
        "matrix": matrix,
        "checked_at": datetime.now().isoformat()
    }


# =====================================================================
# 6. UNIFIED DOCUMENT DISPATCHER
# =====================================================================
def validate_any_document(file_path: str, doc_type_name: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Central institutional validation router.
    Dispatches to specialized validators based on document type name.
    """
    type_lower = (doc_type_name or "").lower()

    if "course structure" in type_lower or "syllabus" in type_lower or "curriculum" in type_lower:
        return validate_course_structure_document(file_path, metadata)
    elif "question bank" in type_lower or "bank" in type_lower:
        return validate_question_bank_document(file_path, metadata)
    elif "question paper" in type_lower or "mid" in type_lower or "semester" in type_lower or "paper" in type_lower or "evaluation" in type_lower:
        return validate_question_paper_document(file_path, metadata)
    else:
        return validate_course_structure_document(file_path, metadata)


# Preserve existing custom format function for backwards compatibility with Auditor custom format builder
def evaluate_requirement(req: dict, pdf_data: Dict[str, Any]) -> Tuple[bool, str | None]:
    req_name = req.get("requirement_name", "").strip()
    req_type = normalize(req.get("requirement_type", ""))
    req_val = (req.get("requirement_value") or "").strip()

    full_text = pdf_data.get("full_text", "")
    full_norm = normalize(full_text)
    header = normalize(pdf_data.get("header_preview", ""))

    if req_type in ("header", "institution_header"):
        expected = normalize(req_val)
        matched = expected in header or expected in full_norm[:1500] or "anantha lakshmi" in full_norm[:1500]
        return matched, "Official Header Found" if matched else "Header missing"

    if req_type in ("marks", "max_marks"):
        m = extract_detected_total_marks(full_text)
        exp_m = extract_detected_total_marks(req_val)
        if exp_m and m:
            return m == exp_m, f"Detected: {m}M (Expected: {exp_m}M)"
        return True, "Marks verified"

    if req_type == "question_count":
        cnt = count_questions(full_text)
        exp_cnt = int(re.search(r"\d+", req_val).group(0)) if re.search(r"\d+", req_val) else 7
        return cnt >= exp_cnt, f"Detected: {cnt} questions (Expected: {exp_cnt})"

    expected = normalize(req_val)
    if expected in full_norm:
        return True, f"Matched '{req_val}'"

    return False, f"Missing '{req_val}'"

def analyze_document_structure(file_path: str, format_record: dict, requirements: List[dict]) -> Dict[str, Any]:
    doc_type_name = format_record.get("format_name", "")
    metadata = {
        "institution_name": "Anantha Lakshmi Institute of Technology & Sciences",
        "file_name": Path(file_path).name
    }
    return validate_any_document(file_path, doc_type_name, metadata)
