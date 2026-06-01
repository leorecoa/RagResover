import unittest

from app.repositories.documents import normalize_metadata, serialize_vector


class RepositoryHelperTests(unittest.TestCase):
    def test_serialize_vector_formats_pgvector_literal(self):
        self.assertEqual(serialize_vector([1, 2.5, -0.3]), "[1,2.5,-0.3]")

    def test_serialize_vector_preserves_null_embedding(self):
        self.assertIsNone(serialize_vector(None))

    def test_normalize_metadata_accepts_dicts(self):
        self.assertEqual(normalize_metadata({"source": "file.md"}), {"source": "file.md"})

    def test_normalize_metadata_parses_json_object_strings(self):
        self.assertEqual(normalize_metadata('{"source": "file.md"}'), {"source": "file.md"})

    def test_normalize_metadata_returns_empty_dict_for_invalid_values(self):
        self.assertEqual(normalize_metadata("not-json"), {})
        self.assertEqual(normalize_metadata("[1, 2]"), {})
        self.assertEqual(normalize_metadata(None), {})
