import pytest


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory for tests."""
    return tmp_path
