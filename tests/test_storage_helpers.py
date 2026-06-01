import re
import unittest

from app.services.storage import build_safe_object_name


class StorageHelperTests(unittest.TestCase):
    def test_build_safe_object_name_removes_path_and_unsafe_characters(self):
        object_name = build_safe_object_name("../Meu Arquivo!.txt")

        self.assertRegex(object_name, r"^[a-f0-9]{32}_Meu_Arquivo_.txt$")
        self.assertNotIn("..", object_name)
        self.assertNotIn("/", object_name)
        self.assertNotIn("\\", object_name)

    def test_build_safe_object_name_falls_back_for_empty_names(self):
        object_name = build_safe_object_name("   ")

        self.assertTrue(re.match(r"^[a-f0-9]{32}_document$", object_name))
