from __future__ import annotations
import subprocess
from config import ElrondConfig
from erdpy.interfaces import IElrondProxy
import consts.elrond as consts
import base64
import time
import itertools
import requests

from typing import Any, Dict, List, Optional, Tuple, cast

from erdpy import config
from erdpy.proxy import ElrondProxy
from erdpy.accounts import Account, Address
from erdpy.contracts import SmartContract
from erdpy.transactions import Transaction


# https://github.com/ElrondNetwork/elrond-sdk/blob/master/erdpy/wallet/pem.py#L16
def parse_pem(pem_data: str) -> Tuple[bytes, bytes]:
    lines = pem_data.splitlines()
    keys_lines = [list(key_lines) for is_next_key, key_lines in
                  itertools.groupby(lines, lambda line: "-----" in line)
                  if not is_next_key]

    keys = ["".join(key_lines) for key_lines in keys_lines]

    key_base64 = keys[0]
    key_hex = base64.b64decode(key_base64).decode()
    key_bytes = bytes.fromhex(key_hex)

    seed = key_bytes[:32]
    pubkey = key_bytes[32:]
    return seed, pubkey


# https://github.com/ElrondNetwork/elrond-sdk/blob/master/erdpy/accounts.py#L54-L56
def account(pem_data: str) -> Account:
    acc = Account()
    seed, pub = parse_pem(pem_data)
    acc.private_key_seed = seed.hex()
    acc.address = Address(pub)  # type: ignore

    return acc


