import pexpect

from ethpm_cli.main import ENTRY_DESCRIPTION


def test_ipfs_scrape(tmp_path):
    ipfs_dir = tmp_path / "ipfs"
    ipfs_dir.mkdir()
    child = pexpect.spawn(f"ethpm scrape --ipfs-dir {ipfs_dir} --start-block 1")
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect("Scraping from block 1.\r\n")
    child.expect("Blocks 1-5001 scraped. 0 VersionRelease events found.\r\n")
