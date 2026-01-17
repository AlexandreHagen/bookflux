from __future__ import annotations

from typing import List


def ocr_pdf(pdf_path: str, ocr_lang: str = "eng", dpi: int = 300) -> List[str]:
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "OCR deps missing. Install pdf2image, pytesseract, and system binaries "
            "(poppler, tesseract)."
        ) from exc

    images = convert_from_path(pdf_path, dpi=dpi)
    page_texts: List[str] = []
    for image in images:
        page_texts.append(pytesseract.image_to_string(image, lang=ocr_lang) or "")

    if not any(text.strip() for text in page_texts):
        raise ValueError("OCR produced no text. Check --ocr-lang or image quality.")

    return page_texts
