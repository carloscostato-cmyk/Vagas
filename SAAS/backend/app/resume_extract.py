from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Literal

from docx import Document
from pypdf import PdfReader


ResumeKind = Literal["pdf", "docx", "txt", "unknown"]


@dataclass(frozen=True)
class ExtractedResume:
    kind: ResumeKind
    text: str


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", " ").replace("\r", "\n")
    lines = [ln.strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines).strip()


def guess_kind(filename: str | None, content_type: str | None) -> ResumeKind:
    name = (filename or "").lower().strip()
    ctype = (content_type or "").lower().strip()

    if name.endswith(".pdf") or ctype == "application/pdf":
        return "pdf"
    if name.endswith(".docx") or ctype in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ):
        return "docx"
    if name.endswith(".txt") or ctype.startswith("text/"):
        return "txt"
    return "unknown"


def extract_text(kind: ResumeKind, data: bytes) -> ExtractedResume:
    if kind == "pdf":
        reader = PdfReader(BytesIO(data))
        parts: list[str] = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                parts.append(t)
        return ExtractedResume(kind=kind, text=_normalize_text("\n".join(parts)))

    if kind == "docx":
        doc = Document(BytesIO(data))
        parts = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
        return ExtractedResume(kind=kind, text=_normalize_text("\n".join(parts)))

    if kind == "txt":
        try:
            return ExtractedResume(kind=kind, text=_normalize_text(data.decode("utf-8")))
        except UnicodeDecodeError:
            return ExtractedResume(kind=kind, text=_normalize_text(data.decode("latin-1", errors="ignore")))

    # Fallback: best-effort decode; the client can retry with correct format.
    try:
        text = data.decode("utf-8", errors="ignore")
    except Exception:
        text = ""
    return ExtractedResume(kind="unknown", text=_normalize_text(text))

