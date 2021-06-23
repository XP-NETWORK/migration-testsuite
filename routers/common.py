from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.requests import Request
from substrateinterface.base import Keypair

from chains.polkadot import PolkadotHelper
import deps

router = APIRouter()


class XpNetTransferReq(BaseModel):
    sender_key: str
    destination: str
    value: int


TokenUnfreezeReq = XpNetTransferReq


class TxHash(BaseModel):
    tx: str


@router.post("/xpnet/transfer")
async def transfer_xpnet_p2(req: Request, data: XpNetTransferReq) -> None:
    polka = deps.get(req.app, PolkadotHelper)

    sender = Keypair.create_from_private_key(data.sender_key)
    if not polka.send_tokens(sender, data.destination, data.value).is_success:
        raise HTTPException(status_code=500, detail="Failed to send tokens")


@router.post("/{token}/withdraw")
async def withdraw_token_p2e(req: Request,
                             data: TokenUnfreezeReq, token: str) -> None:
    polka = deps.get(req.app, PolkadotHelper)

    sender = Keypair.create_from_private_key(data.sender_key)
    if not polka.unfreeze_wrap(sender, data.destination, data.value).is_success:  # noqa: E501
        raise HTTPException(status_code=500,
                            detail=f"Failed to unfreeze {token}")
