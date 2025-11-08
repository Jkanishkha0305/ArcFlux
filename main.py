"""
FastAPI server for Circle Wallet operations
"""
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from circle_api import circle_api

load_dotenv()

app = FastAPI(
    title="Circle Wallet API",
    description="API for Circle wallet operations on Arc testnet",
    version="1.0.0"
)

# Enable CORS for React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TransferRequest(BaseModel):
    """Transfer request model"""
    walletId: str
    destinationAddress: str
    amount: str
    blockchain: str = "ARC-TESTNET"


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "ok",
        "message": "Circle Wallet API is running",
        "endpoints": {
            "balance": "/api/balance?walletId={wallet_id}",
            "transfer": "/api/transfer (POST)"
        }
    }


@app.get("/api/balance")
async def get_balance(
    walletId: str = Query(..., description="Wallet ID")
):
    """Get wallet USDC balance"""
    try:
        balance = circle_api.get_wallet_balance(walletId)

        return {
            "success": True,
            "balance": balance
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transfer")
async def create_transfer(request: TransferRequest):
    """
    Create a USDC transfer transaction

    Returns challenge_id for PIN approval in React app
    """
    try:
        result = circle_api.create_transfer(
            wallet_id=request.walletId,
            destination_address=request.destinationAddress,
            amount_usdc=request.amount,
            blockchain=request.blockchain
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wallet/{wallet_id}")
async def get_wallet_info(wallet_id: str):
    """Get wallet information"""
    try:
        wallet_info = circle_api.get_wallet_balance(wallet_id)

        return {
            "success": True,
            "wallet": wallet_info
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
