from argparse import Namespace
from ethpm_cli.config import Config
import logging
import json
from ethpm_cli._utils.logger import cli_logger
from ethpm_cli.exceptions import InstallError
from web3.auto.infura import w3
from eth_utils import to_checksum_address, to_hex

logger = logging.getLogger("ethpm_cli.verify")

# verify deployments of a manifest
# verify a registry's package:contract_type against an address
# # i.e. zeppelin owned is installed @ 0x123

def verify_contract(args: Namespace, config: Config) -> None:
    package, contract_type = args.contract_type.split(":")
    runtime_bytecode = get_contract_type_verification_data(
        package, contract_type, config
    )
    actual_bytecode = to_hex(w3.eth.getCode(to_checksum_address(args.address)))
    if runtime_bytecode == actual_bytecode:
        logger.info("Valid: Contract code found at %s matches contract type: %s located in the %s package.", args.address, contract_type, package)
    else:
        logger.info("Invalid: Contract code found at %s does not match the contract type: %s located in the %s package.", args.address, contract_type, package)


def get_contract_type_verification_data(package: str, contract_type: str, config: Config) -> str:
    manifest = json.loads((config.ethpm_dir / package / "manifest.json").read_text())
    if contract_type not in manifest["contract_types"].keys():
        raise InstallError(
            f"{contract_type} not available in {package} package. Available contract types include: {list(manifest['contract_types'].keys())}."
        )
    runtime_bytecode = manifest["contract_types"][contract_type]["runtime_bytecode"][
        "bytecode"
    ]
    if runtime_bytecode == "0x":
        raise InstallError
    return runtime_bytecode
