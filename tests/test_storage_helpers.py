import re

from app.services.storage import build_safe_object_name


def test_build_safe_object_name_removes_path_and_unsafe_characters():
    object_name = build_safe_object_name("../Meu Arquivo!.txt")

    assert re.match(r"^[a-f0-9]{32}_Meu_Arquivo_.txt$", object_name)
    assert ".." not in object_name
    assert "/" not in object_name
    assert "\\" not in object_name


def test_build_safe_object_name_falls_back_for_empty_names():
    object_name = build_safe_object_name("   ")

    assert re.match(r"^[a-f0-9]{32}_document$", object_name)
