import time
from eth_typing.evm import ChecksumAddress

from web3.main import Web3

from polkadot import PolkadotHelper
from web3_h import Web3Helper


def wait_erc20_bal_added(
    w3: Web3Helper,
    addr: ChecksumAddress,
    target: int
) -> None:
    while w3.erc20_check_bal(addr) != target:
        time.sleep(2.5)


def liquidity_p2w3(polka: PolkadotHelper, w3: Web3Helper) -> None:
    destination = input("Enter destination web3 address(H160): ")
    value = int(input("Enter XP Token value(pico): "))

    dest_check_addr = Web3.toChecksumAddress(destination)
    cur_b = w3.erc20_check_bal(dest_check_addr)
    print(f"{destination} current balance: {cur_b}")
    assert(polka.send_tokens(destination, value).is_success)

    target = cur_b + value
    wait_erc20_bal_added(w3, dest_check_addr, target)

    print(f"{destination} new balance: {target}")


def liquidity_test(polka: PolkadotHelper, w3: Web3Helper) -> None:
    print("Send Test (polkadot(Unit) -> Web3)")
    liquidity_p2w3(polka, w3)

    input("Press enter to continue")

    print("Unfreeze Test (Web3(XPNET ERC20) -> Polkadot)")
    # liqudity_w32p(w3)


def w3_tests(polka: PolkadotHelper, w3: Web3Helper) -> None:
    print("""Available Tests:
1. Liquidity (Polkadot Units -> Web3)""")

    choice = input("Select test: ")
    if choice == "1":
        liquidity_test(polka, w3)
    else:
        print("Invalid choice!")
