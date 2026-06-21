from unittest.mock import patch

import pytest

from nasa_dod_agent.chunker import FILE_LEVEL, chunk_file


def test_chunk_go_file_splits_functions_and_file_level(tmp_path):
    target = tmp_path / "sample.go"
    target.write_text(
        "package sample\n"
        "\n"
        "import \"fmt\"\n"
        "\n"
        "// Divide returns a / b.\n"
        "func Divide(a, b int) int {\n"
        "\treturn a / b\n"
        "}\n"
        "\n"
        "func main() {\n"
        "\tfmt.Println(Divide(4, 2))\n"
        "}\n"
    )

    chunks = chunk_file(target, "go")

    names = [c.name for c in chunks]
    assert names == ["Divide", "main", FILE_LEVEL]


def test_chunk_includes_leading_doc_comment_in_function_chunk(tmp_path):
    target = tmp_path / "sample.go"
    target.write_text(
        "package sample\n"
        "\n"
        "// Divide returns a / b.\n"
        "func Divide(a, b int) int {\n"
        "\treturn a / b\n"
        "}\n"
    )

    chunks = chunk_file(target, "go")
    divide_chunk = next(c for c in chunks if c.name == "Divide")

    assert "// Divide returns a / b." in divide_chunk.text
    assert divide_chunk.start_line == 3


def test_chunk_file_level_excludes_function_bodies(tmp_path):
    target = tmp_path / "sample.go"
    target.write_text(
        "package sample\n"
        "\n"
        "const MaxRetries = 3\n"
        "\n"
        "func Foo() {\n"
        "\tx := 1\n"
        "\t_ = x\n"
        "}\n"
    )

    chunks = chunk_file(target, "go")
    file_level = next(c for c in chunks if c.name == FILE_LEVEL)

    assert "const MaxRetries" in file_level.text
    assert "x := 1" not in file_level.text


def test_chunk_python_methods_and_module_functions(tmp_path):
    target = tmp_path / "sample.py"
    target.write_text(
        "import os\n"
        "\n"
        "class Foo:\n"
        "    def bar(self):\n"
        "        pass\n"
        "\n"
        "def baz():\n"
        "    pass\n"
    )

    chunks = chunk_file(target, "python")

    names = sorted(c.name for c in chunks)
    assert names == sorted(["bar", "baz", FILE_LEVEL])


def test_chunk_does_not_descend_into_nested_functions(tmp_path):
    target = tmp_path / "sample.py"
    target.write_text(
        "def outer():\n"
        "    def inner():\n"
        "        pass\n"
        "    return inner\n"
    )

    chunks = chunk_file(target, "python")

    names = [c.name for c in chunks]
    assert names == ["outer"]
    assert "def inner" in chunks[0].text


def test_chunk_c_function_name_extracted_from_declarator(tmp_path):
    target = tmp_path / "sample.c"
    target.write_text("int add(int a, int b) { return a + b; }\n")

    chunks = chunk_file(target, "c")

    assert [c.name for c in chunks] == ["add"]


def test_chunk_unsupported_language_returns_whole_file(tmp_path):
    target = tmp_path / "sample.rb"
    target.write_text("def foo\n  1\nend\n")

    chunks = chunk_file(target, "ruby")

    assert len(chunks) == 1
    assert chunks[0].name == FILE_LEVEL
    assert chunks[0].text == target.read_text()


def test_chunk_file_with_no_functions_returns_whole_file(tmp_path):
    target = tmp_path / "consts.go"
    target.write_text("package sample\n\nconst MaxRetries = 3\n")

    chunks = chunk_file(target, "go")

    assert len(chunks) == 1
    assert chunks[0].name == FILE_LEVEL


def test_chunk_parser_failure_falls_back_to_whole_file(tmp_path):
    target = tmp_path / "sample.go"
    target.write_text("package sample\n\nfunc Foo() {}\n")

    with patch("nasa_dod_agent.chunker.get_parser", side_effect=RuntimeError("boom")):
        chunks = chunk_file(target, "go")

    assert len(chunks) == 1
    assert chunks[0].name == FILE_LEVEL
    assert chunks[0].text == target.read_text()
