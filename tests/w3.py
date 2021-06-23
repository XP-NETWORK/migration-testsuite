import time
from eth_account.account import Account
import stdiomask
from eth_typing.evm import ChecksumAddress
from substrateinterface.base import Keypair

from web3.main import Web3

from chains.polkadot import PolkadotHelper
from chains.web3_h import Web3Helper


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
    assert(polka.send_tokens(polka.sender, destination, value).is_success)

    target = cur_b + value
    wait_erc20_bal_added(w3, dest_check_addr, target)

    print(f"{destination} new balance: {target}")


def liquidity_w32p(w3: Web3Helper) -> None:
    destination = input("Enter destination polkadot address: ")
    value = int(input("Enter XP Token value(pico): "))
    pk = stdiomask.getpass("Enter sender's(w3) private key(protected): ")

    sender = Account.from_key(pk)
    cur_b = w3.erc20_check_bal(sender.address)
    print(f"{sender.address} cur balance: {cur_b}")

    tx = w3.withdraw_tokens(sender, destination, value)
    print(f"TX Hash: {tx['blockHash'].hex()}")

    wait_erc20_bal_added(w3, sender.address, cur_b - value)

    input("Press enter when you receive tokens in polkadot")


def ht_w32p(w3: Web3Helper) -> None:
    destination = input("Enter destination polkadot address: ")
    value = int(input("Enter HT value(wei): "))
    pk = stdiomask.getpass("Enter sender's(w3) private key(protected): ")

    sender = Account.from_key(pk)
    tx = w3.freeze_ht(sender, destination, value)
    print(f"TX Hash: {tx['blockHash'].hex()}")

    input("Please enter once you have received confirmation from validator\n")


def ht_p2w3(polka: PolkadotHelper) -> None:
    destination = input("Enter w3 address(H160): ")
    value = int(input("Enter Wrapper HT amount: "))
    addr = input("Enter sender address: ")
    pk = stdiomask.getpass("Enter sender's private key(protected): ")

    sender = Keypair.create_from_private_key(pk, ss58_address=addr)

    assert(polka.unfreeze_wrap(sender, destination, value).is_success)

    input("Press enter once you have received the HT!\n")


def liquidity_test(polka: PolkadotHelper, w3: Web3Helper) -> None:
    print("Send Test (polkadot(Unit) -> Web3)")
    liquidity_p2w3(polka, w3)

    input("Press enter to continue")

    print("Unfreeze Test (Web3(XPNET ERC20) -> Polkadot)")
    liquidity_w32p(w3)


def ht_test(w3: Web3Helper, polka: PolkadotHelper) -> None:
    print("Send Test (W3 -> Polkadot)")
    ht_w32p(w3)

    input("Press enter to continue\n")

    print("Unfreeze Test (Polkadot -> W3)")
    ht_p2w3(polka)


def w3_tests(polka: PolkadotHelper, w3: Web3Helper) -> None:
    print("""Available Tests:
1. Liquidity (Polkadot Units -> Web3)
2. WEI (Web3 -> Polkadot)""")

    choice = input("Select test: ")
    if choice == "1":
        liquidity_test(polka, w3)
    elif choice == "2":
        ht_test(w3, polka)
    else:
        print("Invalid choice!")
