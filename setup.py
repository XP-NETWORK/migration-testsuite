import dataclasses
from chains.elrond import ElrondHelper
from chains.web3_h import Web3Helper
from chains.polkadot import PolkadotHelper
from validator import ValidatorHelper
from config import (
    Config,
    ElrondValidatorRuntimeConfig, Web3ValidatorRuntimeConfig
)


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
