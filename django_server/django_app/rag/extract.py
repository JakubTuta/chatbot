import io

import docx
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {"txt", "md", "pdf", "docx"}


class UnsupportedFileTypeError(ValueError):
    pass


def extract_text(filename: str, raw: bytes) -> str:
    """Pulls plain text out of an uploaded file. Raises
    UnsupportedFileTypeError for anything not in SUPPORTED_EXTENSIONS —
    callers turn that into a 400 rather than silently ingesting garbage.
    """
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type: .{extension or '?'}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )

    if extension in ("txt", "md"):
        return raw.decode("utf-8", errors="replace")

    if extension == "pdf":
        reader = PdfReader(io.BytesIO(raw))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    # docx
    document = docx.Document(io.BytesIO(raw))
    return "\n\n".join(p.text for p in document.paragraphs if p.text)
