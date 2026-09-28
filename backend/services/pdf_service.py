import pymupdf as fitz
from pathlib import Path
from typing import Dict, List, Any

def extract_pdf_data(file_path: str) -> Dict[str, Any]:
    """
    Extracts structural components from a PDF file using PyMuPDF (fitz).
    Returns total pages, full text, per-page text and blocks, header area, and footer lines.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file does not exist: {file_path}")

    doc = fitz.open(str(path))
    pages_data = []
    full_text_parts = []
    first_page_header = ""
    footer_lines = []

    try:
        total_pages = len(doc)
        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_text = page.get_text("text") or ""
            full_text_parts.append(page_text)

            # Get structured text blocks: (x0, y0, x1, y1, text, block_no, block_type)
            blocks = page.get_text("blocks")
            clean_blocks = []
            for b in blocks:
                if len(b) >= 5 and b[4].strip():
                    clean_blocks.append({
                        "bbox": (b[0], b[1], b[2], b[3]),
                        "text": b[4].strip()
                    })

            lines = [line.strip() for line in page_text.splitlines() if line.strip()]
            if page_idx == 0:
                # Top 10 non-empty lines on page 1 typically form the header
                first_page_header = "\n".join(lines[:10])

            if lines:
                # Last 2 lines on page typically represent footers/notes
                footer_lines.extend(lines[-2:])

            pages_data.append({
                "page_number": page_idx + 1,
                "text": page_text,
                "blocks": clean_blocks,
                "line_count": len(lines)
            })

        full_text = "\n".join(full_text_parts)

        return {
            "total_pages": total_pages,
            "full_text": full_text,
            "pages": pages_data,
            "header_preview": first_page_header,
            "footer_preview": "\n".join(footer_lines),
        }
    finally:
        doc.close()
