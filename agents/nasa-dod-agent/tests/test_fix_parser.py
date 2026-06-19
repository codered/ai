import pytest

from nasa_dod_agent.fix_parser import FixParser
from nasa_dod_agent.models import Patch


def test_parse_valid_patches():
    raw = """
### Patch 1: Fix unbounded loop
**File:** src/main.py
**Search:**
```python
while True:
    process()
```
**Replace:**
```python
MAX_ITER = 1000
for _ in range(MAX_ITER):
    process()
```
"""
    parser = FixParser()
    patches, errors = parser.parse(raw)
    assert len(patches) == 1
    assert patches[0].file_path == "src/main.py"
    assert "range(MAX_ITER)" in patches[0].replace_block
    assert len(errors) == 0


def test_parse_malformed_returns_error():
    raw = "### Patch\n**File:**\nNo actual patch body here."
    parser = FixParser()
    patches, errors = parser.parse(raw)
    assert len(patches) == 0
    assert len(errors) >= 1


def test_apply_patch_to_file(temp_project):
    target = temp_project / "main.py"
    target.write_text("while True:\n    process()\n")

    patch = Patch(
        file_path=str(target),
        description="Fix loop",
        search_block="while True:\n    process()",
        replace_block="for _ in range(1000):\n    process()",
    )
    parser = FixParser()
    parser.apply_patch(patch)
    assert "range(1000)" in target.read_text()


def test_apply_patch_rejects_truncated_search_block(temp_project):
    """Regression test: an LLM once handed us search_block='func TestIsEven_maxInt_minu'
    (cut off mid-identifier, missing 's(t *testing.T) {'). A naive str.replace happily
    "succeeded" and spliced the new function in while leaving the orphaned tail
    's(t *testing.T) {' behind, corrupting the file into invalid Go. Applying a search
    block that doesn't land on a token boundary must be rejected instead.
    """
    target = temp_project / "main.go"
    target.write_text("func TestIsEven_maxInt_minus(t *testing.T) {\n\tdoStuff()\n}\n")

    patch = Patch(
        file_path=str(target),
        description="rewrite test",
        search_block="func TestIsEven_maxInt_minu",
        replace_block="func TestIsEven_maxInt_minus(t *testing.T) {\n\tdoOtherStuff()\n}",
    )
    parser = FixParser()
    with pytest.raises(ValueError, match="truncated"):
        parser.apply_patch(patch)
    # File must be untouched, not corrupted.
    assert target.read_text() == "func TestIsEven_maxInt_minus(t *testing.T) {\n\tdoStuff()\n}\n"


def test_apply_patch_rejects_ambiguous_multiple_matches(temp_project):
    target = temp_project / "main.py"
    target.write_text("x = 1\nx = 1\n")

    patch = Patch(
        file_path=str(target),
        description="fix",
        search_block="x = 1",
        replace_block="x = 2",
    )
    parser = FixParser()
    with pytest.raises(ValueError, match="2 locations"):
        parser.apply_patch(patch)
    assert target.read_text() == "x = 1\nx = 1\n"


def test_ambiguous_match_error_tells_llm_how_to_fix_it(temp_project):
    """Regression test: a real run got stuck for 10 iterations because the
    LLM kept resubmitting the same non-unique Search block (a repeated
    `if err != nil { return nil }` idiom in readconfig.go) without ever
    being told that the fix is to add more surrounding context. The error
    message itself must say so, since it's the only thing fed back to the
    LLM on the next iteration.
    """
    target = temp_project / "main.py"
    target.write_text("x = 1\nx = 1\n")

    patch = Patch(
        file_path=str(target),
        description="fix",
        search_block="x = 1",
        replace_block="x = 2",
    )
    parser = FixParser()
    with pytest.raises(ValueError, match="more context|surrounding"):
        parser.apply_patch(patch)
