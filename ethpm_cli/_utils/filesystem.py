import contextlib
import filecmp
import os
from pathlib import Path
import shutil
import tempfile
from typing import IO, TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    from ethpm_cli.config import Config


def check_dir_trees_equal(dir1: str, dir2: str) -> bool:
    """
    Compare two directories recursively. Files in each directory are
    assumed to be equal if their names and contents are equal.

    @param dir1: First directory path
    @param dir2: Second directory path

    @return: True if the directory trees are the same and
        there were no errors while accessing the directories or files,
        False otherwise.
   """

    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if (
        len(dirs_cmp.left_only) > 0
        or len(dirs_cmp.right_only) > 0  # noqa: W503
        or len(dirs_cmp.funny_files) > 0  # noqa: W503
    ):
        print("right_only: ", dirs_cmp.right_only)
        print("left_only: ", dirs_cmp.left_only)
        return False
    (_, mismatch, errors) = filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False
    )
    if len(mismatch) > 0 or len(errors) > 0:
        print("mismatch: ", mismatch)
        print("errors: ", errors)
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not check_dir_trees_equal(new_dir1, new_dir2):
            return False
    return True


@contextlib.contextmanager
def atomic_replace(path: Path) -> Generator[IO[Any], None, None]:
    """
    Usage:

    with atomic_replace(original: Path) as file:
        file.write("new text")
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file_path = Path(tmpdir) / path.name
        tmp_file_path.touch()
        with tmp_file_path.open(mode="w+") as tmpfile:
            yield tmpfile
        shutil.copyfile(tmp_file_path, path)


def is_package_installed(package_name: str, config: "Config") -> bool:
    if not (config.ethpm_dir / package_name).is_dir():
        return False
    if not (config.ethpm_dir / package_name / "manifest.json").is_file():
        return False
    return True
