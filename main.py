import dataclasses
from typing import Union
from elrond import ElrondHelper
from web3_h import Web3Helper
from polkadot import PolkadotHelper
from validator import ValidatorHelper
from config import (
    Config,
    ElrondValidatorRuntimeConfig, Web3ValidatorRuntimeConfig
)

from tests.elrd import elrd_tests
from tests.w3 import w3_tests


def setup_web3(polka: PolkadotHelper, config: Config) -> Web3Helper:
    validator = ValidatorHelper(config.validator.project)
    print()
    w3 = Web3Helper.setup(config.web3)
    print()

    print("dumping validator config...")
    rtconf = Web3ValidatorRuntimeConfig(
        xnode=config.polkadot.uri,
        w3_node=config.web3.uri,
        w3_pk=config.web3.sender,
        w3_minter=w3.minter.address,
        xp_freezer=polka.contract.contract_address
    )
    validator.dump_config(dataclasses.asdict(rtconf))
    print("starting validator...")
    validator.spawn()

    return w3


def setup_elrd(polka: PolkadotHelper, config: Config) -> ElrondHelper:
    validator = ValidatorHelper(config.validator.project)
    print()
    elrd = ElrondHelper.setup(config.elrond)
    print()

    print("dumping validator config...")
    rtconf = ElrondValidatorRuntimeConfig(
        xnode=config.polkadot.uri,
        elrond_node=config.elrond.uri,
        private_key=config.elrond.sender,
        elrond_sender=elrd.sender.address.bech32(),
        elrond_minter=elrd.contract.address.bech32(),
        xp_freezer=polka.contract.contract_address,
        elrond_ev_socket=config.elrond.event_socket
    )
    validator.dump_config(dataclasses.asdict(rtconf))
    print("starting validator...")
    validator.spawn()

    return elrd


def main() -> None:
    config = Config()
    print("""Available Chains:
1. Elrond
2. HECO
""")

    helper: Union[ElrondHelper, Web3Helper]
    choice = input("Select chain: ")
    if choice == "1":
        polka = PolkadotHelper.setup(config.polkadot, "./workaround.json")
        test = elrd_tests
        helper = setup_elrd(polka, config)
    elif choice == "2":
        polka = PolkadotHelper.setup(config.polkadot, "./workaround_w3.json")
        test = w3_tests
        helper = setup_web3(polka, config)
    else:
        print("Invalid choice!")
        return

    cont = True

    while cont:
        test(polka, helper)  # type: ignore

        cont = input("Continue?(y/n) ").lower() == "y"


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
