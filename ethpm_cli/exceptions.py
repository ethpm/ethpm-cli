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
