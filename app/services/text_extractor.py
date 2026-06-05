import fitz
from fastapi import UploadFile

SUPPORTED_CONTENT_TYPES = {"application/pdf", "text/plain"}


async def extract_text(file: UploadFile) -> str:
    """Extract raw text from an uploaded PDF or TXT file."""
    content = await file.read()

    if file.content_type == "text/plain":
        return content.decode("utf-8", errors="ignore")

    if file.content_type == "application/pdf":
        with fitz.open(stream=content, filetype="pdf") as doc:
            return "\n".join(page.get_text() for page in doc)

    raise ValueError(f"Unsupported content type: {file.content_type}")
