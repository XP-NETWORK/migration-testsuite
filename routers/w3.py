import eth_account

from fastapi import APIRouter
from starlette.requests import Request
from routers.common import XpNetTransferReq, TxHash

from chains.web3_h import Web3Helper
import deps

router = APIRouter()


XpNetUnfreezeReq = XpNetTransferReq
HTTransferReq = XpNetTransferReq


@router.post("/xpnet/withdraw")
async def withdraw_xpnet_w32p(req: Request, data: XpNetUnfreezeReq) -> TxHash:
    w3 = deps.get(req.app, Web3Helper)

    sender = eth_account.Account.from_key(data.sender_key)

    tx = w3.withdraw_tokens(sender, data.destination, data.value)

    return TxHash(tx=tx["blockHash"].hex())


@router.post("/ht/transfer")
async def transfer_ht_w32p(req: Request, data: HTTransferReq) -> TxHash:
    w3 = deps.get(req.app, Web3Helper)

    sender = eth_account.Account.from_key(data.sender_key)

    tx = w3.freeze_ht(sender, data.destination, data.value)

    return TxHash(tx=tx['blockHash'].hex())
