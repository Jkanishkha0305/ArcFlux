"""
============================================
ARCPAY FASTAPI APPLICATION
============================================

Main FastAPI application with all API endpoints.

This is the Python equivalent of the Cloudflare
Worker index.js file.
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uvicorn

from config import settings
from database import (
    init_db, get_db,
    create_scheduled_payment, get_user_scheduled_payments,
    get_payment_history, cancel_scheduled_payment,
    ScheduledPayment, PaymentHistory
)
from circle_integration import circle_api
from ai_agent import ai_agent, interval_to_ms
from scheduler import payment_scheduler

# ============================================
# FASTAPI APPLICATION
# ============================================

app = FastAPI(
    title="ArcPay API",
    description="AI-powered payment automation on Arc blockchain",
    version="1.0.0"
)

# ============================================
# CORS MIDDLEWARE
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# PYDANTIC MODELS (Request/Response schemas)
# ============================================

class ParseIntentRequest(BaseModel):
    input: str

class ParseIntentResponse(BaseModel):
    success: bool
    intent: Optional[dict] = None
    error: Optional[str] = None

class CreatePaymentRequest(BaseModel):
    walletId: str
    recipient: str
    amount: float
    interval: str

class CreatePaymentResponse(BaseModel):
    success: bool
    payment: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None

class QueryRequest(BaseModel):
    query: str
    walletId: Optional[str] = None

class QueryResponse(BaseModel):
    success: bool
    answer: str

# ============================================
# STARTUP/SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize database and start scheduler"""
    print("🚀 Starting ArcPay API...")
    
    # Initialize database tables
    init_db()
    
    # Start payment scheduler
    payment_scheduler.start()
    
    print("✓ ArcPay API ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on shutdown"""
    payment_scheduler.stop()
    print("✓ ArcPay API stopped")

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ArcPay API is running! 🚀",
        "version": "1.0.0",
        "scheduler_running": payment_scheduler.running
    }

@app.post("/api/parse-intent", response_model=ParseIntentResponse)
async def parse_intent(request: ParseIntentRequest):
    """
    Parse natural language payment command using AI.
    
    Example:
        POST /api/parse-intent
        {"input": "Pay 50 USDC to Alice every week"}
    """
    try:
        intent = ai_agent.parse_payment_intent(request.input)
        return ParseIntentResponse(success=True, intent=intent)
    
    except Exception as e:
        return ParseIntentResponse(success=False, error=str(e))

@app.post("/api/create-payment", response_model=CreatePaymentResponse)
async def create_payment(
    request: CreatePaymentRequest,
    db: Session = Depends(get_db)
):
    """
    Create a scheduled payment.
    For one-time payments (interval="once"), executes immediately.
    
    Example:
        POST /api/create-payment
        {
            "walletId": "wallet-123",
            "recipient": "0x742d35Cc...",
            "amount": 50,
            "interval": "weekly"
        }
    """
    try:
        # Validate inputs
        if not request.walletId or not request.recipient or not request.amount:
            raise Exception("Missing required fields")
        
        if not circle_api.is_valid_address(request.recipient):
            raise Exception("Invalid recipient address")
        
        # Convert interval to milliseconds
        interval_ms = interval_to_ms(request.interval)
        
        # Create scheduled payment
        payment = create_scheduled_payment(
            db=db,
            user_wallet_id=request.walletId,
            recipient_address=request.recipient,
            amount=request.amount,
            interval_ms=interval_ms
        )
        
        # For one-time payments, execute immediately
        transaction_result = None
        if interval_ms == 0:
            try:
                # Check balance first
                balance = circle_api.get_wallet_balance(request.walletId)
                balance_float = float(balance)
                
                if balance_float < request.amount:
                    raise Exception(
                        f"Insufficient balance: have {balance} USDC, need {request.amount} USDC"
                    )
                
                # Execute transfer immediately
                print(f"[CREATE-PAYMENT] Executing immediate transfer: {request.amount} USDC to {request.recipient}")
                transaction = circle_api.transfer_usdc(
                    from_wallet_id=request.walletId,
                    to_address=request.recipient,
                    amount=request.amount
                )
                
                transaction_id = transaction.get("transactionId")
                transaction_status = transaction.get("status")
                print(f"[CREATE-PAYMENT] Transfer initiated: {transaction_id} (status: {transaction_status})")
                
                # Wait a moment for transaction to process, then get transaction hash
                import time
                time.sleep(2)
                
                tx_hash = None
                if transaction_id:
                    try:
                        tx_status = circle_api.get_transaction_status(transaction_id)
                        tx_hash = tx_status.get("txHash")
                        if tx_hash:
                            print(f"[CREATE-PAYMENT] Transaction hash: {tx_hash}")
                    except Exception as e:
                        print(f"[CREATE-PAYMENT] Could not get transaction hash yet: {e}")
                
                # Record payment history
                from database import record_payment_history
                record_payment_history(
                    db=db,
                    scheduled_payment_id=payment.id,
                    from_wallet_id=request.walletId,
                    to_address=request.recipient,
                    amount=request.amount,
                    status="completed" if transaction_status in ["COMPLETE", "CONFIRMED"] else "pending",
                    transaction_hash=tx_hash
                )
                
                # Mark one-time payment as completed
                from database import cancel_scheduled_payment
                cancel_scheduled_payment(db, payment.id)
                
                transaction_result = {
                    "transactionId": transaction_id,
                    "status": transaction_status,
                    "txHash": tx_hash,
                    "executed": True
                }
                print(f"[CREATE-PAYMENT] ✅ Payment executed successfully: {transaction_id}")
                
            except Exception as e:
                # Log the error for debugging
                import traceback
                error_msg = str(e)
                print(f"[CREATE-PAYMENT] ❌ Error executing payment: {error_msg}")
                traceback.print_exc()
                
                # Return error to user - don't create payment if execution fails
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to execute payment: {error_msg}"
                )
        
        return CreatePaymentResponse(
            success=True,
            payment={
                "id": payment.id,
                "amount": payment.amount,
                "recipient": payment.recipient_address,
                "interval_ms": payment.interval_ms,
                "next_execution_time": payment.next_execution_time,
                "status": payment.status,
                "transaction": transaction_result
            },
            message="Payment executed immediately" if interval_ms == 0 and transaction_result and transaction_result.get("executed") else "Payment scheduled successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/payments")
