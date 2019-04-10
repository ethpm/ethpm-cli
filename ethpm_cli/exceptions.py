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
