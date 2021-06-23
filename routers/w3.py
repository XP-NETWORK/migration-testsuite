import eth_account

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from pydantic.main import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse
from routers.common import TxHash

from chains.web3_h import Web3Helper
import deps

router = APIRouter()


class HTTransferReq(BaseModel):
    sender_key: str
    destination: str
    value: int


XpNetUnfreezeReq = HTTransferReq


@router.post("/xpnet/withdraw")
async def withdraw_xpnet_w32p(req: Request,
                              data: XpNetUnfreezeReq) -> JSONResponse:
    w3 = deps.get(req.app, Web3Helper)

    sender = eth_account.Account.from_key(data.sender_key)

    tx = w3.withdraw_tokens(sender, data.destination, data.value)

    return JSONResponse(jsonable_encoder(TxHash(tx=tx["blockHash"].hex())))


@router.post("/ht/transfer")
async def transfer_ht_w32p(req: Request, data: HTTransferReq) -> JSONResponse:
    w3 = deps.get(req.app, Web3Helper)

    sender = eth_account.Account.from_key(data.sender_key)

    tx = w3.freeze_ht(sender, data.destination, data.value)

    return JSONResponse(jsonable_encoder(TxHash(tx=tx['blockHash'].hex())))
