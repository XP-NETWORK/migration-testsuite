from typing import TypeVar

from fastapi.routing import APIRouter
from chains.elrond import ElrondHelper
from chains.web3_h import Web3Helper
from chains.polkadot import PolkadotHelper
from config import Config
from setup import setup_elrd, setup_web3
from fastapi import FastAPI

from routers import common, elrond, w3

import deps

Helper = TypeVar('Helper', ElrondHelper, Web3Helper)


def init_fastapi(app: FastAPI, helper: Helper, router: APIRouter) -> None:
    deps.inject(app, type(helper), helper)
    app.include_router(router)


def main() -> None:
    config = Config()

    app = FastAPI()

    if config.rest.chain == "ELROND":
        polka = PolkadotHelper.setup(config.polkadot, "./workaround.json")
        init_fastapi(app, setup_elrd(polka, config), elrond.router)
    elif config.rest.chain == "HECO":
        polka = PolkadotHelper.setup(config.polkadot, "./workaround_w3.json")
        init_fastapi(app, setup_web3(polka, config), w3.router)
    else:
        print("Invalid Chain in Config!")
        return

    deps.inject(app, PolkadotHelper, polka)
    app.include_router(common.router)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
