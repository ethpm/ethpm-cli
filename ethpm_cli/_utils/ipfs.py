from ethpm.backends.ipfs import BaseIPFSBackend, InfuraIPFSBackend, LocalIPFSBackend


def get_ipfs_backend(ipfs: bool = False) -> BaseIPFSBackend:
    if ipfs:
        return LocalIPFSBackend()
    return InfuraIPFSBackend()
