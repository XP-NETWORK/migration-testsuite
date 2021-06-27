from consts import common as consts
from typing import TypeVar

from fastapi.routing import APIRouter
from chains.elrond import ElrondHelper
from chains.web3_h import Web3Helper
from chains.polkadot import PolkadotHelper
from config import Config
from setup import setup_elrd, setup_polkadot, setup_web3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import common, elrond, w3

import deps

Helper = TypeVar('Helper', ElrondHelper, Web3Helper)


def init_fastapi(app: FastAPI, helper: Helper, router: APIRouter) -> None:
    deps.inject(app, type(helper), helper)
    app.include_router(router)


def setup_app() -> FastAPI:
    config = Config()

    app = FastAPI()

    if config.rest.chain == "ELROND":
        polka = setup_polkadot(
            config.polkadot, "./workaround.json", consts.CACHE_POLKADOT_ELRD
        )
        init_fastapi(app, setup_elrd(polka, config), elrond.router)
    elif config.rest.chain == "HECO":
        polka = setup_polkadot(
            config.polkadot, "./workaround_w3.json", consts.CACHE_POLKADOT_W3
        )
        init_fastapi(app, setup_web3(polka, config), w3.router)
    else:
        raise Exception("Invalid Chain in Config!")

    deps.inject(app, PolkadotHelper, polka)
    app.include_router(common.router)

    return app


try:
    app = setup_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    print(app.openapi())
except KeyboardInterrupt:
    exit(0)