class ElrondHelper:
    def __init__(
        self,
        proxy: str,
        events: str,
        sender_pem: str,
        project: str,
        swap_project: str,
        esdt_cost: int
    ):
        self.proxy = ElrondProxy(proxy)
        self.proxy_uri = proxy
        self.event_uri = events
        self.sender = Account(pem_file=sender_pem)
        self.project = project
        self.swap_project = swap_project
        self.esdt_cost = esdt_cost
        self.sender.sync_nonce(self.proxy)
        self.contract = SmartContract()
        self.contract_swap = SmartContract()

    def cache_dict(self) -> Dict[str, str]:
        res = dict()
        res["esdt_str"] = self.esdt_str
        res["esdt_nft_str"] = self.esdt_nft_str
        res["esdt_swap_str"] = self.swap_token
        res["contract_addr"] = self.contract.address.bech32()
        res["contract_swap_addr"] = self.contract_swap.address.bech32()

        return res

    @classmethod
    def load_cache(cls, config: ElrondConfig,
                   cache: Dict[str, str]) -> ElrondHelper:
        elrd = cls(
            config.uri,
            config.event_rest,
            config.sender,
            config.project,
            config.swap_project,
            config.esdt_cost
        )

        elrd.esdt_str = cache["esdt_str"]
        elrd.esdt_hex = bytes(elrd.esdt_str, 'utf-8').hex()
        elrd.esdt_nft_str = cache["esdt_nft_str"]
        elrd.esdt_nft_hex = bytes(elrd.esdt_nft_str, 'utf-8').hex()
        elrd.swap_token = cache["esdt_swap_str"]
        elrd.swap_token_hex = bytes(elrd.swap_token, 'utf-8').hex()
        elrd.contract = SmartContract(address=cache["contract_addr"])  # type: ignore # noqa: E501
        elrd.contract_swap = SmartContract(address=cache["contract_swap_addr"])  # type: ignore # noqa: E501

        return elrd

    @classmethod
    def setup(cls, config: ElrondConfig) -> ElrondHelper:
        print("Elrond Setup")
        elrd = cls(
            config.uri,
            config.event_rest,
            config.sender,
            config.project,
            config.swap_project,
            config.esdt_cost
        )

        print("Issuing esdt...")
        print(f"Issued esdt: {elrd.prepare_esdt()}")

        print("Issuing nft esdt...")
        print(f"Issued nft esdt: {elrd.prepare_esdt_nft()}")

        print("deploying egld swap...")
        elrd.contract_swap = elrd.deploy_sc([], elrd.swap_project)
        print(f"deployed egld swap contract: \
{elrd.contract_swap.address.bech32()}")

        print("isseing swap esdt")
        elrd.prepare_egld_swap_esdt()
        print(f"Issued swap esdt: {elrd.swap_token}")

        print("deplyoing minter...")
        elrd.contract = elrd.deploy_sc(
            consts.CONTRACT_ARGS.format(
                esdt=elrd.esdt_hex,
                esdt_nft=elrd.esdt_nft_hex,
                esdt_swap=elrd.swap_token.encode('utf-8').hex(),
                sender=elrd.sender.address.hex().replace("0x", "")
            ).split(),
            elrd.project
        )
        print(f"deployed contract: {elrd.contract.address.bech32()}")

        print("setting up contract perms...")
        esdt_data = consts.SETROLE_DATA.format(
            esdt=elrd.esdt_hex,
            sc_addr=elrd.contract.address.hex().replace("0x", "")
        )
        print(f"esdt perm setup done! tx: {elrd.setup_sc_perms(esdt_data).hash}")  # noqa: E501

        esdt_nft_data = consts.SETROLE_NFT_DATA.format(
            esdt=elrd.esdt_nft_hex,
            sc_addr=elrd.contract.address.hex().replace("0x", "")
        )
        print(f"esdt nft perm setup done! tx: {elrd.setup_sc_perms(esdt_nft_data).hash}")  # noqa: E501

        return elrd

    def wait_transaction_done(self, tx_hash: str) -> Any:
        uri = consts.TX_URI.format(proxy=self.proxy_uri, tx=tx_hash)
        while True:
            data = requests.get(uri)
            res = data.json()
            if res["error"] and res["error"] == "transaction not found":
                time.sleep(5)
                continue
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
        tx = Transaction()  # type: ignore
        tx.value = str(self.esdt_cost)
        tx.sender = self.sender.address.bech32()
        tx.receiver = consts.ESDT_SC_ADDR
        tx.gasPrice = consts.GAS_PRICE
        tx.gasLimit = consts.ESDT_GASL
        tx.data = consts.ESDT_ISSUE_DATA
        tx.chainID = str(self.proxy.get_chain_id())  # type: ignore
        tx.version = config.get_tx_version()

        self.sender.sync_nonce(self.proxy)
        tx.nonce = self.sender.nonce

        tx.sign(self.sender)
        tx.send(cast(IElrondProxy, self.proxy))
        time.sleep(10)
        for res in self.wait_transaction_done(tx.hash)["smartContractResults"]:
            if res["sender"] != consts.ESDT_SC_ADDR:  # noqa: E501
                continue

            self.esdt_hex = str(
                res["data"]
            ).split("@")[-1]
            if len(self.esdt_hex) < len("XPNET")*2:
                continue

            break

        self.esdt_str = bytes.fromhex(self.esdt_hex).decode("utf-8")
        if "out of funds" in self.esdt_str:
            raise Exception("Invalid ESDT Issuance value!")

        return self.esdt_str

    def prepare_esdt_nft(self) -> str:
        tx = Transaction()  # type: ignore
        tx.value = str(self.esdt_cost)
        tx.sender = self.sender.address.bech32()
        tx.receiver = consts.ESDT_SC_ADDR
        tx.gasPrice = consts.GAS_PRICE
        tx.gasLimit = consts.ESDT_GASL
        tx.data = consts.ESDT_NFT_ISSUE_DATA
        tx.chainID = str(self.proxy.get_chain_id())  # type: ignore
        tx.version = config.get_tx_version()

        self.sender.sync_nonce(self.proxy)
        tx.nonce = self.sender.nonce

        tx.sign(self.sender)
        tx.send(cast(IElrondProxy, self.proxy))
        time.sleep(10)
        for res in self.wait_transaction_done(tx.hash)["smartContractResults"]:
            if res["sender"] != consts.ESDT_SC_ADDR:  # noqa: E501
                continue

            self.esdt_nft_hex = str(
                res["data"]
            ).split("@")[-1]
            if len(self.esdt_nft_hex) < len("XPNFT")*2:
                continue

            break

        self.esdt_nft_str = bytes.fromhex(self.esdt_nft_hex).decode('utf-8')
        if "out of funds" in self.esdt_nft_str:
            raise Exception("Invalid ESDT Issuance value!")

        return self.esdt_nft_str

    def prepare_egld_swap_esdt(self) -> str:
        tx = self.contract_swap.execute(
            caller=self.sender,
            function="issueWrappedEgld",
            value=self.esdt_cost,
            arguments=[
                f"0x{b'WEGLD'.hex()}",
                f"0x{b'WEGLD'.hex()}",
                "0x0"
            ],
            gas_price=consts.GAS_PRICE,
            gas_limit=consts.ESDT_GASL,
            chain=str(self.proxy.get_chain_id()),  # type: ignore
            version=config.get_tx_version()
        )

        tx.send(cast(IElrondProxy, self.proxy))

        token = self.contract_swap.query(
            self.proxy,
            "getWrappedEgldTokenIdentifier",
            [],
        )

        self.swap_token = str(token[0])
        self.swap_token_hex = self.swap_token.encode('utf-8').hex()

        return self.swap_token

    def deploy_sc(self, init_args: List[str], project: str) -> SmartContract:
        if not self.esdt_hex:
            raise Exception("Deploy called before prepare_esdt!")

        subprocess.run(
            ["erdpy", "contract", "build"],
            check=True,
            cwd=project
        )

        with open(consts.OUT_FILE.format(project=self.project), 'rb') as ct:
            bytecode = ct.read()

        contract = SmartContract(bytecode=bytecode.hex())  # type: ignore
        self.sender.sync_nonce(self.proxy)
        tx = contract.deploy(
            self.sender,
            init_args,
            consts.GAS_PRICE,
            consts.ESDT_GASL,
            value=0,
            chain=str(self.proxy.get_chain_id()),  # type: ignore
            version=config.get_tx_version()
        )
        tx.send(cast(IElrondProxy, self.proxy))
        tx.send_wait_result(self.proxy, 30)  # type: ignore
        print("Contract tx:", tx.hash)

        return contract

    def setup_sc_perms(self, data: str) -> Transaction:
        if not self.contract:
            raise Exception("Setup SC called before deploy!")

        tx = Transaction()  # type: ignore
        tx.value = str(0)
        tx.sender = self.sender.address.bech32()
        tx.receiver = consts.ESDT_SC_ADDR
        tx.gasPrice = consts.GAS_PRICE
        tx.gasLimit = consts.ESDT_GASL
        tx.data = data
        tx.chainID = str(self.proxy.get_chain_id())  # type: ignore
        tx.version = config.get_tx_version()

        self.sender.sync_nonce(self.proxy)
        tx.nonce = self.sender.nonce

        tx.sign(self.sender)
        tx.send(cast(IElrondProxy, self.proxy))

        self.wait_transaction_done(tx.hash)

        return tx

    def check_esdt_bal(self, bch32_addr: str) -> Optional[int]:
        try:
            uri = consts.ESDT_BAL_URI.format(
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
            gas_price=consts.GAS_PRICE,
            gas_limit=consts.ESDT_GASL,
            chain=str(self.proxy.get_chain_id()),  # type: ignore
            version=config.get_tx_version()
        )

        tx.send(cast(IElrondProxy, self.proxy))

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
            gas_price=consts.GAS_PRICE,
            gas_limit=consts.ESDT_GASL,
            chain=str(self.proxy.get_chain_id()),  # type: ignore
            version=config.get_tx_version()
        )

        tx.send(cast(IElrondProxy, self.proxy))

        return tx
