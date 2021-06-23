from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse
from substrateinterface.base import Keypair

from chains.polkadot import PolkadotHelper
import deps

router = APIRouter()


class OkRespone(BaseModel):
    status: str = "ok"


class XpNetTransferReq(BaseModel):
    sender_addr: str
    sender_key: str
    destination: str
    value: int


TokenUnfreezeReq = XpNetTransferReq


class TxHash(BaseModel):
    tx: str


@router.post("/xpnet/transfer")
async def transfer_xpnet_p2(req: Request,
                            data: XpNetTransferReq) -> JSONResponse:
    polka = deps.get(req.app, PolkadotHelper)

    sender = Keypair.create_from_private_key(data.sender_key,
                                             ss58_address=data.sender_addr)
    if not polka.send_tokens(sender, data.destination, data.value).is_success:
        raise HTTPException(status_code=500, detail="Failed to send tokens")

    return JSONResponse(jsonable_encoder(OkRespone()))


@router.post("/{token}/withdraw")
async def withdraw_token_p2e(req: Request,
                             data: TokenUnfreezeReq,
                             token: str) -> JSONResponse:
    polka = deps.get(req.app, PolkadotHelper)

    sender = Keypair.create_from_private_key(data.sender_key,
                                             ss58_address=data.sender_addr)
    if not polka.unfreeze_wrap(sender, data.destination, data.value).is_success:  # noqa: E501
        raise HTTPException(status_code=500,
                            detail=f"Failed to unfreeze {token}")

    return JSONResponse(jsonable_encoder(OkRespone()))
