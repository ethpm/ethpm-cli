from eth_utils import to_text

from ethpm.backends.ipfs import LocalIPFSBackend
from ethpm.utils.ipfs import is_ipfs_uri


def write_sources_to_disk(manifest, parent_dir):
    (parent_dir / "src").mkdir()
    for path, source in manifest["sources"].items():
        # todo: support all schemes
        if is_ipfs_uri(source):
            source_contents = to_text(
                LocalIPFSBackend().fetch_uri_contents(source)
            ).rstrip("\n")
        else:
            source_contents = source
        target_file = parent_dir / "src" / path
        target_dir = target_file.parent
        if not target_dir.is_dir():
            target_dir.mkdir(parents=True)
        target_file.touch()
        target_file.write_text(source_contents)
