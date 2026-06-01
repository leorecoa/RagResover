import anyio

from app.services.ingestion import IngestionService


def test_process_document_splits_text_into_chunks_with_metadata():
    service = IngestionService()
    content = ("RagResover transforma documentos privados em respostas com fontes.\n" * 80)

    chunks = anyio.run(
        service.process_document,
        "manual.md",
        content,
        {"source": "manual.md", "content_type": "text/markdown"},
    )

    assert len(chunks) > 1
    assert all(chunk.page_content.strip() for chunk in chunks)
    assert all(chunk.metadata["source"] == "manual.md" for chunk in chunks)
    assert all(chunk.metadata["content_type"] == "text/markdown" for chunk in chunks)
    assert chunks[0].page_content in content
