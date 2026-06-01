import anyio

from app.repositories.documents import DocumentRepository


class FakeMappings:
    def all(self):
        return []


class FakeResult:
    def mappings(self):
        return FakeMappings()


class FakeSession:
    def __init__(self):
        self.statement = None
        self.params = None

    async def execute(self, statement, params):
        self.statement = statement
        self.params = params
        return FakeResult()


def test_search_similar_chunks_applies_threshold_and_metadata_filters():
    session = FakeSession()
    repository = DocumentRepository(session)

    async def call_repository():
        return await repository.search_similar_chunks(
            embedding=[0.1, 0.2],
            limit=10,
            score_threshold=0.74,
            metadata_filters={"source": "manual.pdf", "page": 1},
        )

    results = anyio.run(call_repository)

    assert results == []
    assert "dc.metadata @> CAST(:metadata_filters AS jsonb)" in str(session.statement)
    assert "score_threshold" in str(session.statement)
    assert session.params["score_threshold"] == 0.74
    assert session.params["metadata_filters"] == '{"source": "manual.pdf", "page": 1}'
