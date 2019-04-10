from ethpm.backends.ipfs import BaseIPFSBackend, LocalIPFSBackend, InfuraIPFSBackend


def get_ipfs_backend(ipfs: bool = None) -> BaseIPFSBackend:
    if ipfs:
        return LocalIPFSBackend()
    return InfuraIPFSBackend()
