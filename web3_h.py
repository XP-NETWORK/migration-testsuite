from __future__ import annotations
from typing import Any, Type
from eth_account.account import Account, LocalAccount
from eth_typing.evm import ChecksumAddress

from web3.contract import Contract
from web3.types import TxParams, TxReceipt, Wei

import consts
import json
import subprocess

from pathlib import Path

from config import Web3Config
from web3 import Web3


class Web3Helper:
    def __init__(
        self,
        provider: str,
        sender: str,
        project_folder: str,
    ):
        self.w3 = Web3(Web3.WebsocketProvider(provider))
        self.project = project_folder
        self.sender: LocalAccount = Account.from_key(sender)

    @classmethod
    def setup(cls, config: Web3Config) -> Web3Helper:
        print("Web3 Setup")
        w3 = cls(
          config.uri,
          config.sender,
          config.project,
        )

        w3.compile()

        print(f"deployed XPNET: {w3.deploy_erc20()}")
        print(f"deployed minter: {w3.deploy_minter()}")

        w3.erc20_transfer_ownership(w3.minter.address)

        return w3

    def compile(self) -> None:
        subprocess.run(
            ["npx", "hardhat", "compile"],
            check=True,
            cwd=self.project
        )

    def deploy_contract(self, jsonf: Path, *args: Any) -> Type[Contract]:
        with open(jsonf, "rb") as contract:
            data = json.load(contract)

        abi = data["abi"]
        bytecode = data["bytecode"]
        Contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        tx = Contract.constructor(*args).buildTransaction()

        return self.w3.eth.contract(  # type: ignore
            address=self.send_tx(tx).contractAddress,  # type: ignore
            abi=abi
        )

    def send_tx_i(self, sender: LocalAccount, tx: TxParams) -> TxReceipt:
        tx["nonce"] = self.w3.eth.get_transaction_count(
            sender.address
        )

        signed = self.w3.eth.account.sign_transaction(
            tx, private_key=sender.key
        )

        hs = self.w3.eth.send_raw_transaction(signed.rawTransaction)

        return self.w3.eth.wait_for_transaction_receipt(hs)

    def send_tx(self, tx: TxParams) -> TxReceipt:
        return self.send_tx_i(self.sender, tx)

    def deploy_erc20(self) -> str:
        contract = Path(consts.WEB3_XPNET_JSON.format(
            project=self.project
        ))

        self.xpnet = self.deploy_contract(contract)

        return str(self.xpnet.address)

    def deploy_minter(self) -> str:
        contract = Path(consts.WEB3_MINTER_JSON.format(
            project=self.project
        ))

        self.minter = self.deploy_contract(
            contract, [self.sender.address], 1, self.xpnet.address
        )

        return str(self.minter.address)

    def erc20_transfer_ownership(self, addr: ChecksumAddress) -> None:
        call = self.xpnet.functions.transferOwnership(
            addr
        ).buildTransaction()

        self.send_tx(call)

    def erc20_check_bal(self, addr: ChecksumAddress) -> int:
        return int(
            self.xpnet.functions.balanceOf(
                addr
            ).call()
        )

    def withdraw_tokens(
        self,
        sender: LocalAccount,
        destination: str,
        value: int
    ) -> TxReceipt:
        call = self.minter.functions.withdraw(
            destination, value=value
        ).buildTransaction()

        return self.send_tx_i(sender, call)

    def freeze_ht(
        self,
        sender: LocalAccount,
        destination: str,
        value: int
    ) -> TxReceipt:
        params = TxParams(value=Wei(value))
        call = self.minter.functions.freeze(
            destination,
        ).buildTransaction(params)

        return self.send_tx_i(sender, call)
