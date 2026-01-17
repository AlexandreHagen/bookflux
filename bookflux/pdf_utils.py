from __future__ import annotations

from typing import List

import pdfplumber


def extract_text(pdf_path: str, use_ocr: bool = False, ocr_lang: str = "eng") -> List[str]:
    if use_ocr:
        from .ocr_utils import ocr_pdf

        return ocr_pdf(pdf_path, ocr_lang=ocr_lang)

    page_texts: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_texts.append(page.extract_text() or "")

    if not any(text.strip() for text in page_texts):
        raise ValueError("No text extracted from PDF. Try --ocr for scanned PDFs.")

    return page_texts
