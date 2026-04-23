"""Lightweight PDF text extraction for uploaded resumes."""
import os


def extract_pdf_text(path):
    try:
        import pdfplumber
    except ImportError:
        return ""
    if not path or not os.path.exists(path):
        return ""
    try:
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages[:6]:  # first 6 pages is plenty
                t = page.extract_text() or ""
                text_parts.append(t)
        return "\n".join(text_parts)[:8000]
    except Exception as exc:
        print(f"[file_parser] PDF extraction failed: {exc}")
        return ""
