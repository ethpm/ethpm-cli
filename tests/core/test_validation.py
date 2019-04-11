from argparse import Namespace
from pathlib import Path

import pytest

from ethpm_cli.exceptions import InstallError, UriNotSupportedError, ValidationError
from ethpm_cli.validation import validate_cli_args


@pytest.fixture
def args():
    namespace = Namespace()
    setattr(namespace, "uri", "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW")
    setattr(namespace, "packages_dir", None)
    setattr(namespace, "local_ipfs", None)
    setattr(namespace, "alias", None)
    return namespace


@pytest.mark.parametrize("alias", ("_invalid", "1nvalid"))
def test_validate_cli_args_rejects_invalid_aliases(alias, args):
    setattr(args, "alias", alias)

    with pytest.raises(ValidationError):
        validate_cli_args(args)


@pytest.mark.parametrize(
    "uri",
    (
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
        "ercXXX://0x6b5DA3cA4286Baa7fBaf64EEEE1834C7d430B729/owned?version=1.0.0",
        "https://api.github.com/repos/ethpm/py-ethpm/git/blobs/a7232a93f1e9e75d606f6c1da18aa16037e03480",  # noqa: E501
    ),
)
def test_validate_cli_args_validates_supported_uris(uri, args):
    setattr(args, "uri", uri)

    assert validate_cli_args(args) is None


@pytest.mark.parametrize(
    "uri",
    (
        "www.google.com",
        "bzz://da6adeeb4589d8652bbe5679aae6b6409ec85a20e92a8823c7c99e25dba9493d",
    ),
)
def test_validate_cli_args_rejects_unsupported_uris(uri, args):
    setattr(args, "uri", uri)

    with pytest.raises(UriNotSupportedError):
        validate_cli_args(args)


def test_validate_cli_args_validates_absolute_ethpm_dir_paths(args, tmpdir):
    ethpm_dir = Path(tmpdir) / "ethpm_packages"
    ethpm_dir.mkdir()
    setattr(args, "packages_dir", ethpm_dir)

    assert validate_cli_args(args) is None


def test_validate_cli_args_validates_relative_paths_to_cwd(args, tmpdir, monkeypatch):
    p = Path(tmpdir)
    ethpm_dir = p / "ethpm_packages"
    ethpm_dir.mkdir()
    monkeypatch.chdir(p)
    setattr(args, "packages_dir", Path("./ethpm_packages"))

    assert validate_cli_args(args) is None


def test_validate_cli_args_rejects_invalid_absolute_paths(args, tmpdir):
    invalid_path = Path(tmpdir) / "ethpm_packages"
    setattr(args, "packages_dir", invalid_path)

    with pytest.raises(InstallError):
        validate_cli_args(args)


def test_validate_cli_args_rejects_invalid_relative_paths(args, tmpdir, monkeypatch):
    p = Path(tmpdir)
    ethpm_dir = p / "ethpm_packages"
    ethpm_dir.mkdir()
    monkeypatch.chdir(p)
    setattr(args, "packages_dir", Path("./invalid"))

    with pytest.raises(InstallError):
        validate_cli_args(args)
