import re
from typing import Dict, List, Any, Tuple
from datetime import datetime
from backend.services.pdf_service import extract_pdf_data

def normalize(text: str) -> str:
    """Normalizes whitespace and converts text to lowercase."""
    return re.sub(r"\s+", " ", (text or "").lower()).strip()

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
        # Match only after the initial start_marker length
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

    # Fallback to numbering lines if regex matched nothing
    if not all_matches:
        line_patterns = re.findall(r"(?m)^\s*\d{1,2}\s*[\.\)]", text)
        return len(line_patterns)

    return len(all_matches)

def evaluate_requirement(req: dict, pdf_data: Dict[str, Any]) -> Tuple[bool, str | None]:
    """
    Evaluates a single structural requirement against extracted PDF structural features.
    Returns (passed: bool, reason: str | None).
    """
    req_name = req.get("requirement_name", "").strip()
    req_type = normalize(req.get("requirement_type", ""))
    req_val = (req.get("requirement_value") or "").strip()

    name_norm = normalize(req_name)
    full_text = pdf_data.get("full_text", "")
    full_norm = normalize(full_text)
    header_preview = normalize(pdf_data.get("header_preview", ""))
    footer_preview = normalize(pdf_data.get("footer_preview", ""))

    # 1. Header / Page presence
    if any(k in req_type for k in ["header", "college header"]) or "college header" in name_norm or "college name" in name_norm:
        if req_val:
            val_norm = normalize(req_val)
            if val_norm in header_preview or val_norm in full_norm[:1500]:
                return True, None
            # Check keywords if general
            if any(term in val_norm for term in ["college", "institute", "technology", "university"]):
                if any(term in header_preview for term in ["college", "institute", "technology", "university"]):
                    return True, None
            return False, f"Expected header '{req_val}' was not detected in top section."
        else:
            # Check if header area has substantive text
            if len(header_preview) > 10:
                return True, None
            return False, "College/Document header was not detected in the top section."

    # 2. Footer presence
    if any(k in req_type for k in ["footer", "footer presence"]) or "footer" in name_norm:
        if len(footer_preview.strip()) > 3:
            return True, None
        return False, "Footer or ending section was not detected."

    # 3. Question Count check
    if any(k in req_type for k in ["question_count", "required count", "count"]):
        # Extract target count
        count_match = re.search(r"\d+", req_val or req_name)
        if not count_match:
            return True, None  # Cannot evaluate without target count
        expected_count = int(count_match.group())

        # Determine target section text
        target_text = full_text
        if "part a" in name_norm:
            target_text = extract_section_text(full_text, "Part A", ["Part B", "Unit 2", "Unit 3"])
        elif "part b" in name_norm:
            target_text = extract_section_text(full_text, "Part B", ["Unit 2", "Unit 3", "Unit 4", "Unit 5"])
        elif "unit 1" in name_norm:
            target_text = extract_section_text(full_text, "Unit 1", ["Unit 2"])
        elif "unit 2" in name_norm:
            target_text = extract_section_text(full_text, "Unit 2", ["Unit 3"])
        elif "unit 3" in name_norm:
            target_text = extract_section_text(full_text, "Unit 3", ["Unit 4"])
        elif "unit 4" in name_norm:
            target_text = extract_section_text(full_text, "Unit 4", ["Unit 5"])
        elif "unit 5" in name_norm:
            target_text = extract_section_text(full_text, "Unit 5", [])

        detected_count = count_questions(target_text)

        # Allow matching or reasonable presence
        if detected_count == expected_count:
            return True, None
        elif detected_count > 0:
            # Check if text mentions the count e.g. "Answer all 5 questions" or "5 x 2"
            if str(expected_count) in normalize(target_text):
                return True, None
            return False, f"Expected {expected_count} questions in section, detected {detected_count}."
        else:
            return False, f"Section requires {expected_count} questions, but no questions were detected."

    # 4. Marks pattern check
    if any(k in req_type for k in ["marks", "marks pattern"]):
        target_marks = re.search(r"\d+", req_val or req_name)
        expected_marks = target_marks.group() if target_marks else None

        target_text = full_norm
        if "part a" in name_norm:
            target_text = normalize(extract_section_text(full_text, "Part A", ["Part B"]))
        elif "part b" in name_norm:
            target_text = normalize(extract_section_text(full_text, "Part B", []))

        # Check for marks patterns: e.g. "2 marks", "10 marks", "2m", "10m", "[2]", "[10]"
        if expected_marks:
            patterns = [
                rf"\b{expected_marks}\s*marks?\b",
                rf"\b{expected_marks}\s*m\b",
                rf"\[\s*{expected_marks}\s*m?\s*\]",
                rf"\(\s*{expected_marks}\s*m?\s*\)",
                rf"\b\d+\s*[xX*]\s*{expected_marks}\b"
            ]
            if any(re.search(p, target_text) for p in patterns):
                return True, None
            return False, f"Required marks pattern ({expected_marks} marks) was not found in section."
        else:
            if "mark" in target_text or "m" in target_text:
                return True, None
            return False, "Required marks distribution was not detected."

    # 5. Section / Part structure presence
    if any(k in req_type for k in ["section", "section presence", "part a structure", "part b structure"]):
        section_term = req_name
        if "part a" in name_norm:
            section_term = "part a"
        elif "part b" in name_norm:
            section_term = "part b"
        elif "unit 1" in name_norm:
            section_term = "unit 1"
        elif "unit 2" in name_norm:
            section_term = "unit 2"
        elif "unit 3" in name_norm:
            section_term = "unit 3"
        elif "unit 4" in name_norm:
            section_term = "unit 4"
        elif "unit 5" in name_norm:
            section_term = "unit 5"

        pattern = rf"\b{re.escape(section_term)}\b"
        if re.search(pattern, full_norm):
            return True, None
        return False, f"Required structural section '{req_name}' was not detected."

    # 6. Heading presence
    if "heading" in req_type or "heading" in name_norm:
        # Search for heading name in text
        # If it's "Unit 1 Heading" or similar:
        unit_match = re.search(r"unit\s*([1-5ivx]+)", name_norm)
        if unit_match:
            u_num = unit_match.group(1)
            patterns = [
                rf"\bunit\s*[-–:]?\s*{re.escape(u_num)}\b",
                rf"\bunit\s*[-–:]?\s*i+\b"
            ]
            if any(re.search(p, full_norm) for p in patterns):
                return True, None
            return False, f"Required heading for Unit {u_num} was not found."

        if req_val and normalize(req_val) in full_norm:
            return True, None
        if name_norm in full_norm:
            return True, None
        return False, f"Required heading '{req_name}' was not found."

    # 7. Arrangement / Ordering
    if "arrangement" in req_type or "ordering" in req_type or "arrangement" in name_norm:
        # Check that Part A appears before Part B, or Units appear in sequential order
        pos_part_a = full_norm.find("part a")
        pos_part_b = full_norm.find("part b")
        if "part b arrangement" in name_norm or "part b" in name_norm:
            if pos_part_b != -1 and (pos_part_a == -1 or pos_part_b > pos_part_a):
                return True, None
            return False, "Part B structural arrangement does not follow Part A."
        if "part a arrangement" in name_norm or "part a" in name_norm:
            if pos_part_a != -1:
                return True, None
            return False, "Part A structural arrangement was not detected."
        return True, None

    # 8. General Text / Field presence
    target_terms = []
    if req_val:
        target_terms.append(normalize(req_val))

    # Add standard domain keywords based on requirement name
    keyword_map = {
        "b.tech": [r"\bb\.?\s*tech\b", r"\bbachelor of technology\b"],
        "semester": [r"\bsemester\b", r"\bsem\b", r"\bi{1,2}\s*year\b"],
        "examination type": [r"\bexamination\b", r"\bmid\b", r"\bsemester examination\b"],
        "subject name": [r"\bsubject\b", r"\bcourse\b"],
        "subject code": [r"\bsubject\s*code\b", r"\bcourse\s*code\b", r"\bcode\b"],
        "course code": [r"\bcourse\s*code\b", r"\bsubject\s*code\b", r"\bcode\b"],
        "course name": [r"\bcourse\s*name\b", r"\bsubject\b", r"\bcourse\b"],
        "branch": [r"\bbranch\b", r"\bdiscipline\b", r"\bcse\b", r"\bece\b", r"\bmech\b"],
        "department": [r"\bdepartment\b", r"\bdept\b"],
        "time": [r"\btime\b", r"\bhours?\b", r"\bhrs\b", r"\bmins?\b"],
        "maximum marks": [r"\bmaximum\s*marks\b", r"\bmax\.?\s*marks\b", r"\bmax\b"],
        "body": [r"\bpart\b", r"\bunit\b", r"\bquestions?\b"],
        "part a": [r"\bpart\s*a\b"],
        "part b": [r"\bpart\s*b\b"],
    }

    # Check if keyword map has specific regex patterns
    matched_pattern = False
    for k, patterns in keyword_map.items():
        if k in name_norm:
            if any(re.search(p, full_norm) for p in patterns):
                matched_pattern = True
                break

    if matched_pattern:
        return True, None

    # Check if requirement_name or requirement_value literal is present
    if req_val and normalize(req_val) in full_norm:
        return True, None

    if name_norm in full_norm:
        return True, None

    # As a fallback for "Topics" in Course Structure:
    if "topics" in name_norm:
        unit_match = re.search(r"unit\s*([1-5ivx]+)", name_norm)
        if unit_match:
            u_text = extract_section_text(full_text, f"Unit {unit_match.group(1)}", ["Unit 2", "Unit 3", "Unit 4", "Unit 5", "Reference", "Text Books"])
            if len(u_text.strip()) > 20:
                return True, None
            return False, f"Topics under Unit {unit_match.group(1)} were not found."

    return False, f"Required element '{req_name}' was not detected in the document."

def analyze_document_structure(file_path: str, format_record: dict, requirements: List[dict]) -> Dict[str, Any]:
    """
    Executes structural analysis of an uploaded PDF against Auditor-defined format requirements.
    Separates:
      1. PDF extraction
      2. Feature extraction
      3. Requirement comparison
      4. Strict ACCEPTED / REJECTED decision
    """
    pdf_data = extract_pdf_data(file_path)
    requirement_results = []
    all_mandatory_passed = True

    # Sort requirements by display order
    sorted_reqs = sorted(requirements, key=lambda x: x.get("display_order", 1))

    for req in sorted_reqs:
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
