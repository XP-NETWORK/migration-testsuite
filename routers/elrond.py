from fastapi import APIRouter
from pydantic import BaseModel
from starlette.requests import Request

from chains import elrond
from chains.elrond import ElrondHelper
from routers.common import XpNetTransferReq, TxHash
import deps

router = APIRouter()


class XpNetUnfreezeReq(BaseModel):
    pem: str
    destination: str
    value: int


EgldTransferReq = XpNetUnfreezeReq
EgldUnfreezeReq = XpNetTransferReq


@router.post("/xpnet/withdraw")
async def withdraw_xpnet_e2p(req: Request, data: XpNetUnfreezeReq) -> TxHash:
    elrd = deps.get(req.app, ElrondHelper)

    sender = elrond.account(data.pem)
    tx = elrd.unfreeze(sender, data.destination, data.value)
    event = tx.data_decoded()
    print(event)

    return TxHash(tx=tx.hash)


@router.post("/egld/transfer")
async def transfer_egld_e2p(req: Request, data: EgldTransferReq) -> TxHash:
    elrd = deps.get(req.app, ElrondHelper)

    sender = elrond.account(data.pem)
    tx = elrd.send_tokens(sender, data.destination, data.value)
    event = tx.data_decoded()
    print(event)

    return TxHash(tx=tx.hash)
