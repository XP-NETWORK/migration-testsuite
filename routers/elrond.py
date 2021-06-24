import httpx

from typing import Any, Dict, List
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from chains import elrond
from chains.elrond import ElrondHelper
from routers.common import TxHash
import deps

router = APIRouter()


class XpNetUnfreezeReq(BaseModel):
    pem: str
    destination: str
    value: int


EgldTransferReq = XpNetUnfreezeReq


def filter_event_id(res: List[Dict[str, Any]]) -> int:
    for r in res:
        if int(r["nonce"]) == 0:
            continue

        try:
            return int(str(r["data"]).split("@")[-1][1:])
        except Exception:
            continue

    raise Exception("invalid res:", res)


async def emit_event(uri: str, ident: int):
    async with httpx.AsyncClient() as req:
        await req.post(f"{uri}/event/transfer", headers={"id": str(ident)})


@router.post("/xpnet/withdraw")
async def withdraw_xpnet_e2p(req: Request,
                             data: XpNetUnfreezeReq) -> JSONResponse:
    elrd = deps.get(req.app, ElrondHelper)

    sender = elrond.account(data.pem)
    tx = elrd.unfreeze(sender, data.destination, data.value)
    event = filter_event_id(
        tx.send_wait_result(elrd.proxy,
                            30)["smartContractResults"]  # type: ignore
    )
    await emit_event(elrd.event_uri, event)

    return JSONResponse(jsonable_encoder(TxHash(tx=tx.hash)))


@router.post("/egld/transfer")
async def transfer_egld_e2p(req: Request,
                            data: EgldTransferReq) -> JSONResponse:
    elrd = deps.get(req.app, ElrondHelper)

    sender = elrond.account(data.pem)
    tx = elrd.send_tokens(sender, data.destination, data.value)
    event = filter_event_id(
        tx.send_wait_result(elrd.proxy,
                            30)["smartContractResults"]  # type: ignore
    )
    await emit_event(elrd.event_uri, event)

    return JSONResponse(jsonable_encoder(TxHash(tx=tx.hash)))
