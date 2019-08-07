class BaseEthpmCliError(Exception):
    """
    Base class for all EthPM CLI errors.
    """

    pass


class InstallError(BaseEthpmCliError):
    """
    Raised when there's a failure to install something.
    """

    pass


class UriNotSupportedError(BaseEthpmCliError):
    """
    Raised when a given uri does not fit a supported format.
    """

    pass


class BlockNotFoundError(BaseEthpmCliError):
    """
    Raised when a block is not available on the provided web3 instance.
    """

    pass


class ValidationError(BaseEthpmCliError):
    """
    Raised when a command line args is not valid.
    """

    pass


class AmbigiousFileSystem(BaseEthpmCliError):
    """
    Raised when the file system paths are unclear.
    """

    pass


class AuthorizationError(BaseEthpmCliError):
    """
    Raised when there is insufficient authorization to perform a task.
    """

    pass


class EtherscanKeyNotFound(BaseEthpmCliError):
    """
    Raised when no Etherscan API key is set as environment variable.
    """

    pass


class ContractNotVerified(BaseEthpmCliError):
    """
    Raised when a request to Etherscan points to an unverified contract.
    """

    pass
