from typing import Union
from chains.elrond import ElrondHelper
from chains.web3_h import Web3Helper
from chains.polkadot import PolkadotHelper
from config import Config
from setup import setup_elrd, setup_web3

from tests.elrd import elrd_tests
from tests.w3 import w3_tests


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
