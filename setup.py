import dataclasses
import json
from pathlib import Path
from typing import Callable, Dict, TypeVar
from chains.elrond import ElrondHelper
from chains.web3_h import Web3Helper
from chains.polkadot import PolkadotHelper
from validator import ValidatorHelper
from consts import common as consts
from config import (
    Config,
    ElrondValidatorRuntimeConfig,
    PolkadotConfig,
    Web3ValidatorRuntimeConfig
)

C = TypeVar('C')
Helper = TypeVar('Helper')


def save_cache(cache_f: Path, data: Dict[str, str]) -> None:
    with open(cache_f, 'w') as cache:
        json.dump(data, cache)


def setup_polkadot(config: PolkadotConfig, abi: str,
                   cache: Path) -> PolkadotHelper:
    polka: PolkadotHelper
    if cache.exists():
        polka = load_cache_polkadot(config, abi, cache)
    else:
        polka = PolkadotHelper.setup(config, abi)
        save_cache(cache, polka.cache_dict())

    return polka


def load_cache_helper(
    config: C,
    cache_f: Path,
    loader: Callable[[C, Dict[str, str]], Helper]
) -> Helper:
    with open(cache_f, 'r') as cache:
        return loader(config, json.load(cache))


def load_cache_polkadot(config: PolkadotConfig, abi: str,
                        cache_f: Path) -> PolkadotHelper:
    with open(cache_f, 'r') as cache:
        return PolkadotHelper.load_cache(config, abi, json.load(cache))


def load_or_setup(
    config: C,
    cache_f: Path,
    setup: Callable[[C], Helper],
    loader: Callable[[C, Dict[str, str]], Helper],
    saver: Callable[[Helper], Dict[str, str]]
) -> Helper:
    res: Helper
    if cache_f.exists():
        res = load_cache_helper(config, cache_f, loader)
    else:
        res = setup(config)
        save_cache(cache_f, saver(res))

    return res


def setup_web3(polka: PolkadotHelper, config: Config) -> Web3Helper:
    validator = ValidatorHelper(config.validator.project)
    print()
    w3 = load_or_setup(
        config.web3,
        consts.CACHE_WEB3,
        Web3Helper.setup,
        Web3Helper.load_cache, Web3Helper.cache_dict
    )
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
    elrd = load_or_setup(
        config.elrond,
        consts.CACHE_ELROND,
        ElrondHelper.setup,
        ElrondHelper.load_cache, ElrondHelper.cache_dict
    )

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
    #validator.spawn()

    return elrd
