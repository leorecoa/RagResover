from app.repositories.documents import normalize_metadata, serialize_vector


def test_serialize_vector_formats_pgvector_literal():
    assert serialize_vector([1, 2.5, -0.3]) == "[1,2.5,-0.3]"


def test_serialize_vector_preserves_null_embedding():
    assert serialize_vector(None) is None


def test_normalize_metadata_accepts_dicts():
    assert normalize_metadata({"source": "file.md"}) == {"source": "file.md"}


def test_normalize_metadata_parses_json_object_strings():
    assert normalize_metadata('{"source": "file.md"}') == {"source": "file.md"}


def test_normalize_metadata_returns_empty_dict_for_invalid_values():
    assert normalize_metadata("not-json") == {}
    assert normalize_metadata("[1, 2]") == {}
    assert normalize_metadata(None) == {}
