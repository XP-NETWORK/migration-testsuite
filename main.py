from elrond import ElrondHelper
from polkadot import PolkadotHelper
from validator import ValidatorHelper
from config import Config, ValidatorRuntimeConfig
from typing import Tuple

from tests import liquidity_test, egld_test


def setup(config: Config) -> Tuple[PolkadotHelper, ElrondHelper]:
    validator = ValidatorHelper(config.validator.project)
    polka = PolkadotHelper.setup(config.polkadot)
    print()
    elrd = ElrondHelper.setup(config.elrond)
    print()

    print("dumping validator config...")
    rtconf = ValidatorRuntimeConfig(
        xnode=config.polkadot.uri,
        elrond_node=config.elrond.uri,
        private_key=config.elrond.sender,
        elrond_sender=elrd.sender.address.bech32(),
        elrond_minter=elrd.contract.address.bech32(),
        xp_freezer=polka.contract.contract_address,
        elrond_ev_socket=config.elrond.event_socket
    )
    validator.dump_config(rtconf)
    print("starting validator...")
    validator.spawn()

    return polka, elrd


def main() -> None:
    config = Config()
    polka, elrd = setup(config)

    cont = True

    while cont:
        print("""Available Tests:
1. Liquidity (Polkadot Units -> Elrond)
2. EGLD (Elrond EGOLD -> Polkadot)""")

        choice = input("Select test: ")
        if choice == "1":
            liquidity_test(polka, elrd)
        elif choice == "2":
            egld_test(elrd, polka)
        else:
            print("Invalid choice!")

        cont = input("Continue?(y/n) ").lower() == "y"


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
