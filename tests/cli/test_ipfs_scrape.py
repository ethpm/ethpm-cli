import pexpect

from ethpm_cli.constants import ETHPM_CLI_VERSION


def test_ipfs_scrape(tmp_path):
    ipfs_dir = tmp_path / "ipfs"
    ipfs_dir.mkdir()
    child = pexpect.spawn(f"ethpm scrape --ipfs-dir {ipfs_dir} --start-block 1")
    child.expect(
        f"A command line tool for the Ethereum Package Manager. v{ETHPM_CLI_VERSION}\r\n"
    )
    child.expect("\r\n")
    child.expect("Scraping from block 1.\r\n")
    child.expect("Blocks 1-5001 scraped. 0 VersionRelease events found.\r\n")
