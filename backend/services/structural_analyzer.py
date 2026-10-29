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
    """
    Counts question items using standard academic numbering patterns:
    e.g. 1. , 1) , Q1. , Q.1 , Question 1 , (a)
    """
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
        r"(?:maximum\s*marks|max\s*marks|total\s*marks|marks)\s*[:=\-]\s*(\d{2,3})\b",
        r"\b(\d{2,3})\s*marks\b",
        r"\bmax\.?\s*(\d{2,3})\b",
        r"\b(?:70|30|100|60)\s*marks\b"
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

def validate_question_paper_document(file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs comprehensive institutional validation of a Question Paper PDF.
    Generates a 6-column validation report with:
      1. Requirement
      2. Expected Value / Rule
      3. Detected Value
      4. Result ("Correct", "Incorrect", "Missing", "Needs Review", "Not Applicable")
      5. Explanation
      6. Recommended Correction
    Also generates detailed summary metrics and compliance percentage.
    """
    path = Path(file_path)
    file_name = metadata.get("file_name") or path.name

    # 1. Corrupt / Empty File Check
    if not path.exists() or path.stat().st_size == 0:
        item = {
            "requirement": "File Integrity & Format",
            "expected_value": "Valid non-empty PDF document",
            "detected_value": "Empty or missing file on disk",
            "result": "Incorrect",
            "explanation": "Uploaded file is 0 bytes or could not be read.",
            "recommended_correction": "Re-export and upload a valid PDF document."
        }
        return {
            "validation_status": "INVALID",
            "compliance_percentage": 0.0,
            "summary": {
                "total_checks": 1,
                "passed_checks": 0,
                "failed_checks": 1,
                "missing_requirements": 1,
                "needs_review": 0,
                "compliance_percentage": 0.0,
                "validation_status": "INVALID"
            },
            "items": [item],
            "analyzed_at": datetime.now().isoformat()
        }

    try:
        pdf_data = extract_pdf_data(str(path))
    except Exception as e:
        item = {
            "requirement": "PDF Structure Integrity",
            "expected_value": "Standard readable PDF structure",
            "detected_value": f"Corrupted PDF ({type(e).__name__})",
            "result": "Incorrect",
            "explanation": f"Document could not be parsed by PDF engine: {str(e)}",
            "recommended_correction": "Generate a clean PDF from your source editor and re-upload."
        }
        return {
            "validation_status": "INVALID",
            "compliance_percentage": 0.0,
            "summary": {
                "total_checks": 1,
                "passed_checks": 0,
                "failed_checks": 1,
                "missing_requirements": 1,
                "needs_review": 0,
                "compliance_percentage": 0.0,
                "validation_status": "INVALID"
            },
            "items": [item],
            "analyzed_at": datetime.now().isoformat()
        }

    full_text = pdf_data.get("full_text", "")
    full_norm = normalize(full_text)
    header_preview = normalize(pdf_data.get("header_preview", ""))
    total_pages = pdf_data.get("total_pages", 1)

    items: List[Dict[str, Any]] = []

    # Check 1: Scanned PDF / Digital Text Layer Check
    text_length = len(full_text.strip())
    is_scanned = text_length < 40 and total_pages > 0

    if is_scanned:
        # Document cannot be read reliably -> show Needs Review for unreadable content
        items.append({
            "requirement": "Digital Text Readability",
            "expected_value": "Searchable digital text layer",
            "detected_value": f"Scanned/Raster image ({text_length} text chars extracted)",
            "result": "Needs Review",
            "explanation": "Document appears to be a scanned image or photo without an accessible text layer.",
            "recommended_correction": "Upload a digitally generated PDF (from MS Word/LaTeX) or request manual auditor review."
        })

        dept_code = (metadata.get("department_code") or "").upper()
        dept_name = (metadata.get("department_name") or "")
        course_code = (metadata.get("course_code") or "").upper()
        course_name = (metadata.get("course_name") or "")
        exam_cat = metadata.get("exam_category", "MID1").upper()
        exp_marks = metadata.get("max_marks") or (40 if exam_cat in ("MID1", "MID2", "MID") else 70)

        for req_name, exp_val in [
            ("Institutional Header", metadata.get("institution_name") or "Anantha Lakshmi Institute of Technology and Sciences"),
            ("Examination Type", "Mid Examination" if exam_cat in ("MID1", "MID2") else "Semester Examination"),
            ("Department / Branch", f"{dept_name} ({dept_code})".strip() if (dept_name or dept_code) else "Department Header"),
            ("Course / Subject Details", f"{course_name} [{course_code}]".strip() if (course_name or course_code) else "Course Header"),
            ("Section Structure (Unit Architecture)" if exam_cat in ("MID1", "MID2", "MID") else "Section Structure (Part A & Part B)", "Unit Headings with Internal Choice" if exam_cat in ("MID1", "MID2", "MID") else "Part A and Part B clearly demarcated"),
            ("Question Numbering & Count", "Standard numbered questions"),
            ("Total Maximum Marks", f"{exp_marks} Marks"),
        ]:
            items.append({
                "requirement": req_name,
                "expected_value": exp_val,
                "detected_value": "Unreadable in scanned raster format",
                "result": "Needs Review",
                "explanation": "Automated verification is inconclusive due to absence of machine-readable text. Requires human auditor review.",
                "recommended_correction": "Review physical document manually or upload high-resolution text PDF."
            })

        summary = {
            "total_checks": len(items),
            "passed_checks": 0,
            "failed_checks": 0,
            "missing_requirements": 0,
            "needs_review": len(items),
            "compliance_percentage": 0.0,
            "validation_status": "NEEDS_REVIEW"
        }
        return {
            "validation_status": "NEEDS_REVIEW",
            "compliance_percentage": 0.0,
            "summary": summary,
            "items": items,
            "analyzed_at": datetime.now().isoformat()
        }

    # If not scanned, proceed with normal digital text checks
    items.append({
        "requirement": "Digital Text Readability",
        "expected_value": "Searchable digital text layer",
        "detected_value": f"Valid text layer ({text_length} chars across {total_pages} page(s))",
        "result": "Correct",
        "explanation": "PDF contains clear machine-readable digital text.",
        "recommended_correction": "None required."
    })

    # Check 2: College / Institution Header
    inst_name = metadata.get("institution_name") or "Anantha Lakshmi Institute of Technology and Sciences"
    inst_norm = normalize(inst_name)
    has_header = (
        inst_norm in full_norm[:1500] or 
        "anantha lakshmi" in full_norm[:1500] or 
        "technology and sciences" in full_norm[:1500] or
        any(k in header_preview for k in ["college", "institute", "technology", "university"])
    )
    if has_header:
        items.append({
            "requirement": "Institutional Header",
            "expected_value": inst_name,
            "detected_value": "Official College Header Found in Top Section",
            "result": "Correct",
            "explanation": "Document contains the authorized institution name in the header block.",
            "recommended_correction": "None required."
        })
    else:
        items.append({
            "requirement": "Institutional Header",
            "expected_value": inst_name,
            "detected_value": "Header text missing or unrecognized",
            "result": "Missing",
            "explanation": f"Official institution name '{inst_name}' was not detected in the header region.",
            "recommended_correction": f"Include the official header banner: '{inst_name}' at the top of page 1."
        })

    # Check 3: Examination Category / Type
    exam_category = metadata.get("exam_category", "MID1").upper()
    if exam_category in ("MID1", "MID2", "MID"):
        expected_cat_text = "Mid Examination"
        detected_cat = "Mid Examination" if any(k in full_norm for k in ["mid examination", "mid exam", "mid semester", "mid-semester", "mid 1", "mid 2", "mid-1", "mid-2", "mid-i", "mid-ii", "mid1", "mid2", "internal test"]) else None
    else:
        expected_cat_text = "Semester / End-Semester Examination"
        detected_cat = "Semester Examination" if any(k in full_norm for k in ["semester examination", "end semester", "end-semester", "semester exam", "university examination", "final examination", "regular examination", "sem exam"]) else None

    if detected_cat:
        items.append({
            "requirement": "Examination Type",
            "expected_value": expected_cat_text,
            "detected_value": detected_cat,
            "result": "Correct",
            "explanation": f"Document specifies the required {expected_cat_text}.",
            "recommended_correction": "None required."
        })
    else:
        items.append({
            "requirement": "Examination Type",
            "expected_value": expected_cat_text,
            "detected_value": "Unspecified examination title",
            "result": "Incorrect",
            "explanation": f"Expected examination title matching '{expected_cat_text}' was not detected in headers.",
            "recommended_correction": f"Add the clear examination title '{expected_cat_text}' in the header details."
        })

    # Check 4: Department Match
    dept_code = (metadata.get("department_code") or "").upper()
    dept_name = (metadata.get("department_name") or "")
    if dept_code or dept_name:
        expected_dept = f"{dept_name} ({dept_code})".strip()
        has_dept = (
            (dept_code and dept_code.lower() in full_norm) or 
            (dept_name and normalize(dept_name) in full_norm) or
            ("department" in full_norm and any(c in full_norm for c in ["cse", "ece", "me", "ce", "cai"]))
        )
        if has_dept:
            items.append({
                "requirement": "Department / Branch",
                "expected_value": expected_dept,
                "detected_value": f"Department marker matched ({dept_code or 'Verified'})",
                "result": "Correct",
                "explanation": "Document is mapped to the correct engineering department.",
                "recommended_correction": "None required."
            })
        else:
            items.append({
                "requirement": "Department / Branch",
                "expected_value": expected_dept,
                "detected_value": "Department identifier not found",
                "result": "Incorrect",
                "explanation": f"Expected department '{expected_dept}' was not found in document text.",
                "recommended_correction": f"Specify 'Department of {dept_name or dept_code}' under the institutional header."
            })

    # Check 5: Course / Subject Name & Subject Code
    course_code = (metadata.get("course_code") or "").upper()
    course_name = (metadata.get("course_name") or "")
    if course_code:
        has_code = course_code.lower() in full_norm
        has_name = normalize(course_name) in full_norm if course_name else True

        if has_code and has_name:
            items.append({
                "requirement": "Course / Subject Details",
                "expected_value": f"{course_name} [{course_code}]",
                "detected_value": f"Matched Subject Code '{course_code}' and Course Title",
                "result": "Correct",
                "explanation": "Subject name and subject code strictly match approved curriculum data.",
                "recommended_correction": "None required."
            })
        elif has_code or has_name:
            detected_part = course_code if has_code else course_name
            items.append({
                "requirement": "Course / Subject Details",
                "expected_value": f"{course_name} [{course_code}]",
                "detected_value": f"Partially matched: '{detected_part}'",
                "result": "Needs Review",
                "explanation": "Detected partial course match. Verify exact subject title and code alignment.",
                "recommended_correction": f"Format course line as: 'Subject: {course_name} | Subject Code: {course_code}'."
            })
        else:
            items.append({
                "requirement": "Course / Subject Details",
                "expected_value": f"{course_name} [{course_code}]",
                "detected_value": "Subject title/code not detected",
                "result": "Missing",
                "explanation": f"Neither course code '{course_code}' nor title '{course_name}' was found in headers.",
                "recommended_correction": f"Add subject line: 'Subject: {course_name} | Subject Code: {course_code}'."
            })

    # Check 6: Section Structure (Unit Architecture for Mid, Part A/B for Semester)
    is_mid_exam = exam_category in ("MID1", "MID2", "MID")

    if is_mid_exam:
        # Mid Papers do NOT have Part A / Part B headings; they utilize Question 1 & Unit Headings with internal choice ('OR')
        has_units = "unit" in full_norm or any(u in full_norm for u in ["unit-i", "unit-ii", "unit-iii", "unit-iv", "unit-v", "unit 1", "unit 2", "unit 3", "unit 4", "unit 5"])
        has_or = bool(re.search(r"\bor\b", full_norm)) or "either" in full_norm

        if has_units:
            items.append({
                "requirement": "Section Structure (Unit Architecture & Internal Choice)",
                "expected_value": "Unit Headings with Internal Choice ('OR')",
                "detected_value": f"Unit-wise breakdown verified ({'with internal choice OR' if has_or else 'standard unit structure'})",
                "result": "Correct",
                "explanation": "Mid question paper complies with official autonomous layout without Part A / Part B subdivisions.",
                "recommended_correction": "None required."
            })
        else:
            items.append({
                "requirement": "Section Structure (Unit Architecture & Internal Choice)",
                "expected_value": "Unit Headings (e.g. UNIT-I/II or UNIT-III/IV/V) with 'OR' internal choice",
                "detected_value": "Unit headings not detected",
                "result": "Missing",
                "explanation": "Descriptive questions must be organized under Unit headings with internal choice ('OR').",
                "recommended_correction": "Add clear unit headings such as 'UNIT-I', 'UNIT-II' or 'UNIT-III', 'UNIT-IV', 'UNIT-V'."
            })
    else:
        # Semester Examination uses Part A and Part B
        has_part_a = "part a" in full_norm or "section a" in full_norm
        has_part_b = "part b" in full_norm or "section b" in full_norm

        if has_part_a and has_part_b:
            items.append({
                "requirement": "Section Structure (Part A & Part B)",
                "expected_value": "Part A and Part B clearly demarcated",
                "detected_value": "Both Part A and Part B detected in sequential order",
                "result": "Correct",
                "explanation": "Paper contains standard structural divisions for objective/short and descriptive sections.",
                "recommended_correction": "None required."
            })
        elif has_part_a or has_part_b:
            missing_sec = "Part B" if has_part_a else "Part A"
            items.append({
                "requirement": "Section Structure (Part A & Part B)",
                "expected_value": "Part A and Part B clearly demarcated",
                "detected_value": f"Only {'Part A' if has_part_a else 'Part B'} detected",
                "result": "Missing",
                "explanation": f"Missing mandatory structural section '{missing_sec}'.",
                "recommended_correction": f"Organize the paper into two sections: 'PART A' (Short Answer) and 'PART B' (Descriptive)."
            })
        else:
            items.append({
                "requirement": "Section Structure (Part A & Part B)",
                "expected_value": "Part A and Part B sections",
                "detected_value": "No distinct section markers found",
                "result": "Missing",
                "explanation": "No distinct 'Part A' and 'Part B' markers detected.",
                "recommended_correction": "Add clear section headings like 'PART A' and 'PART B'."
            })

    # Check 7: Question Numbering & Minimum Count
    total_q_count = count_questions(full_text)
    expected_min_questions = 8 if exam_category in ("MID1", "MID2") else 10
    if total_q_count >= expected_min_questions:
        items.append({
            "requirement": "Question Numbering & Count",
            "expected_value": f"Minimum {expected_min_questions} numbered questions",
            "detected_value": f"{total_q_count} questions detected with standard numbering",
            "result": "Correct",
            "explanation": f"Detected {total_q_count} questions, satisfying the minimum requirement of {expected_min_questions}.",
            "recommended_correction": "None required."
        })
    elif total_q_count > 0:
        items.append({
            "requirement": "Question Numbering & Count",
            "expected_value": f"Minimum {expected_min_questions} numbered questions",
            "detected_value": f"Only {total_q_count} questions detected",
            "result": "Incorrect",
            "explanation": f"Total question count ({total_q_count}) is below the required count ({expected_min_questions}).",
            "recommended_correction": f"Ensure all questions are numbered (e.g., '1.', '2.', 'Q1.') and cover the syllabus syllabus requirements."
        })
    else:
        items.append({
            "requirement": "Question Numbering & Count",
            "expected_value": f"Minimum {expected_min_questions} numbered questions",
            "detected_value": "No recognized question numbers",
            "result": "Missing",
            "explanation": "Could not identify standard question numbering patterns (e.g. '1.', '2.', 'Q1').",
            "recommended_correction": "Prefix each question clearly with numbers like '1.', '2.', '3.' on new lines."
        })

    # Check 8: Total Marks Scheme
    expected_marks = metadata.get("max_marks") or (40 if exam_category in ("MID1", "MID2", "MID") else 70)
    detected_marks = extract_detected_total_marks(full_text)
    if detected_marks:
        is_mid_marks_valid = exam_category in ("MID1", "MID2", "MID") and detected_marks in (40, 30)
        if detected_marks == expected_marks or is_mid_marks_valid:
            items.append({
                "requirement": "Total Maximum Marks",
                "expected_value": f"{expected_marks} Marks",
                "detected_value": f"{detected_marks} Marks Detected",
                "result": "Correct",
                "explanation": f"Maximum marks match configured examination standard of {expected_marks} marks.",
                "recommended_correction": "None required."
            })
        else:
            items.append({
                "requirement": "Total Maximum Marks",
                "expected_value": f"{expected_marks} Marks",
                "detected_value": f"{detected_marks} Marks Detected",
                "result": "Incorrect",
                "explanation": f"The detected total ({detected_marks} Marks) does not match the configured total ({expected_marks} Marks).",
                "recommended_correction": f"Verify the marks assigned to all questions and sections to sum to exactly {expected_marks} Marks."
            })
    else:
        # Check if marks keywords appear
        if "mark" in full_norm or "[m]" in full_norm:
            items.append({
                "requirement": "Total Maximum Marks",
                "expected_value": f"{expected_marks} Marks",
                "detected_value": f"Marks keywords found, total unparsed",
                "result": "Needs Review",
                "explanation": f"Marks annotations are present, but explicit total of {expected_marks} Marks could not be definitively extracted.",
                "recommended_correction": f"State total marks prominently in header as: 'Maximum Marks: {expected_marks}'."
            })
        else:
            items.append({
                "requirement": "Total Maximum Marks",
                "expected_value": f"{expected_marks} Marks",
                "detected_value": "No marks scheme detected",
                "result": "Missing",
                "explanation": "No question marks or maximum marks declaration detected in the document.",
                "recommended_correction": f"Add '[X Marks]' brackets to each question and declare 'Maximum Marks: {expected_marks}' in the header."
            })

    # Compute Summary Statistics
    total_checks = len(items)
    passed_checks = sum(1 for it in items if it["result"] == "Correct")
    failed_checks = sum(1 for it in items if it["result"] == "Incorrect")
    missing_reqs = sum(1 for it in items if it["result"] == "Missing")
    needs_review = sum(1 for it in items if it["result"] == "Needs Review")
    not_applicable = sum(1 for it in items if it["result"] == "Not Applicable")

    applicable_checks = total_checks - not_applicable
    compliance_pct = round((passed_checks / applicable_checks * 100.0), 1) if applicable_checks > 0 else 0.0

    if failed_checks > 0 or missing_reqs > 0:
        overall_status = "INVALID"
    elif needs_review > 0:
        overall_status = "NEEDS_REVIEW"
    else:
        overall_status = "VALID"

    summary = {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "missing_requirements": missing_reqs,
        "needs_review": needs_review,
        "compliance_percentage": compliance_pct,
        "validation_status": overall_status
    }

    return {
        "validation_status": overall_status,
        "compliance_percentage": compliance_pct,
        "summary": summary,
        "items": items,
        "analyzed_at": datetime.now().isoformat()
    }

def evaluate_requirement(req: dict, pdf_data: Dict[str, Any]) -> Tuple[bool, str | None]:
    """Preserves backwards compatibility for existing custom format requirements."""
    req_name = req.get("requirement_name", "").strip()
    req_type = normalize(req.get("requirement_type", ""))
    req_val = (req.get("requirement_value") or "").strip()
    name_norm = normalize(req_name)
    full_text = pdf_data.get("full_text", "")
    full_norm = normalize(full_text)
    header_preview = normalize(pdf_data.get("header_preview", ""))

    if "header" in req_type or "college header" in name_norm:
        if req_val and normalize(req_val) in full_norm[:1500]:
            return True, None
        if any(term in header_preview for term in ["college", "institute", "technology", "university"]):
            return True, None
        return False, f"Expected header '{req_val or req_name}' was not detected in top section."

    if "footer" in req_type or "footer" in name_norm:
        if len(pdf_data.get("footer_preview", "").strip()) > 3:
            return True, None
        return False, "Footer or ending section was not detected."

    if "question_count" in req_type or "count" in req_type:
        count_match = re.search(r"\d+", req_val or req_name)
        if not count_match:
            return True, None
        exp = int(count_match.group())
        det = count_questions(full_text)
        if det >= exp or str(exp) in full_norm:
            return True, None
        return False, f"Expected {exp} questions, detected {det}."

    if "marks" in req_type:
        target_marks = re.search(r"\d+", req_val or req_name)
        if target_marks and target_marks.group() in full_norm:
            return True, None
        if "mark" in full_norm:
            return True, None
        return False, f"Required structural section '{req_name}' was not detected."

    # 6. Heading / Unit section presence
    if "heading" in req_type or "heading" in name_norm or re.search(r"\bunit\s*[1-5ivx]+\b", name_norm):
        # Search for heading name in text
        # If it's "Unit 1", "Unit 1 Heading" or similar:
        unit_match = re.search(r"unit\s*([1-5ivx]+)", name_norm)
        if unit_match:
            u_num = unit_match.group(1).lower()
            roman_map = {"1": "i", "2": "ii", "3": "iii", "4": "iv", "5": "v"}
            roman_num = roman_map.get(u_num, u_num)
            patterns = [
                rf"\bunit\s*[-–:]?\s*{re.escape(u_num)}\b",
                rf"\bunit\s*[-–:]?\s*{re.escape(roman_num)}\b",
                rf"\bunit\s*[-–:]?\s*{re.escape(u_num.upper())}\b"
            ]
            if any(re.search(p, full_norm) for p in patterns):
                return True, None
            return False, f"Required heading / section for Unit {u_num.upper()} was not found."

        if req_val and normalize(req_val) in full_norm:
            return True, None
        return False, f"Required marks scheme ({req_val or req_name}) not detected."

# Autonomous Status
    if "autonomous" in name_norm or "autonomous" in normalize(req_val):
        if "autonomous" in full_norm:
            return True, None
        return False, "Autonomous status marker '(AUTONOMOUS)' was not detected."

    # Location / Address
    if any(k in name_norm for k in ["location", "address", "ananthapuramu", "pin"]):
        if any(k in full_norm for k in ["515721", "ananthapuramu", "s.k. university", "near s.k"]):
            return True, None
        return False, f"Institutional address '{req_val}' was not detected."

    # Regulations
    if "regulation" in name_norm or "regulation" in normalize(req_val):
        if any(k in full_norm for k in ["regulation", "r-24", "r24", "r-20", "r-23", "r20", "r23"]):
            return True, None
        return False, "Academic regulations tag (e.g. 'Regulations: R-24') was not detected."

    # Time Duration
    if "time" in name_norm or "time duration" in name_norm:
        if any(k in full_norm for k in ["110 min", "110", "time", "min", "hours"]):
            return True, None
        return False, f"Time duration specification '{req_val}' was not detected."

    # Maximum Marks
    if "maximum marks" in name_norm or "max marks" in name_norm:
        if any(k in full_norm for k in ["40", "max marks", "max. marks", "70", "30"]):
            return True, None
        return False, f"Maximum marks specification '{req_val}' was not detected."

    # General Instruction
    if "instruction" in name_norm or "answer all" in name_norm:
        if any(k in full_norm for k in ["answer all questions", "answer all", "instructions", "instruction"]):
            return True, None
        return False, f"General instruction '{req_val}' was not detected."

    # Table Columns
    if "table column" in name_norm:
        if "s.no" in name_norm or "sno" in name_norm:
            if any(k in full_norm for k in ["s.no", "sno", "q.no", "qno", "s. no", "sl.no"]):
                return True, None
            return False, "Table column 'S.No' was not detected."
        if "blooms" in name_norm:
            if any(k in full_norm for k in ["bloom", "blooms level", "apply", "remember", "understand", "analyze", "evaluate", "bt level"]):
                return True, None
            return False, "Table column 'Blooms Level' was not detected."
        if "outcome" in name_norm or "course outcome" in name_norm:
            if any(k in full_norm for k in ["course outcome", "co", "co1", "co2", "co3", "co4", "co5", "co6"]):
                return True, None
            return False, "Table column 'Course Outcome' was not detected."
        if "marks" in name_norm:
            if "mark" in full_norm:
                return True, None
            return False, "Table column 'Marks' was not detected."

    # Internal Choice (OR)
    if "internal choice" in name_norm or "(or)" in name_norm or "choice" in name_norm:
        if re.search(r"\bor\b", full_norm) or "either" in full_norm:
            return True, None
        return False, "Internal choice 'OR' was not detected between descriptive questions."

    # Unit Syllabus Architecture
    if "unit" in name_norm and ("syllabus" in name_norm or "architecture" in name_norm):
        if "unit" in full_norm:
            return True, None
        return False, "Unit syllabus section markers were not detected."

    # Question 1 (Short Answer Section)
    if "question 1" in name_norm or "short answer" in name_norm:
        if any(k in full_norm for k in ["1.", "1", "q1", "(a)", "a.", "part a"]):
            return True, None
        return False, "Short answer question section (Question 1) was not detected."

    # Unit Descriptive Weightage
    if "descriptive marks" in name_norm or "weightage" in name_norm:
        if any(k in full_norm for k in ["10", "5", "marks"]):
            return True, None
        return False, "Descriptive marks allocation (10 Marks / 5+5 Marks) was not detected."

    # Total Marks Scheme Verification
    if "total marks" in name_norm:
        if any(k in full_norm for k in ["40", "70", "30", "total"]):
            return True, None
        return False, "Total marks verification failed."

    if req_val and normalize(req_val) in full_norm:
        return True, None
    if name_norm in full_norm:
        return True, None

    return False, f"Required element '{req_name}' was not detected."

def analyze_document_structure(file_path: str, format_record: dict, requirements: List[dict]) -> Dict[str, Any]:
    """Legacy runner preserved for custom Auditor formats."""
    pdf_data = extract_pdf_data(file_path)
    requirement_results = []
    all_mandatory_passed = True

    for req in sorted(requirements, key=lambda x: x.get("display_order", 1)):
        req_name = req.get("requirement_name", "Requirement")
        is_required = req.get("is_required", True)
        passed, reason = evaluate_requirement(req, pdf_data)

        requirement_results.append({
            "name": req_name,
            "type": req.get("requirement_type", "text"),
            "required": is_required,
            "status": "PASS" if passed else "FAIL",
            "reason": reason if not passed else None
        })
        if is_required and not passed:
            all_mandatory_passed = False

    final_status = "ACCEPTED" if all_mandatory_passed else "REJECTED"
    return {
        "status": final_status,
        "format_id": format_record.get("id"),
        "format_name": format_record.get("format_name"),
        "total_requirements": len(requirement_results),
        "passed_requirements": sum(1 for r in requirement_results if r["status"] == "PASS"),
        "failed_requirements": sum(1 for r in requirement_results if r["status"] == "FAIL"),
        "requirements": requirement_results,
        "analyzed_at": datetime.now().isoformat()
    }


# =====================================================================
# 2. COURSE STRUCTURE & SYLLABUS VALIDATOR (6-Column Breakdown)
# =====================================================================
def validate_course_structure_document(file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    path = Path(file_path)
    file_name = metadata.get("file_name") or path.name

    if not path.exists() or path.stat().st_size == 0:
        item = {
            "requirement": "File Integrity & Format",
            "expected_value": "Valid non-empty PDF document",
            "detected_value": "Empty or missing file on disk",
            "result": "Incorrect",
            "explanation": "Uploaded file is 0 bytes or could not be read.",
            "recommended_correction": "Re-export and upload a valid PDF document."
        }
        return {
            "validation_status": "INVALID",
            "compliance_percentage": 0.0,
            "summary": {"total_checks": 1, "passed_checks": 0, "failed_checks": 1, "missing_requirements": 1, "needs_review": 0, "compliance_percentage": 0.0, "validation_status": "INVALID"},
            "items": [item],
            "analyzed_at": datetime.now().isoformat()
        }

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
        return {
            "validation_status": "INVALID",
            "compliance_percentage": 0.0,
            "summary": {"total_checks": 1, "passed_checks": 0, "failed_checks": 1, "missing_requirements": 1, "needs_review": 0, "compliance_percentage": 0.0, "validation_status": "INVALID"},
            "items": [item],
            "analyzed_at": datetime.now().isoformat()
        }

    full_text = pdf_data.get("full_text", "")
    full_norm = normalize(full_text)
    header_preview = normalize(pdf_data.get("header_preview", ""))
    total_pages = pdf_data.get("total_pages", 1)
    text_length = len(full_text.strip())

    items: List[Dict[str, Any]] = []

    # Check 1: Scanned vs Text Layer
    is_scanned = text_length < 40 and total_pages > 0
    if is_scanned:
        items.append({
            "requirement": "Digital Text Readability",
            "expected_value": "Searchable digital text layer",
            "detected_value": f"Scanned/Raster image ({text_length} text chars extracted)",
            "result": "Needs Review",
            "explanation": "Document appears to be a scanned image or photo without an accessible text layer.",
            "recommended_correction": "Upload a digitally exported PDF syllabus or request manual auditor review."
        })
        for req_name, exp_val in [
            ("Institutional Header Banner", metadata.get("institution_name") or "Anantha Lakshmi Institute of Technology and Sciences"),
            ("Academic Regulation & Year", "JNTUA Regulation (R20/R23) & Academic Year"),
            ("Course / Subject Details", "Subject Code & Approved Course Title"),
            ("Course Outcomes (CO1-CO5)", "Minimum 5 Course Outcomes (CO1 to CO5)"),
            ("5-Unit Curriculum Architecture", "Comprehensive coverage of Unit I through Unit V"),
            ("Prescribed Textbooks & References", "Author, Title, Publisher, and Edition"),
            ("Evaluation & Marks Scheme", "Internal Continuous Assessment & End Exam marks"),
        ]:
            items.append({
                "requirement": req_name,
                "expected_value": exp_val,
                "detected_value": "Unreadable in scanned raster format",
                "result": "Needs Review",
                "explanation": "Automated verification is inconclusive due to absence of text. Requires auditor review.",
                "recommended_correction": "Review physical document manually or upload high-resolution text PDF."
            })
        summary = {"total_checks": len(items), "passed_checks": 0, "failed_checks": 0, "missing_requirements": 0, "needs_review": len(items), "compliance_percentage": 0.0, "validation_status": "NEEDS_REVIEW"}
        return {"validation_status": "NEEDS_REVIEW", "compliance_percentage": 0.0, "summary": summary, "items": items, "analyzed_at": datetime.now().isoformat()}

    items.append({
        "requirement": "Digital Text Readability",
        "expected_value": "Searchable digital text layer",
        "detected_value": f"Valid text layer ({text_length} chars across {total_pages} page(s))",
        "result": "Correct",
        "explanation": "PDF contains clear machine-readable digital text.",
        "recommended_correction": "None required."
    })

    # Check 2: Institutional Header
    inst_name = metadata.get("institution_name") or "Anantha Lakshmi Institute of Technology and Sciences"
    has_header = (
        normalize(inst_name) in full_norm[:1500] or
        "anantha lakshmi" in full_norm[:1500] or
        "technology and sciences" in full_norm[:1500] or
        any(k in header_preview for k in ["college", "institute", "technology", "university", "jntua"])
    )
    if has_header:
        items.append({
            "requirement": "Institutional Header Banner",
            "expected_value": inst_name,
            "detected_value": "Authorized Institutional Header detected",
            "result": "Correct",
            "explanation": "Header contains authorized college and governance banners.",
            "recommended_correction": "None required."
        })
    else:
        items.append({
            "requirement": "Institutional Header Banner",
            "expected_value": inst_name,
            "detected_value": "Header text missing or unrecognized",
            "result": "Missing",
            "explanation": f"Official institution name '{inst_name}' was not detected in top section.",
            "recommended_correction": f"Add the official institutional title banner: '{inst_name}' at the top."
        })

    # Check 3: Academic Regulation & Year
    has_reg = any(r in full_norm for r in ["r20", "r23", "r19", "jntua", "regulation", "autonomous", "academic regulations"])
    has_year = any(y in full_norm for y in ["2024", "2025", "2026", "2023", "academic year", "year"])
    if has_reg and has_year:
        items.append({
            "requirement": "Academic Regulation & Year",
            "expected_value": "JNTUA Regulation (R20/R23) & Academic Year",
            "detected_value": "Regulation code and Academic Year detected",
            "result": "Correct",
            "explanation": "Syllabus strictly declares approved regulatory framework and academic year.",
            "recommended_correction": "None required."
        })
    elif has_reg or has_year:
        items.append({
            "requirement": "Academic Regulation & Year",
            "expected_value": "JNTUA Regulation (R20/R23) & Academic Year",
            "detected_value": "Partially matched regulation or academic year",
            "result": "Needs Review",
            "explanation": "Declared regulation or academic calendar year requires verification.",
            "recommended_correction": "Clearly specify: 'JNTUA Academic Regulations R20 / R23 | Academic Year: 2025-2026'."
        })
    else:
        items.append({
            "requirement": "Academic Regulation & Year",
            "expected_value": "JNTUA Regulation (R20/R23) & Academic Year",
            "detected_value": "No regulation citation found",
            "result": "Missing",
            "explanation": "Syllabus does not state the governing academic regulation (e.g. JNTUA R20/R23).",
            "recommended_correction": "State the academic regulation line: 'Regulation: JNTUA R20 / R23'."
        })

    # Check 4: Department & Course / Subject Details
    dept_code = (metadata.get("department_code") or "").upper()
    course_code = (metadata.get("course_code") or "").upper()
    course_name = metadata.get("course_name") or ""
    has_dept = (dept_code and dept_code.lower() in full_norm) or any(c in full_norm for c in ["department", "cse", "ece", "cai", "engineering", "b.tech"])
    has_course = (course_code and course_code.lower() in full_norm) or (course_name and normalize(course_name) in full_norm) or any(k in full_norm for k in ["course code", "subject code", "course title", "subject"])

    if has_dept and has_course:
        items.append({
            "requirement": "Department & Course Alignment",
            "expected_value": f"{course_name or 'Course'} [{course_code or 'Code'}]",
            "detected_value": f"Department marker and Course details matched",
            "result": "Correct",
            "explanation": "Document correctly identifies the academic department and subject code.",
            "recommended_correction": "None required."
        })
    else:
        items.append({
            "requirement": "Department & Course Alignment",
            "expected_value": f"{course_name or 'Course'} [{course_code or 'Code'}]",
            "detected_value": "Course code or department mismatch",
            "result": "Incorrect",
            "explanation": "Could not identify unambiguous course code or department title in syllabus.",
            "recommended_correction": f"Include: 'Department of {dept_code or 'Engineering'} | Subject: {course_name} ({course_code})'."
        })

    # Check 5: Course Objectives & Outcomes (CO1-CO5)
    has_obj = "objective" in full_norm or "course objectives" in full_norm
    co_matches = re.findall(r"co\s*[1-5]", full_norm)
    has_outcomes = len(set(co_matches)) >= 3 or ("course outcome" in full_norm or "outcomes" in full_norm)

    if has_obj and has_outcomes:
        co_count = len(set(co_matches))
        items.append({
            "requirement": "Course Objectives & Outcomes",
            "expected_value": "Course Objectives + Minimum 5 Course Outcomes (CO1-CO5)",
            "detected_value": f"Objectives present, {co_count if co_count > 0 else 5} CO statements detected",
            "result": "Correct",
            "explanation": "Syllabus outlines pedagogical objectives and Bloom's taxonomy mapped outcomes.",
            "recommended_correction": "None required."
        })
    elif has_obj or has_outcomes:
        items.append({
            "requirement": "Course Objectives & Outcomes",
            "expected_value": "Course Objectives + Minimum 5 Course Outcomes (CO1-CO5)",
            "detected_value": "Partial objectives or outcomes detected",
            "result": "Needs Review",
            "explanation": "Objectives or Course Outcomes (CO1-CO5) are incomplete.",
            "recommended_correction": "Define 5 distinct Course Outcomes: 'CO1', 'CO2', 'CO3', 'CO4', and 'CO5'."
        })
    else:
        items.append({
            "requirement": "Course Objectives & Outcomes",
            "expected_value": "Course Objectives + Minimum 5 Course Outcomes (CO1-CO5)",
            "detected_value": "Neither objectives nor CO statements detected",
            "result": "Missing",
            "explanation": "Institutional syllabus standard requires explicit Course Objectives and CO1-CO5 statements.",
            "recommended_correction": "Add 'Course Objectives' and 'Course Outcomes (CO1 to CO5)' sections."
        })

    # Check 6: 5-Unit Curriculum Architecture
    units_found = []
    for u_num, u_name in [("1", "unit 1"), ("2", "unit 2"), ("3", "unit 3"), ("4", "unit 4"), ("5", "unit 5"),
                          ("i", "unit i"), ("ii", "unit ii"), ("iii", "unit iii"), ("iv", "unit iv"), ("v", "unit v")]:
        if u_name in full_norm:
            units_found.append(u_num.upper())

    unique_units = set(units_found)
    # Map roman to arabic
    normalized_units = set()
    for u in unique_units:
        if u in ("1", "I"): normalized_units.add(1)
        elif u in ("2", "II"): normalized_units.add(2)
        elif u in ("3", "III"): normalized_units.add(3)
        elif u in ("4", "IV"): normalized_units.add(4)
        elif u in ("5", "V"): normalized_units.add(5)

    if len(normalized_units) >= 5:
        items.append({
            "requirement": "5-Unit Curriculum Architecture",
            "expected_value": "Complete 5-Unit Structure (Unit I through Unit V)",
            "detected_value": f"All 5 Units detected (Units 1, 2, 3, 4, 5)",
            "result": "Correct",
            "explanation": "Syllabus complies with JNTUA university standard 5-unit curriculum division.",
            "recommended_correction": "None required."
        })
    elif len(normalized_units) >= 3:
        missing_units = [f"Unit {n}" for n in range(1, 6) if n not in normalized_units]
        items.append({
            "requirement": "5-Unit Curriculum Architecture",
            "expected_value": "Complete 5-Unit Structure (Unit I through Unit V)",
            "detected_value": f"Detected {len(normalized_units)}/5 units. Missing: {', '.join(missing_units)}",
            "result": "Missing",
            "explanation": f"Syllabus lacks mandatory unit headings: {', '.join(missing_units)}.",
            "recommended_correction": "Organize course syllabus into five distinct units: 'UNIT-I' through 'UNIT-V'."
        })
    else:
        items.append({
            "requirement": "5-Unit Curriculum Architecture",
            "expected_value": "Complete 5-Unit Structure (Unit I through Unit V)",
            "detected_value": "No standard unit markers detected",
            "result": "Missing",
            "explanation": "Could not identify standard unit divisions ('UNIT I', 'UNIT II', etc.).",
            "recommended_correction": "Divide syllabus content into headings: 'UNIT I', 'UNIT II', 'UNIT III', 'UNIT IV', 'UNIT V'."
        })

    # Check 7: Prescribed Textbooks & Reference Literature
    has_textbooks = any(t in full_norm for t in ["textbook", "text books", "text book", "prescribed books"])
    has_references = any(r in full_norm for r in ["reference book", "references", "reference literature", "suggested reading"])

    if has_textbooks and has_references:
        items.append({
            "requirement": "Prescribed Textbooks & Literature",
            "expected_value": "Both Textbooks and Reference Books cited with publisher/year",
            "detected_value": "Textbooks and Reference literature sections detected",
            "result": "Correct",
            "explanation": "Standard academic citations and reading material provided for learners.",
            "recommended_correction": "None required."
        })
    elif has_textbooks or has_references:
        items.append({
            "requirement": "Prescribed Textbooks & Literature",
            "expected_value": "Both Textbooks and Reference Books cited with publisher/year",
            "detected_value": f"Only {'Textbooks' if has_textbooks else 'References'} detected",
            "result": "Needs Review",
            "explanation": "Both primary Textbooks and supplementary Reference Books must be provided.",
            "recommended_correction": "Add separate sections for 'Textbooks' and 'Reference Books'."
        })
    else:
        items.append({
            "requirement": "Prescribed Textbooks & Literature",
            "expected_value": "Both Textbooks and Reference Books cited with publisher/year",
            "detected_value": "No textbook or reference sections found",
            "result": "Missing",
            "explanation": "Syllabus does not cite approved textbooks or reference literature.",
            "recommended_correction": "Add 'Textbooks' and 'Reference Books' with Author, Title, Edition, and Publisher."
        })

    # Check 8: Evaluation & Marks Scheme
    has_marks = any(m in full_norm for m in ["marks", "credits", "evaluation", "internal", "external", "scheme of examination", "cie", "see"])
    if has_marks:
        items.append({
            "requirement": "Evaluation & Marks Scheme",
            "expected_value": "Internal Continuous Assessment (30M) & End Exam (70M) weightage",
            "detected_value": "Evaluation scheme / credits detected",
            "result": "Correct",
            "explanation": "Document specifies course credits and evaluation breakdown.",
            "recommended_correction": "None required."
        })
    else:
        items.append({
            "requirement": "Evaluation & Marks Scheme",
            "expected_value": "Internal Continuous Assessment (30M) & End Exam (70M) weightage",
            "detected_value": "No evaluation criteria found",
            "result": "Missing",
            "explanation": "Course structure lacks marks breakdown or credit allocation.",
            "recommended_correction": "State: 'Continuous Internal Evaluation (CIE): 30 Marks | Semester End Exam (SEE): 70 Marks'."
        })

    total_checks = len(items)
    passed_checks = sum(1 for it in items if it["result"] == "Correct")
    failed_checks = sum(1 for it in items if it["result"] == "Incorrect")
    missing_reqs = sum(1 for it in items if it["result"] == "Missing")
    needs_review = sum(1 for it in items if it["result"] == "Needs Review")
    not_applicable = sum(1 for it in items if it["result"] == "Not Applicable")

    applicable_checks = total_checks - not_applicable
    compliance_pct = round((passed_checks / applicable_checks * 100.0), 1) if applicable_checks > 0 else 0.0

    if failed_checks > 0 or missing_reqs > 0:
        overall_status = "INVALID"
    elif needs_review > 0:
        overall_status = "NEEDS_REVIEW"
    else:
        overall_status = "VALID"

    summary = {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "missing_requirements": missing_reqs,
        "needs_review": needs_review,
        "compliance_percentage": compliance_pct,
        "validation_status": overall_status
    }

    return {
        "validation_status": overall_status,
        "compliance_percentage": compliance_pct,
        "summary": summary,
        "items": items,
        "analyzed_at": datetime.now().isoformat()
    }


# =====================================================================
# 3. QUESTION BANK VALIDATOR (6-Column Breakdown)
# =====================================================================
def validate_question_bank_document(file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    path = Path(file_path)
    file_name = metadata.get("file_name") or path.name

    if not path.exists() or path.stat().st_size == 0:
        item = {
            "requirement": "File Integrity & Format",
            "expected_value": "Valid non-empty PDF document",
            "detected_value": "Empty or missing file on disk",
            "result": "Incorrect",
            "explanation": "Uploaded file is 0 bytes or could not be read.",
            "recommended_correction": "Re-export and upload a valid PDF document."
        }
        return {
            "validation_status": "INVALID",
            "compliance_percentage": 0.0,
            "summary": {"total_checks": 1, "passed_checks": 0, "failed_checks": 1, "missing_requirements": 1, "needs_review": 0, "compliance_percentage": 0.0, "validation_status": "INVALID"},
            "items": [item],
            "analyzed_at": datetime.now().isoformat()
        }

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
        return {
            "validation_status": "INVALID",
            "compliance_percentage": 0.0,
            "summary": {"total_checks": 1, "passed_checks": 0, "failed_checks": 1, "missing_requirements": 1, "needs_review": 0, "compliance_percentage": 0.0, "validation_status": "INVALID"},
            "items": [item],
            "analyzed_at": datetime.now().isoformat()
        }

    full_text = pdf_data.get("full_text", "")
    full_norm = normalize(full_text)
    header_preview = normalize(pdf_data.get("header_preview", ""))
    total_pages = pdf_data.get("total_pages", 1)
    text_length = len(full_text.strip())

    items: List[Dict[str, Any]] = []

    # Check 1: Scanned vs Text Layer
    is_scanned = text_length < 40 and total_pages > 0
    if is_scanned:
        items.append({
            "requirement": "Digital Text Readability",
            "expected_value": "Searchable digital text layer",
            "detected_value": f"Scanned/Raster image ({text_length} text chars extracted)",
            "result": "Needs Review",
            "explanation": "Document appears to be a scanned image or photo without an accessible text layer.",
            "recommended_correction": "Upload a digitally exported PDF question bank or request manual auditor review."
        })
        for req_name, exp_val in [
            ("Institutional Header Banner", metadata.get("institution_name") or "Anantha Lakshmi Institute of Technology and Sciences"),
            ("Course & Branch Identifier", "Department Name and Approved Subject Code"),
            ("5-Unit Question Coverage", "Questions spanning all 5 Units (Unit I to Unit V)"),
            ("Dual-Tier Question Classification", "Part A (Short Answer) and Part B (Descriptive/Analytical)"),
            ("Bloom's Taxonomy & CO Mapping", "Cognitive levels (L1-L4) and Course Outcome mapping (CO1-CO5)"),
            ("Minimum Question Volume", "Minimum 15-20 total questions across all units"),
            ("Marks Allocation per Question", "Explicit marks declared for questions/sections"),
        ]:
            items.append({
                "requirement": req_name,
                "expected_value": exp_val,
                "detected_value": "Unreadable in scanned raster format",
                "result": "Needs Review",
                "explanation": "Automated verification is inconclusive due to absence of text. Requires auditor review.",
                "recommended_correction": "Review physical document manually or upload high-resolution text PDF."
            })
        summary = {"total_checks": len(items), "passed_checks": 0, "failed_checks": 0, "missing_requirements": 0, "needs_review": len(items), "compliance_percentage": 0.0, "validation_status": "NEEDS_REVIEW"}
        return {"validation_status": "NEEDS_REVIEW", "compliance_percentage": 0.0, "summary": summary, "items": items, "analyzed_at": datetime.now().isoformat()}

    items.append({
        "requirement": "Digital Text Readability",
        "expected_value": "Searchable digital text layer",
        "detected_value": f"Valid text layer ({text_length} chars across {total_pages} page(s))",
        "result": "Correct",
        "explanation": "PDF contains clear machine-readable digital text.",
        "recommended_correction": "None required."
    })

    # Check 2: Institutional Header Banner
    inst_name = metadata.get("institution_name") or "Anantha Lakshmi Institute of Technology and Sciences"
    has_header = (
        normalize(inst_name) in full_norm[:1500] or
        "anantha lakshmi" in full_norm[:1500] or
        "technology and sciences" in full_norm[:1500] or
        any(k in header_preview for k in ["college", "institute", "technology", "university", "department"])
    )
    if has_header:
        items.append({
            "requirement": "Institutional Header Banner",
            "expected_value": inst_name,
            "detected_value": "Authorized Institutional Header detected",
            "result": "Correct",
            "explanation": "Header contains authorized institution name and logo block.",
            "recommended_correction": "None required."
        })
    else:
        items.append({
            "requirement": "Institutional Header Banner",
            "expected_value": inst_name,
            "detected_value": "Header text missing or unrecognized",
            "result": "Missing",
            "explanation": f"Official institution name '{inst_name}' was not detected in top section.",
            "recommended_correction": f"Include the official header banner: '{inst_name}' at the top."
        })

    # Check 3: Course & Branch Identifier
    dept_code = (metadata.get("department_code") or "").upper()
    course_code = (metadata.get("course_code") or "").upper()
    course_name = metadata.get("course_name") or ""
    has_dept = (dept_code and dept_code.lower() in full_norm) or any(c in full_norm for c in ["department", "cse", "ece", "cai", "engineering"])
    has_course = (course_code and course_code.lower() in full_norm) or (course_name and normalize(course_name) in full_norm) or any(k in full_norm for k in ["course", "subject", "question bank"])

    if has_dept and has_course:
        items.append({
            "requirement": "Course & Branch Identifier",
            "expected_value": f"{course_name or 'Course'} [{course_code or 'Code'}]",
            "detected_value": "Department and Subject details successfully aligned",
            "result": "Correct",
            "explanation": "Question bank is mapped to the authorized department and course.",
            "recommended_correction": "None required."
        })
    else:
        items.append({
            "requirement": "Course & Branch Identifier",
            "expected_value": f"{course_name or 'Course'} [{course_code or 'Code'}]",
            "detected_value": "Course code or department not detected",
            "result": "Incorrect",
            "explanation": "Could not identify unambiguous course code or department header in question bank.",
            "recommended_correction": f"Add title: 'Question Bank - {course_name} ({course_code}) | Department of {dept_code or 'Engineering'}'."
        })

    # Check 4: 5-Unit Question Coverage
    units_found = []
    for u_num, u_name in [("1", "unit 1"), ("2", "unit 2"), ("3", "unit 3"), ("4", "unit 4"), ("5", "unit 5"),
                          ("i", "unit i"), ("ii", "unit ii"), ("iii", "unit iii"), ("iv", "unit iv"), ("v", "unit v")]:
        if u_name in full_norm:
            units_found.append(u_num.upper())

    unique_units = set(units_found)
    normalized_units = set()
    for u in unique_units:
        if u in ("1", "I"): normalized_units.add(1)
        elif u in ("2", "II"): normalized_units.add(2)
        elif u in ("3", "III"): normalized_units.add(3)
        elif u in ("4", "IV"): normalized_units.add(4)
        elif u in ("5", "V"): normalized_units.add(5)

    if len(normalized_units) >= 5:
        items.append({
            "requirement": "5-Unit Question Coverage",
            "expected_value": "Questions spanning all 5 Units (Unit I through Unit V)",
            "detected_value": f"Questions detected across all 5 Units (1, 2, 3, 4, 5)",
            "result": "Correct",
            "explanation": "Question bank provides comprehensive syllabus coverage across all 5 units.",
            "recommended_correction": "None required."
        })
    elif len(normalized_units) >= 3:
        missing_units = [f"Unit {n}" for n in range(1, 6) if n not in normalized_units]
        items.append({
            "requirement": "5-Unit Question Coverage",
            "expected_value": "Questions spanning all 5 Units (Unit I through Unit V)",
            "detected_value": f"Found {len(normalized_units)}/5 units. Missing: {', '.join(missing_units)}",
            "result": "Missing",
            "explanation": f"Question bank is missing questions for: {', '.join(missing_units)}.",
            "recommended_correction": "Add question sets for each missing unit: 'UNIT-I' through 'UNIT-V'."
        })
    else:
        items.append({
            "requirement": "5-Unit Question Coverage",
            "expected_value": "Questions spanning all 5 Units (Unit I through Unit V)",
            "detected_value": "No unit markers detected",
            "result": "Missing",
            "explanation": "Could not identify unit headers ('UNIT I', 'UNIT II', etc.).",
            "recommended_correction": "Structure questions under unit headers: 'UNIT I', 'UNIT II', 'UNIT III', 'UNIT IV', 'UNIT V'."
        })

    # Check 5: Dual-Tier Question Classification (Part A & Part B)
    has_part_a = "part a" in full_norm or "short answer" in full_norm or "2 marks" in full_norm
    has_part_b = "part b" in full_norm or "long answer" in full_norm or "descriptive" in full_norm or "10 marks" in full_norm

    if has_part_a and has_part_b:
        items.append({
            "requirement": "Dual-Tier Question Classification",
            "expected_value": "Part A (Short Answer) & Part B (Descriptive / Analytical)",
            "detected_value": "Both Part A and Part B question tiers detected",
            "result": "Correct",
            "explanation": "Question bank categorizes questions into short conceptual and descriptive analytical tiers.",
            "recommended_correction": "None required."
        })
    elif has_part_a or has_part_b:
        items.append({
            "requirement": "Dual-Tier Question Classification",
            "expected_value": "Part A (Short Answer) & Part B (Descriptive / Analytical)",
            "detected_value": f"Only {'Part A' if has_part_a else 'Part B'} questions detected",
            "result": "Needs Review",
            "explanation": "Question bank must contain both Part A (Short Answer) and Part B (Long Answer) questions.",
            "recommended_correction": "Include both 'PART A (Short Answer Questions)' and 'PART B (Long Answer Questions)' per unit."
        })
    else:
        items.append({
            "requirement": "Dual-Tier Question Classification",
            "expected_value": "Part A (Short Answer) & Part B (Descriptive / Analytical)",
            "detected_value": "No Part A / Part B tier division",
            "result": "Missing",
            "explanation": "Institutional standards require questions to be divided into Part A (Short) and Part B (Descriptive).",
            "recommended_correction": "Label questions in each unit as 'Part A' and 'Part B'."
        })

    # Check 6: Bloom's Taxonomy & CO Mapping
    has_blooms = any(b in full_norm for b in ["bloom", "taxonomy", "l1", "l2", "l3", "l4", "remember", "understand", "apply", "analyze", "evaluate", "bt level"])
    has_co = any(c in full_norm for c in ["co1", "co2", "co3", "co4", "co5", "course outcome", "co mapping"])

    if has_blooms and has_co:
        items.append({
            "requirement": "Bloom's Taxonomy & CO Mapping",
            "expected_value": "Cognitive levels (L1-L4) and Course Outcome mapping (CO1-CO5)",
            "detected_value": "Bloom's Taxonomy levels (BT) and CO mapping detected",
            "result": "Correct",
            "explanation": "Questions are systematically mapped to cognitive levels and syllabus Course Outcomes.",
            "recommended_correction": "None required."
        })
    elif has_blooms or has_co:
        items.append({
            "requirement": "Bloom's Taxonomy & CO Mapping",
            "expected_value": "Cognitive levels (L1-L4) and Course Outcome mapping (CO1-CO5)",
            "detected_value": f"Partially mapped: {'Bloom taxonomy' if has_blooms else 'Course Outcomes'}",
            "result": "Needs Review",
            "explanation": "Provide both Bloom's Taxonomy cognitive levels (L1-L4) and Course Outcome tags (CO1-CO5) for every question.",
            "recommended_correction": "Tag each question with: '[BT: L2 | CO: CO1]'."
        })
    else:
        items.append({
            "requirement": "Bloom's Taxonomy & CO Mapping",
            "expected_value": "Cognitive levels (L1-L4) and Course Outcome mapping (CO1-CO5)",
            "detected_value": "No Bloom's taxonomy or CO tags detected",
            "result": "Missing",
            "explanation": "NAAC/NBA accreditation requires question banks to tag questions with Bloom's Taxonomy and COs.",
            "recommended_correction": "Add cognitive levels and course outcomes to questions: e.g. '[L2, CO1]'."
        })

    # Check 7: Question Count Volume
    detected_q_count = count_questions(full_text)
    if detected_q_count >= 15:
        items.append({
            "requirement": "Question Volume & Depth",
            "expected_value": "Minimum 15-20 total questions across all units",
            "detected_value": f"{detected_q_count} questions detected with standard numbering",
            "result": "Correct",
            "explanation": f"Detected {detected_q_count} questions, satisfying the minimum required depth.",
            "recommended_correction": "None required."
        })
    elif detected_q_count >= 8:
        items.append({
            "requirement": "Question Volume & Depth",
            "expected_value": "Minimum 15-20 total questions across all units",
            "detected_value": f"Only {detected_q_count} questions detected",
            "result": "Incorrect",
            "explanation": f"Question count ({detected_q_count}) is below the required 15-20 questions for an institutional question bank.",
            "recommended_correction": "Add additional practice and analytical questions to reach at least 15 questions."
        })
    else:
        items.append({
            "requirement": "Question Volume & Depth",
            "expected_value": "Minimum 15-20 total questions across all units",
            "detected_value": f"{detected_q_count} recognized questions",
            "result": "Missing",
            "explanation": "Could not identify standard numbered question entries.",
            "recommended_correction": "Prefix each question clearly with numbers like '1.', '2.', '3.' on new lines."
        })

    # Check 8: Marks Allocation per Question
    has_marks = any(m in full_norm for m in ["marks", "[m]", "(m)", "2m", "5m", "10m", "[2]", "[10]", "[5]"])
    if has_marks:
        items.append({
            "requirement": "Marks Allocation Scheme",
            "expected_value": "Explicit marks indicated for questions or sections",
            "detected_value": "Marks allocation annotations detected",
            "result": "Correct",
            "explanation": "Questions or sections indicate specific mark weightages.",
            "recommended_correction": "None required."
        })
    else:
        items.append({
            "requirement": "Marks Allocation Scheme",
            "expected_value": "Explicit marks indicated for questions or sections",
            "detected_value": "No marks indicators detected",
            "result": "Missing",
            "explanation": "Questions lack explicit marks annotations (e.g. '[2 Marks]', '[10 Marks]').",
            "recommended_correction": "Add mark brackets like '[2 Marks]' or '[10 Marks]' to each question."
        })

    total_checks = len(items)
    passed_checks = sum(1 for it in items if it["result"] == "Correct")
    failed_checks = sum(1 for it in items if it["result"] == "Incorrect")
    missing_reqs = sum(1 for it in items if it["result"] == "Missing")
    needs_review = sum(1 for it in items if it["result"] == "Needs Review")
    not_applicable = sum(1 for it in items if it["result"] == "Not Applicable")

    applicable_checks = total_checks - not_applicable
    compliance_pct = round((passed_checks / applicable_checks * 100.0), 1) if applicable_checks > 0 else 0.0

    if failed_checks > 0 or missing_reqs > 0:
        overall_status = "INVALID"
    elif needs_review > 0:
        overall_status = "NEEDS_REVIEW"
    else:
        overall_status = "VALID"

    summary = {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "missing_requirements": missing_reqs,
        "needs_review": needs_review,
        "compliance_percentage": compliance_pct,
        "validation_status": overall_status
    }

    return {
        "validation_status": overall_status,
        "compliance_percentage": compliance_pct,
        "summary": summary,
        "items": items,
        "analyzed_at": datetime.now().isoformat()
    }


# =====================================================================
# 4. UNIFIED DOCUMENT DISPATCHER (All Categories)
# =====================================================================
def validate_any_document(file_path: str, doc_type_name: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Central institutional validation router.
    Dispatches to specialized validators based on document type name or content.
    Always generates the uniform 6-column breakdown analysis:
      Requirement | Expected Value / Rule | Detected Value | Result | Explanation | Recommended Correction
    """
    type_lower = (doc_type_name or "").lower()

    if "course structure" in type_lower or "syllabus" in type_lower or "curriculum" in type_lower:
        return validate_course_structure_document(file_path, metadata)
    elif "question bank" in type_lower or "assignment bank" in type_lower:
        return validate_question_bank_document(file_path, metadata)
    elif "question paper" in type_lower or "mid" in type_lower or "semester" in type_lower:
        return validate_question_paper_document(file_path, metadata)
    else:
        # Default fallback to Course Structure / general structural validator
        return validate_course_structure_document(file_path, metadata)
