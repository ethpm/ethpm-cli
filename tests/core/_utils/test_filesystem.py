import pytest

from ethpm_cli._utils.filesystem import atomic_replace


@pytest.fixture
def original(tmp_path):
    original = tmp_path / "original.txt"
    original.write_text("original")
    return original


def test_atomic_replace_will_replace_file(original):
    with atomic_replace(original) as original_file:
        original_file.write("update")

    assert "update" in original.read_text()
    assert "original" not in original.read_text()


def test_atomic_replace_is_atomic(original):
    try:
        with atomic_replace(original) as original_file:
            original_file.write("update")
            raise Exception
    except Exception:
        pass

    assert "original" in original.read_text()
    assert "update" not in original.read_text()
