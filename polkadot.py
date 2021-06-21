from __future__ import annotations

from substrateinterface.exceptions import ExtrinsicFailedException
from config import PolkadotConfig
import consts
import subprocess

from pathlib import Path
from typing import cast

from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.contracts import ContractCode, ContractExecutionReceipt


class PolkadotHelper:
    def __init__(
            self,
            provider: str,
            freezer_project: str,
            erc20_project: str
    ):
        self.substrate = SubstrateInterface(
            url=provider,
            ss58_format=42,
            type_registry_preset='default'
        )
        self.freezer_project = freezer_project
        self.erc20_project = erc20_project
        self.sender = Keypair.create_from_uri(consts.ALICE_URI)

    @classmethod
    def setup(cls, config: PolkadotConfig) -> PolkadotHelper:
        print("Polkadot setup")

        polka = cls(config.uri, config.freezer_project, config.erc20_project)

        print(f"deployed erc20: {polka.deploy_erc20()}")
        print(f"deployed contract: {polka.deploy_sc()}")

        print(f"sending coins to validator: {config.validator}")
        call = polka.substrate.compose_call(
            call_module='Balances',
            call_function='transfer',
            call_params={
                'dest': config.validator,
                'value': 10**16
            }
        )
        ext = polka.substrate.create_signed_extrinsic(call, polka.sender)
        polka.substrate.submit_extrinsic(ext, wait_for_inclusion=True)

        return polka

    def erc20_transfer_ownership(self, addr: str) -> ContractExecutionReceipt:
        dry = self.erc20.read(
            self.sender,
            consts.INK_EGLD_NEW_OWNER_CALL,
            args={'owner': addr},
            value=0
        )

        return self.erc20.exec(
            self.sender,
            consts.INK_EGLD_NEW_OWNER_CALL,
            args={'owner': addr},
            value=0,
            gas_limit=cast(int, dry.gas_consumed)
        )

    def deploy_erc20(self) -> str:
        subprocess.run(
            ["cargo", "+nightly", "contract", "build"],
            check=True,
            cwd=self.erc20_project
        )

        target = Path(consts.POLKADOT_OUT_DIR.format(
            project=self.erc20_project
        ))
        code = ContractCode.create_from_contract_files(
            wasm_file=list(target.glob("*.wasm"))[0].as_posix(),
            metadata_file=target.joinpath("metadata.json").as_posix(),
            substrate=self.substrate
        )

        try:
            self.erc20 = code.deploy(
                keypair=self.sender,
                constructor="new",
                upload_code=True,
                endowment=consts.POLKADOT_FREEZER_ENDOW,
                gas_limit=consts.POLKADOT_DEPLOY_GASL,
                args={"initial_supply": 1000}
            )
        except ExtrinsicFailedException as e:
            if e.args[0]["name"] == "DuplicateContract":
                print("WARN: Contract is predeployed. not handled yet!")
            else:
                raise e

        return str(self.erc20.contract_address)

    def deploy_sc(self) -> str:
        subprocess.run(
            ["cargo", "+nightly", "contract", "build"],
            check=True,
            cwd=self.freezer_project
        )

        target = Path(consts.POLKADOT_OUT_DIR.format(
            project=self.freezer_project
        ))
        code = ContractCode.create_from_contract_files(
            wasm_file=list(target.glob("*.wasm"))[0].as_posix(),
            metadata_file="./workaround.json",
            substrate=self.substrate
        )

        try:
            self.contract = code.deploy(
                keypair=self.sender,
                constructor="new",
                upload_code=True,
                endowment=consts.POLKADOT_FREEZER_ENDOW,
                gas_limit=consts.POLKADOT_DEPLOY_GASL,
                args={"erc20_addr": self.erc20.contract_address}
            )
        except ExtrinsicFailedException as e:
            if e.args[0]["name"] == "DuplicateContract":
                print("WARN: Contract is predeployed. not handled yet!")
            else:
                raise e

        assert(self.erc20_transfer_ownership(self.contract.contract_address)
               .is_success)

        return str(self.contract.contract_address)

    def send_tokens(self, to: str, value: int) -> ContractExecutionReceipt:
        dry = self.contract.read(
            self.sender,
            consts.FREEZER_SEND_CALL,
            args={'to': to},
            value=value
        )

        return self.contract.exec(
            self.sender,
            consts.FREEZER_SEND_CALL,
            args={'to': to},
            value=value,
            gas_limit=cast(int, dry.gas_consumed)
        )

    def unfreeze_wrap(
        self,
        sender: Keypair,
        to: str,
        value: int
    ) -> ContractExecutionReceipt:
        dry = self.contract.read(
            sender,
            consts.FREEZER_UNFREEZE_CALL,
            args={'to': to, 'value': value},
            value=0
        )

        return self.contract.exec(
            sender,
            consts.FREEZER_UNFREEZE_CALL,
            args={'to': to, 'value': value},
            value=0,
            gas_limit=cast(int, dry.gas_consumed)
        )
