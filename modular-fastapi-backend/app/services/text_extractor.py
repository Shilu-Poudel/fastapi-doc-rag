import io
from typing import Union
from fastapi import UploadFile
import requests
import os

LLAMA_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY", "")

async def extract_text_from_file(file: UploadFile) -> str:
    """
    Extract text from an uploaded PDF or TXT file.

    - Uses PyMuPDF (pymupdf) for PDFs if available (lazy import).
    - Falls back to llama-parse HTTP API if pymupdf is not installed and LLAMA_API_KEY is set.
    - Raises RuntimeError with actionable message if neither option is available.
    """
    content = await file.read()
    if file.content_type == "text/plain":
        return content.decode(errors="ignore")

    # Lazy import PyMuPDF to avoid import-time failures if it's not installed.
    try:
        import fitz  # PyMuPDF (module name is 'fitz')
    except ModuleNotFoundError:
        # If PyMuPDF not installed, try llama-parse fallback if configured.
        if not LLAMA_API_KEY:
            raise RuntimeError(
                "PyMuPDF (pymupdf) is required to parse PDFs but is not installed. "
                "Install it with: pip install pymupdf"
            )
        resp = requests.post(
            "https://api.llama.cloud/parse",
            headers={"Authorization": f"Bearer {LLAMA_API_KEY}"},
            files={"file": ("upload.pdf", content)},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("text", "")

    # Use PyMuPDF to parse PDF
    try:
        pdf_stream = io.BytesIO(content)
        doc = fitz.open(stream=pdf_stream.read(), filetype="pdf")
        text_chunks = [page.get_text() for page in doc]
        return "\n".join(text_chunks)
    except Exception as exc:
        # If PyMuPDF fails for this PDF, attempt llama-parse if available.
        if LLAMA_API_KEY:
            resp = requests.post(
                "https://api.llama.cloud/parse",
                headers={"Authorization": f"Bearer {LLAMA_API_KEY}"},
                files={"file": ("upload.pdf", content)},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("text", "")
        raise RuntimeError(f"Failed to extract PDF text: {exc}") from exc