async def get_payments(
    walletId: str = Query(..., description="Wallet ID"),
    db: Session = Depends(get_db)
):
    """Get user's active scheduled payments"""
    try:
        payments = get_user_scheduled_payments(db, walletId)
        
        return {
            "success": True,
            "payments": [
                {
                    "id": p.id,
                    "user_wallet_id": p.user_wallet_id,
                    "recipient_address": p.recipient_address,
                    "amount": p.amount,
                    "interval_ms": p.interval_ms,
                    "next_execution_time": p.next_execution_time,
                    "status": p.status,
                    "created_at": p.created_at,
                    "execution_count": p.execution_count,
                    "total_sent": p.total_sent
                }
                for p in payments
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_history(
    walletId: str = Query(..., description="Wallet ID"),
    limit: int = Query(50, description="Max results"),
    db: Session = Depends(get_db)
):
    """Get payment execution history from Circle blockchain"""
    try:
        # Get real transactions from Circle API
        circle_transactions = circle_api.get_wallet_transactions(walletId, limit)
        
        # Convert Circle transactions to history format
        history = []
        for tx in circle_transactions:
            # Map Circle transaction states to our status
            status_map = {
                "COMPLETE": "completed",
                "CONFIRMED": "completed",
                "FAILED": "failed",
                "SENT": "pending",
                "QUEUED": "pending",
                "INITIATED": "pending"
            }
            status = status_map.get(tx.get("state", "UNKNOWN"), "pending")
            
            history.append({
                "id": tx.get("id"),
                "scheduled_payment_id": None,  # Not linked to scheduled payment
                "from_wallet_id": walletId,
                "to_address": tx.get("to_address"),
                "amount": float(tx.get("amount", "0")),
                "status": status,
                "transaction_hash": tx.get("txHash"),
                "executed_at": int(datetime.fromisoformat(tx.get("created_at", "").replace("Z", "+00:00")).timestamp() * 1000) if tx.get("created_at") else int(datetime.now().timestamp() * 1000),
                "error_message": None,
                "blockchain": tx.get("blockchain"),
                "network_fee": tx.get("network_fee")
            })
        
        # Also include database history for scheduled payments (merge)
        db_history = get_payment_history(db, walletId, limit)
        for h in db_history:
            # Only add if not already in Circle transactions
            if not any(tx.get("transaction_hash") == h.transaction_hash for tx in history if h.transaction_hash):
                history.append({
                    "id": h.id,
                    "scheduled_payment_id": h.scheduled_payment_id,
                    "from_wallet_id": h.from_wallet_id,
                    "to_address": h.to_address,
                    "amount": h.amount,
                    "status": h.status,
                    "transaction_hash": h.transaction_hash,
                    "executed_at": h.executed_at,
                    "error_message": h.error_message,
                    "blockchain": None,
                    "network_fee": None
                })
        
        # Sort by executed_at descending (most recent first)
        history.sort(key=lambda x: x.get("executed_at", 0), reverse=True)
        history = history[:limit]  # Limit results
        
        return {
            "success": True,
            "history": history
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/api/cancel-payment")
async def cancel_payment(
    paymentId: str,
    db: Session = Depends(get_db)
):
    """Cancel a scheduled payment"""
    try:
        cancel_scheduled_payment(db, paymentId)
        
        return {
            "success": True,
            "message": "Payment cancelled successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query", response_model=QueryResponse)
async def handle_query(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Handle user queries about payments.
    
    Example:
        POST /api/query
        {"query": "What's my balance?", "walletId": "wallet-123"}
    """
    try:
        # Get context
        context = {}
        
        if request.walletId:
            balance = circle_api.get_wallet_balance(request.walletId)
            payments = get_user_scheduled_payments(db, request.walletId)
            
            context = {
                "balance": balance,
                "activePayments": len(payments),
                "recentTransactions": "see history"
            }
        
        answer = ai_agent.handle_query(request.query, context)
        
        return QueryResponse(success=True, answer=answer)
    
    except Exception as e:
        return QueryResponse(success=False, answer=f"Error: {str(e)}")

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True  # Auto-reload on code changes (development only)
    )

