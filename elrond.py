from __future__ import annotations
from config import ElrondConfig
from erdpy.interfaces import IElrondProxy
import consts
import time
import requests

from typing import Any, Optional, cast

from erdpy import config
from erdpy.proxy import ElrondProxy
from erdpy.accounts import Account, Address
from erdpy.contracts import SmartContract
from erdpy.projects import ProjectRust
from erdpy.transactions import Transaction


class ElrondHelper:
    def __init__(
        self,
        proxy: str,
        events: str,
        sender_pem: str,
        project_folder: str
    ):
        self.proxy = ElrondProxy(proxy)
        self.proxy_uri = proxy
        self.event_uri = events
        self.sender = Account(pem_file=sender_pem)
        self.project = ProjectRust(project_folder)
        self.sender.sync_nonce(self.proxy)

    @classmethod
    def setup(cls, config: ElrondConfig) -> ElrondHelper:
        print("Elrond Setup")
        elrd = cls(
            config.uri,
            config.event_rest,
            config.sender,
            config.project
        )

        print("Issuing esdt...")
        print(f"Issued esdt: {elrd.prepare_esdt()}")

        print("deplyoing minter...")
        print(f"deployed contract: {elrd.deploy_sc().bech32()}")

        print("setting up contract perms...")
        print(f"perm setup done! tx: {elrd.setup_sc_perms().hash}")

        return elrd

    def wait_transaction_done(self, tx_hash: str) -> Any:
        time.sleep(3)
        uri = consts.ELROND_TX_URI.format(proxy=self.proxy_uri, tx=tx_hash)
        while data := requests.get(uri):
            res = data.json()
            if res["code"] != "successful":
                raise Exception(f"failed to execute tx: {tx_hash}, \
                                error: {res['error']}")

            res = res["data"]["transaction"]
            if res["status"] == "pending":
                time.sleep(5)
                continue
            elif res["status"] != "success":
                raise Exception(f"failed to execute tx: {tx_hash}, \
                                status: {res['transaction']['status']}")

            return res

    def prepare_esdt(self) -> str:
        tx = Transaction()
        tx.value = str(consts.ELROND_ESDT_VALUE)
        tx.sender = self.sender.address.bech32()
        tx.receiver = consts.ELROND_ESDT_SC_ADDR
        tx.gasPrice = consts.ELROND_GAS_PRICE
        tx.gasLimit = consts.ELROND_ESDT_GASL
        tx.data = consts.ELROND_ESDT_ISSUE_DATA
        tx.chainID = str(self.proxy.get_chain_id())
        tx.version = config.get_tx_version()

        self.sender.sync_nonce(self.proxy)
        tx.nonce = self.sender.nonce

        tx.sign(self.sender)
        tx.send(cast(IElrondProxy, self.proxy))
        for res in self.wait_transaction_done(tx.hash)["smartContractResults"]:
            if res["sender"] != consts.ELROND_ESDT_SC_ADDR:  # noqa: E501
                continue

            self.esdt_hex = str(
                res["data"]
            ).split("@")[1]
            if len(self.esdt_hex) < len("XPNET")*2:
                continue

            break

        self.esdt_str = bytes.fromhex(self.esdt_hex).decode("utf-8")

        return self.esdt_str

    def deploy_sc(self, clean: bool = False) -> Address:
        if not self.esdt_hex:
            raise Exception("Deploy called before prepare_esdt!")

        if clean:
            self.project.clean()
        self.project.build()

        contract = SmartContract(bytecode=self.project.get_bytecode())
        self.sender.sync_nonce(self.proxy)
        tx = contract.deploy(
            self.sender,
            consts.ELROND_CONTRACT_ARGS.format(
                esdt=self.esdt_hex,
                sender=self.sender.address.hex().replace("0x", "")
            ).split(),
            consts.ELROND_GAS_PRICE,
            consts.ELROND_ESDT_GASL,
            value=0,
            chain=str(self.proxy.get_chain_id()),
            version=config.get_tx_version()
        )
        tx.send(cast(IElrondProxy, self.proxy))
        self.wait_transaction_done(tx.hash)

        self.contract = contract

        return contract.address

    def setup_sc_perms(self) -> Transaction:
        if not self.contract:
            raise Exception("Setup SC called before deploy!")

        tx = Transaction()
        tx.value = str(0)
        tx.sender = self.sender.address.bech32()
        tx.receiver = consts.ELROND_ESDT_SC_ADDR
        tx.gasPrice = consts.ELROND_GAS_PRICE
        tx.gasLimit = consts.ELROND_ESDT_GASL
        tx.data = consts.ELROND_SETROLE_DATA.format(
            esdt=self.esdt_hex,
            sc_addr=self.contract.address.hex().replace("0x", "")
        )
        tx.chainID = str(self.proxy.get_chain_id())
        tx.version = config.get_tx_version()

        self.sender.sync_nonce(self.proxy)
        tx.nonce = self.sender.nonce

        tx.sign(self.sender)
        tx.send(cast(IElrondProxy, self.proxy))
        self.wait_transaction_done(tx.hash)

        return tx

    def check_esdt_bal(self, bch32_addr: str) -> Optional[int]:
        try:
            uri = consts.ELROND_ESDT_BAL_URI.format(
                proxy=self.proxy_uri,
                addr=bch32_addr,
                token=self.esdt_str
            )

            return int(requests.get(uri)
                       .json()["data"]["tokenData"]["balance"])
        except Exception as e:
            print("WARN: Can't check esdt balance. returning None. err:", e)
            return None

    def wait_esdt_bal_added(self, bch32_addr: str, added: int,
                            prev: Optional[int] = None) -> Optional[int]:
        cur_b = prev if prev else self.check_esdt_bal(bch32_addr)
        if cur_b is None:
            return None

        target = cur_b + added
        while self.check_esdt_bal(bch32_addr) != target:
            time.sleep(2.5)

        return target

    def unfreeze(self, signer: Account, to: str, value: int) -> Transaction:
        signer.sync_nonce(self.proxy)

        tx = self.contract.execute(
            caller=signer,
            function="ESDTTransfer",
            value=0,
            arguments=[
                f"0x{self.esdt_hex}",
                value,
                f'0x{bytes("withdraw", "ascii").hex()}',
                f'0x{bytes(to, "ascii").hex()}'
            ],
            gas_price=consts.ELROND_GAS_PRICE,
            gas_limit=consts.ELROND_ESDT_GASL,
            chain=str(self.proxy.get_chain_id()),
            version=config.get_tx_version()
        )

        tx.send(cast(IElrondProxy, self.proxy))
        self.wait_transaction_done(tx.hash)

        return tx

    def send_tokens(self, signer: Account, to: str, value: int) -> Transaction:
        signer.sync_nonce(self.proxy)

        tx = self.contract.execute(
            caller=signer,
            function="freezeSend",
            value=value,
            arguments=[
                f"0x{bytes(to, 'ascii').hex()}"
            ],
            gas_price=consts.ELROND_GAS_PRICE,
            gas_limit=consts.ELROND_ESDT_GASL,
            chain=str(self.proxy.get_chain_id()),
            version=config.get_tx_version()
        )

        tx.send(cast(IElrondProxy, self.proxy))
        self.wait_transaction_done(tx.hash)

        return tx
