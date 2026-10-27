
from pathlib import Path

import pymupdf


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from all pages of a PDF file.
    """

    file_path = Path(pdf_path)

    if not file_path.is_file():
        raise FileNotFoundError(
            f"PDF file not found: {file_path}"
        )

    if file_path.suffix.lower() != ".pdf":
        raise ValueError("Please provide a PDF file.")

    extracted_pages = []

    # Open PDF and read each page
    with pymupdf.open(str(file_path)) as document:
        for page_number, page in enumerate(document, start=1):
            page_text = page.get_text("text").strip()

            if page_text:
                extracted_pages.append(page_text)

            print(
                f"Page {page_number}: "
                f"{len(page_text)} characters extracted"
            )

    return "\n\n".join(extracted_pages)


if __name__ == "__main__":
    # Test using a PDF placed in the data folder
    project_root = Path(__file__).resolve().parents[3]

    pdf_path = project_root / "data" / "sample_policy.pdf"

    text = extract_text_from_pdf(str(pdf_path))

    print("\n--- EXTRACTED PDF TEXT ---\n")
    print(text[:2000])
