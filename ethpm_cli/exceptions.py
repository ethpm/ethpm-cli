class EthpmCliError(Exception):
    """
    Base class for all EthPM CLI errors.
    """

    pass


class InstallError(EthpmCliError):
    """
    Raised when there's a failure to install something.
    """

    pass


class UriNotSupportedError(EthpmCliError):
    """
    Raised when a given uri does not fit a supported format.
    """

    pass


class BlockNotFoundError(EthpmCliError):
    """
    Raised when a block is not available on the provided web3 instance.
    """

    pass


class ValidationError(EthpmCliError):
    """
    Raised when a command line args is not valid.
    """

    pass
