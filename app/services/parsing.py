import io
from typing import Any

from docx import Document as DocxDocument
from langchain_core.documents import Document
from pypdf import PdfReader


PDF_CONTENT_TYPES = {"application/pdf"}
DOCX_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}
TEXT_CONTENT_TYPES = {"text/plain", "text/markdown", "application/json"}


class DocumentParsingError(ValueError):
    """Raised when a supported document cannot be parsed into text."""


class UnsupportedDocumentTypeError(ValueError):
    """Raised when no parser exists for the uploaded content type."""


def build_base_metadata(
    *,
    file_name: str,
    storage_path: str,
    content_type: str,
    size_bytes: int,
) -> dict[str, Any]:
    return {
        "source": file_name,
        "path": storage_path,
        "content_type": content_type,
        "size_bytes": size_bytes,
    }


def parse_file_to_documents(
    file_name: str,
    file_bytes: bytes,
    content_type: str,
    storage_path: str,
) -> list[Document]:
    metadata = build_base_metadata(
        file_name=file_name,
        storage_path=storage_path,
        content_type=content_type,
        size_bytes=len(file_bytes),
    )

    if content_type in TEXT_CONTENT_TYPES:
        return parse_text(file_bytes=file_bytes, metadata=metadata)
    if content_type in PDF_CONTENT_TYPES:
        return parse_pdf(file_bytes=file_bytes, metadata=metadata)
    if content_type in DOCX_CONTENT_TYPES:
        return parse_docx(file_bytes=file_bytes, metadata=metadata)

    raise UnsupportedDocumentTypeError(f"Tipo de arquivo nao suportado: {content_type}")


def parse_text(*, file_bytes: bytes, metadata: dict[str, Any]) -> list[Document]:
    text = file_bytes.decode("utf-8", errors="replace").strip()
    if not text:
        raise DocumentParsingError("Arquivo nao contem texto extraivel.")
    return [Document(page_content=text, metadata=metadata)]


def parse_pdf(*, file_bytes: bytes, metadata: dict[str, Any]) -> list[Document]:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        page_count = len(reader.pages)
    except Exception as exc:
        raise DocumentParsingError("Arquivo PDF invalido, corrompido ou ilegivel.") from exc

    documents: list[Document] = []
    for page_index, page in enumerate(reader.pages, start=1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception as exc:
            raise DocumentParsingError(
                f"Nao foi possivel extrair texto da pagina {page_index} do PDF."
            ) from exc
        if not text:
            continue

        documents.append(
            Document(
                page_content=text,
                metadata={**metadata, "page": page_index, "page_count": page_count},
            )
        )

    if not documents:
        raise DocumentParsingError("Arquivo PDF nao contem texto extraivel.")

    return documents


def parse_docx(*, file_bytes: bytes, metadata: dict[str, Any]) -> list[Document]:
    try:
        docx = DocxDocument(io.BytesIO(file_bytes))
    except Exception as exc:
        raise DocumentParsingError("Arquivo DOCX invalido, corrompido ou ilegivel.") from exc

    documents: list[Document] = []
    current_section: str | None = None

    for paragraph_index, paragraph in enumerate(docx.paragraphs, start=1):
        text = paragraph.text.strip()
        if not text:
            continue

        style_name = getattr(paragraph.style, "name", "") or ""
        if style_name.lower().startswith("heading"):
            current_section = text

        paragraph_metadata = {**metadata, "paragraph": paragraph_index}
        if current_section:
            paragraph_metadata["section"] = current_section

        documents.append(Document(page_content=text, metadata=paragraph_metadata))

    if not documents:
        raise DocumentParsingError("Arquivo DOCX nao contem texto extraivel.")

    return documents
