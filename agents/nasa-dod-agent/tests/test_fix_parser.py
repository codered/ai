from nasa_dod_agent.fix_parser import FixParser
from nasa_dod_agent.models import Patch, PatchError


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
