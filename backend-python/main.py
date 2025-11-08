"""
============================================
ARCFLUX FASTAPI APPLICATION
============================================

Main FastAPI application with all API endpoints.

This is the Python equivalent of the Cloudflare
Worker index.js file.
"""

from fastapi import FastAPI, Depends, HTTPException, Query, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import uvicorn
from datetime import timedelta

# Try to import JWT, fallback to simple token if not available
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("Warning: PyJWT not installed. Using simple token generation.")

from config import settings
from database import (
    init_db, get_db,
    create_scheduled_payment, get_user_scheduled_payments,
    get_payment_history, cancel_scheduled_payment,
    ScheduledPayment, PaymentHistory,
    create_contact, get_user_contacts, delete_contact,
    create_user, authenticate_user, User,
    record_payment_history,
    create_risk_assessment, get_risk_assessments, get_high_risk_assessments
)
from circle_integration import circle_api, CircleAPI
from ai_agent import ai_agent, interval_to_ms
from payment_agent import payment_agent
from scheduler import payment_scheduler
from wallet_creation import create_wallet_for_user, create_wallet_for_user_with_api_key
from guardian_agent import guardian_agent
from query_agent import query_agent
from balance_monitor import balance_monitor
from stock_agent import stock_agent

# Voice transcription (optional - only if ElevenLabs API key is configured)
try:
    from voice import TranscriptionHandler
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("Warning: Voice transcription module not available. Install elevenlabs package.")

# ============================================
# FASTAPI APPLICATION
# ============================================

app = FastAPI(
    title="ArcFlux API",
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
    dashboard: Optional[Dict] = None


class AgentPayRequest(BaseModel):
    walletId: str
    command: str
    execute: bool = False


class AgentPayResponse(BaseModel):
    success: bool
    plan: Dict
    message: Optional[str] = None
    transaction: Optional[Dict] = None
    error: Optional[str] = None


def _get_circle_client_for_wallet(db: Session, wallet_id: str):
    """Return the appropriate Circle API client for a user wallet."""

    user = db.query(User).filter(User.wallet_id == wallet_id).first()

    if user and user.entity_secret:
        api_key = user.circle_api_key or settings.circle_api_key
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="Circle API key not configured for this wallet."
            )
        return CircleAPI(api_key=api_key, entity_secret=user.entity_secret), user

    if not settings.circle_api_key or not settings.circle_entity_secret:
        raise HTTPException(
            status_code=400,
            detail="Circle API credentials are not configured on the server."
        )

    return circle_api, user


def _serialize_contacts(contacts: List) -> List[Dict]:
    """Simplify SQLAlchemy contact rows into plain dicts."""

    return [
        {
            "id": contact.id,
            "name": contact.name,
            "address": contact.address,
        }
        for contact in contacts
    ]

# ============================================
# STARTUP/SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize database and start scheduler"""
    print("🚀 Starting ArcFlux API...")
    
    # Initialize database tables
    init_db()
    
    # Start payment scheduler
    payment_scheduler.start()
    
    print("✓ ArcFlux API ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on shutdown"""
    payment_scheduler.stop()
    print("✓ ArcFlux API stopped")

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ArcFlux API is running! 🚀",
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
        if not request.walletId:
            raise HTTPException(status_code=400, detail="Wallet ID is required. Please set up your wallet first in Profile Settings.")
        if not request.recipient:
            raise HTTPException(status_code=400, detail="Recipient address is required")
        if not request.amount or request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        
        if not circle_api.is_valid_address(request.recipient):
            raise HTTPException(status_code=400, detail=f"Invalid recipient address format: {request.recipient}")
        
        # Check if user has wallet set up
        user = db.query(User).filter(User.wallet_id == request.walletId).first()
        if not user:
            # Wallet ID doesn't belong to any user - might be from env var or invalid
            # For non-user wallets, we still allow but need to check if wallet exists
            print(f"[CREATE-PAYMENT] Warning: Wallet ID {request.walletId} not found in user database")
        
        # Convert interval to milliseconds
        try:
            interval_ms = interval_to_ms(request.interval)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid interval '{request.interval}': {str(e)}")
        
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
                # Get user's API key and entity secret if this is a user wallet
                if user and user.entity_secret:
                    # Use user's Circle API instance with their API key
                    from circle_integration import CircleAPI
                    if not user.circle_api_key:
                        raise HTTPException(
                            status_code=400,
                            detail="Circle API key not configured. Please add your API key in Profile Settings to execute payments."
                        )
                    user_circle_api = CircleAPI(api_key=user.circle_api_key, entity_secret=user.entity_secret)
                    api_instance = user_circle_api
                elif user and not user.entity_secret:
                    raise HTTPException(
                        status_code=400,
                        detail="Wallet not properly configured. Please regenerate your wallet in Profile Settings."
                    )
                else:
                    # Use default Circle API instance (for legacy/non-user wallets)
                    if not settings.circle_api_key:
                        raise HTTPException(
                            status_code=400,
                            detail="Circle API key not configured. Please configure your API key."
                        )
                    api_instance = circle_api
                
                # Check balance first
                balance = api_instance.get_wallet_balance(request.walletId)
                balance_float = float(balance)
                
                if balance_float < request.amount:
                    raise Exception(
                        f"Insufficient balance: have {balance} USDC, need {request.amount} USDC"
                    )
                
                # Execute transfer immediately
                print(f"[CREATE-PAYMENT] Executing immediate transfer: {request.amount} USDC to {request.recipient}")
                transaction = api_instance.transfer_usdc(
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
                        tx_status = api_instance.get_transaction_status(transaction_id)
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
                # Include more context in error message
                if "Insufficient balance" in error_msg:
                    raise HTTPException(status_code=400, detail=error_msg)
                elif "wallet" in error_msg.lower() or "not found" in error_msg.lower():
                    raise HTTPException(status_code=400, detail=f"Wallet error: {error_msg}. Please ensure your wallet is set up correctly.")
                else:
                    raise HTTPException(status_code=400, detail=f"Failed to execute payment: {error_msg}")
        
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
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors
        import traceback
        error_msg = str(e)
        print(f"[CREATE-PAYMENT] ❌ Unexpected error: {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {error_msg}")

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
        # Get user's API key and entity secret if this is a user wallet
        user = db.query(User).filter(User.wallet_id == walletId).first()
        if user and user.entity_secret:
            # Use user's Circle API instance with their API key
            from circle_integration import CircleAPI
            user_api_key = user.circle_api_key or settings.circle_api_key
            user_circle_api = CircleAPI(api_key=user_api_key, entity_secret=user.entity_secret)
            api_instance = user_circle_api
        else:
            # Use default Circle API instance
            api_instance = circle_api
        
        # Get real transactions from Circle API
        circle_transactions = api_instance.get_wallet_transactions(walletId, limit)
        
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
    walletId: str = Query(..., description="Wallet ID"),
    db: Session = Depends(get_db)
):
    """Get wallet USDC balance"""
    try:
        # If walletId belongs to a user, use their API key and entity secret
        user = db.query(User).filter(User.wallet_id == walletId).first()
        if user and user.entity_secret and user.circle_api_key:
            # Create a CircleAPI instance with user's API key and entity secret
            from circle_integration import CircleAPI
            user_circle_api = CircleAPI(api_key=user.circle_api_key, entity_secret=user.entity_secret)
            balance = user_circle_api.get_wallet_balance(walletId)
        elif user and user.entity_secret:
            # Fallback to settings API key if user doesn't have one
            from circle_integration import CircleAPI
            user_circle_api = CircleAPI(api_key=settings.circle_api_key, entity_secret=user.entity_secret)
            balance = user_circle_api.get_wallet_balance(walletId)
        else:
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
    Handle user queries about payments using enhanced QueryAgent.

    Example:
        POST /api/query
        {"query": "What's my balance?", "walletId": "wallet-123"}
    """
    try:
        if not request.walletId:
            return QueryResponse(success=False, answer="Wallet ID is required for queries.")

        # Get user's API instance
        user = db.query(User).filter(User.wallet_id == request.walletId).first()
        if user and user.entity_secret:
            from circle_integration import CircleAPI
            user_api_key = user.circle_api_key or settings.circle_api_key
            api_instance = CircleAPI(api_key=user_api_key, entity_secret=user.entity_secret)
        else:
            api_instance = circle_api

        # Use enhanced QueryAgent
        result = query_agent.answer_query(
            question=request.query,
            wallet_id=request.walletId,
            db=db,
            circle_api=api_instance
        )

        if result["success"]:
            return QueryResponse(
                success=True, 
                answer=result["answer"],
                dashboard=result.get("dashboard")  # Include dashboard data if present
            )
        else:
            return QueryResponse(success=False, answer=result["answer"])

    except Exception as e:
        return QueryResponse(success=False, answer=f"Error: {str(e)}")


@app.post("/api/agent/pay", response_model=AgentPayResponse)
async def agent_pay_endpoint(
    request: AgentPayRequest,
    db: Session = Depends(get_db)
):
    """Use the MLAI-powered agent to interpret and optionally execute payments or stock purchases."""

    if not payment_agent.is_ready:
        raise HTTPException(status_code=503, detail="Payment agent is not configured.")

    if not request.walletId:
        raise HTTPException(status_code=400, detail="Wallet ID is required.")

    # Check for stock purchase intent
    stock_keywords = ["stock", "stocks", "equity", "equities", "share", "shares", "buy stock", "purchase stock"]
    command_lower = request.command.lower()
    is_stock_intent = any(keyword in command_lower for keyword in stock_keywords)

    if is_stock_intent:
        # Handle stock purchase
        return await _handle_stock_purchase(request, db)

    # Handle regular payment
    contacts = get_user_contacts(db, request.walletId)
    if not contacts:
        raise HTTPException(status_code=400, detail="No contacts found for this wallet.")

    contact_dicts = _serialize_contacts(contacts)
    plan = payment_agent.plan_payment(request.command, contact_dicts)

    if plan.get("action") != "send_payment":
        raise HTTPException(status_code=400, detail="Agent could not find a payment instruction in that text.")

    amount = float(plan.get("amount") or 0)
    currency = (plan.get("currency") or "USDC").upper()
    matched_contact = plan.get("contact")

    if currency != "USDC":
        raise HTTPException(status_code=400, detail="Only USDC payments are supported.")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Could not determine a valid amount from that command.")

    if not matched_contact:
        raise HTTPException(status_code=400, detail="Could not map that request to a saved contact.")

    to_address = matched_contact.get("address")
    if not to_address or not circle_api.is_valid_address(to_address):
        raise HTTPException(status_code=400, detail="The selected contact is missing a valid wallet address.")

    plan["contact"] = matched_contact

    # Get balance for risk assessment
    api_instance, user = _get_circle_client_for_wallet(db, request.walletId)
    balance = api_instance.get_wallet_balance(request.walletId)

    try:
        balance_value = float(balance)
    except (TypeError, ValueError):
        balance_value = 0.0

    # Run Guardian risk assessment
    risk_assessment = guardian_agent.assess_payment_risk(
        amount=amount,
        recipient_address=to_address,
        recipient_name=matched_contact.get("name", ""),
        sender_balance=balance_value,
        is_contact=True  # From contacts list
    )

    # Store risk assessment in database
    create_risk_assessment(
        db=db,
        user_wallet_id=request.walletId,
        amount=amount,
        recipient_address=to_address,
        recipient_name=matched_contact.get("name"),
        risk_score=risk_assessment["riskScore"],
        risk_level=risk_assessment["riskLevel"],
        decision=risk_assessment["decision"],
        reason=risk_assessment.get("reason"),
        balance_at_time=balance_value,
        balance_ratio=risk_assessment.get("balanceRatio"),
        is_contact=True
    )

    # Add risk assessment to plan
    plan["riskAssessment"] = risk_assessment

    if plan.get("needsConfirmation") and request.execute:
        raise HTTPException(
            status_code=400,
            detail="Agent requested confirmation before executing. Review the plan first."
        )

    # If just parsing (not executing), return plan with risk assessment
    if not request.execute:
        return AgentPayResponse(
            success=True,
            plan=plan,
            message=f"Plan created with {risk_assessment['riskLevel']} risk. Resend with execute=true to send the payment."
        )

    # Block high-risk payments that were denied by guardian
    if risk_assessment["decision"] == "deny":
        raise HTTPException(
            status_code=403,
            detail=f"Payment denied by security guardian: {risk_assessment.get('reason', 'High risk detected')}"
        )

    # Final balance check (redundant but explicit)
    if balance_value < amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance ({balance} USDC) to send {amount} USDC."
        )

    # Execute the transaction
    transaction = api_instance.transfer_usdc(
        from_wallet_id=request.walletId,
        to_address=to_address,
        amount=amount
    )

    record_payment_history(
        db=db,
        scheduled_payment_id=None,
        from_wallet_id=request.walletId,
        to_address=to_address,
        amount=amount,
        status=transaction.get("status", "pending"),
        transaction_hash=transaction.get("txHash")
    )

    return AgentPayResponse(
        success=True,
        plan=plan,
        transaction=transaction,
        message="Payment initiated successfully."
    )


async def _handle_stock_purchase(request: AgentPayRequest, db: Session) -> AgentPayResponse:
    """Handle stock purchase request."""
    # Parse stock purchase intent
    stock_plan = payment_agent._plan_stock_purchase(request.command)
    
    if stock_plan.get("action") != "buy_stock":
        raise HTTPException(status_code=400, detail="Could not parse stock purchase intent.")
    
    # Check if a stock symbol is explicitly mentioned in the command
    # This handles cases where user selects a stock from recommendations
    selected_symbol = stock_plan.get("stockSymbol")
    if not selected_symbol:
        # Try to extract symbol from command (might be appended by frontend)
        import re
        # Look for 3-5 letter uppercase sequences (stock symbols) at the end of command
        # This handles cases where user says "Buy stock for 10 USDC BNKX"
        command_upper = request.command.upper()
        # First, try to find stock symbols in the repository from the command
        from stock_agent import stock_agent
        # Get all stock symbols
        all_stocks = stock_agent.repo.list_all()
        stock_symbols = [s.get("symbol", "").upper() for s in all_stocks if s.get("symbol")]
        
        # Look for any stock symbol in the command
        for symbol in stock_symbols:
            if symbol in command_upper:
                # Check if it's a word boundary match (not part of another word)
                pattern = r'\b' + re.escape(symbol) + r'\b'
                if re.search(pattern, command_upper):
                    selected_symbol = symbol
                    break
        
        # Fallback: try regex pattern matching
        if not selected_symbol:
            symbol_match = re.search(r'\b([A-Z]{3,5})\b', command_upper)
            if symbol_match:
                potential_symbol = symbol_match.group(1)
                # Verify it's a valid stock symbol
                if stock_agent.repo.find(potential_symbol):
                    selected_symbol = potential_symbol
    
    # Prepare intent payload for stock agent
    intent_payload = {
        "userId": request.walletId,
        "intent": "stock_purchase",
        "entities": {
            "amount": stock_plan.get("amount"),
            "currency": stock_plan.get("currency", "USDC"),
            "stockRequest": {
                "sector": stock_plan.get("sector"),
                "preference": stock_plan.get("preference"),
                "budget": stock_plan.get("amount")
            },
            "selectedStock": selected_symbol,
            "rawText": request.command
        }
    }
    
    # Process with stock agent
    stock_result = stock_agent.process(intent_payload)
    
    status = stock_result.get("status")
    
    if status == "AWAITING_SELECTION":
        # Return recommendations for user to select
        return AgentPayResponse(
            success=True,
            plan={
                "action": "buy_stock",
                "recommendations": stock_result.get("recommendations", []),
                "prompt": stock_result.get("prompt"),
                "needsSelection": True
            },
            message=stock_result.get("prompt", "Please select a stock from the recommendations.")
        )
    
    if status == "INVALID_SELECTION":
        raise HTTPException(status_code=400, detail=stock_result.get("message", "Invalid stock selection."))
    
    if status == "NO_MATCHES":
        raise HTTPException(status_code=400, detail=stock_result.get("message", "No stocks matched your criteria."))
    
    if status != "READY_FOR_GUARDIAN":
        raise HTTPException(status_code=400, detail=f"Unexpected stock agent status: {status}")
    
    # Stock selected, route to guardian for risk assessment
    selection = stock_result.get("selection", {})
    payload = stock_result.get("payload", {})
    
    # Get balance for risk assessment
    api_instance, user = _get_circle_client_for_wallet(db, request.walletId)
    balance = api_instance.get_wallet_balance(request.walletId)
    
    try:
        balance_value = float(balance)
    except (TypeError, ValueError):
        balance_value = 0.0
    
    amount = payload.get("entities", {}).get("amount", 0)
    recipient_address = payload.get("entities", {}).get("recipientAddress", "")
    recipient_name = payload.get("entities", {}).get("recipientName", "")
    
    # Run Guardian risk assessment
    risk_assessment = guardian_agent.assess_payment_risk(
        amount=amount,
        recipient_address=recipient_address,
        recipient_name=recipient_name,
        sender_balance=balance_value,
        is_contact=False  # Stock purchase, not a contact
    )
    
    # Store risk assessment
    create_risk_assessment(
        db=db,
        user_wallet_id=request.walletId,
        amount=amount,
        recipient_address=recipient_address,
        recipient_name=recipient_name,
        risk_score=risk_assessment["riskScore"],
        risk_level=risk_assessment["riskLevel"],
        decision=risk_assessment["decision"],
        reason=risk_assessment.get("reason"),
        balance_at_time=balance_value,
        balance_ratio=risk_assessment.get("balanceRatio"),
        is_contact=False
    )
    
    # Build response plan
    plan = {
        "action": "buy_stock",
        "stock": selection,
        "amount": amount,
        "currency": "USDC",
        "riskAssessment": risk_assessment
    }
    
    # If not executing, return plan
    if not request.execute:
        return AgentPayResponse(
            success=True,
            plan=plan,
            message=f"Stock purchase plan created for {selection.get('symbol')} with {risk_assessment['riskLevel']} risk. Resend with execute=true to complete the purchase."
        )
    
    # Block high-risk purchases
    if risk_assessment["decision"] == "deny":
        raise HTTPException(
            status_code=403,
            detail=f"Stock purchase denied by security guardian: {risk_assessment.get('reason', 'High risk detected')}"
        )
    
    # Final balance check
    if balance_value < amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance ({balance} USDC) to purchase {amount} USDC worth of stock."
        )
    
    # Execute the transaction (stock purchase as payment to stock address)
    transaction = api_instance.transfer_usdc(
        from_wallet_id=request.walletId,
        to_address=recipient_address,
        amount=amount
    )
    
    # Record payment history
    record_payment_history(
        db=db,
        scheduled_payment_id=None,
        from_wallet_id=request.walletId,
        to_address=recipient_address,
        amount=amount,
        status=transaction.get("status", "pending"),
        transaction_hash=transaction.get("txHash")
    )
    
    return AgentPayResponse(
        success=True,
        plan=plan,
        transaction=transaction,
        message=f"Stock purchase for {selection.get('symbol')} initiated successfully."
    )


# ============================================
# CONTACTS ENDPOINTS
# ============================================

class CreateContactRequest(BaseModel):
    walletId: str
    name: str
    address: str

class ContactResponse(BaseModel):
    id: str
    name: str
    address: str
    created_at: int

@app.post("/api/contacts")
async def create_contact_endpoint(
    request: CreateContactRequest,
    db: Session = Depends(get_db)
):
    """Create a new contact"""
    try:
        # Validate address format (basic check)
        if not request.address or len(request.address) < 10:
            raise HTTPException(status_code=400, detail="Invalid address format")
        
        contact = create_contact(
            db=db,
            user_wallet_id=request.walletId,
            name=request.name,
            address=request.address
        )
        
        return {
            "success": True,
            "contact": {
                "id": contact.id,
                "name": contact.name,
                "address": contact.address,
                "created_at": contact.created_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/contacts")
async def get_contacts_endpoint(
    walletId: str = Query(..., description="Wallet ID"),
    db: Session = Depends(get_db)
):
    """Get user's contacts"""
    try:
        contacts = get_user_contacts(db, walletId)
        
        return {
            "success": True,
            "contacts": [
                {
                    "id": c.id,
                    "name": c.name,
                    "address": c.address,
                    "created_at": c.created_at
                }
                for c in contacts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/contacts/{contact_id}")
async def delete_contact_endpoint(
    contact_id: str,
    walletId: str = Query(..., description="Wallet ID"),
    db: Session = Depends(get_db)
):
    """Delete a contact"""
    try:
        success = delete_contact(db, contact_id, walletId)
        
        if not success:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        return {
            "success": True,
            "message": "Contact deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    wallet_id: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

# Simple JWT secret (in production, use environment variable)
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"

def create_access_token(user_id: str, email: str) -> str:
    """Create JWT token"""
    if JWT_AVAILABLE:
        try:
            payload = {
                "sub": user_id,
                "email": email,
                "exp": datetime.utcnow() + timedelta(days=7)
            }
            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
            return token
        except Exception as e:
            print(f"JWT encoding error: {e}")
            # Fallback to simple token
            return f"token-{user_id}-{datetime.utcnow().timestamp()}"
    else:
        # Fallback: return a simple token if JWT is not available
        return f"token-{user_id}-{datetime.utcnow().timestamp()}"

def get_user_from_token(authorization: str, db: Session) -> Optional[User]:
    """Extract user from JWT token (for validation only)"""
    if not authorization:
        return None

    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "").strip()

        if JWT_AVAILABLE and not token.startswith("token-"):
            # Decode JWT
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                return db.query(User).filter(User.id == user_id).first()
        else:
            # Fallback: parse simple token format "token-{user_id}-{timestamp}"
            if token.startswith("token-"):
                parts = token.split("-")
                if len(parts) >= 2:
                    user_id = parts[1]
                    return db.query(User).filter(User.id == user_id).first()
    except Exception as e:
        print(f"Token decode error: {e}")
        return None

    return None

def validate_wallet_access(wallet_id: str, authorization: str, db: Session):
    """Validate that the wallet_id belongs to the authenticated user"""
    user = get_user_from_token(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if user.wallet_id != wallet_id:
        raise HTTPException(status_code=403, detail="Access denied: This wallet does not belong to you")

@app.post("/api/auth/register")
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user (no automatic wallet creation)"""
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create user account without wallet
        user = create_user(
            db=db,
            email=request.email,
            password=request.password,
            name=request.name
        )
        
        token = create_access_token(user.id, user.email)
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "wallet_id": user.wallet_id,
                "wallet_address": user.wallet_address
            },
            "message": "Account created successfully. Add your Circle API key to generate your wallet."
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/login")
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login user"""
    try:
        user = authenticate_user(db, request.email, request.password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token = create_access_token(user.id, user.email)
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "wallet_id": user.wallet_id,
                "wallet_address": user.wallet_address,
                "has_api_key": bool(user.circle_api_key)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# WALLET GENERATION ENDPOINT
# ============================================

class GenerateWalletRequest(BaseModel):
    api_key: str
    user_id: str  # User ID from frontend (from localStorage)

@app.post("/api/wallet/generate")
async def generate_wallet(
    request: GenerateWalletRequest,
    db: Session = Depends(get_db)
):
    """Generate wallet for authenticated user using their Circle API key"""
    try:
        # Validate API key format (basic check)
        api_key = request.api_key.strip()
        if not api_key or len(api_key) < 10:
            raise HTTPException(status_code=400, detail="Invalid API key format")
        
        # Get user from database
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user already has a wallet
        if user.wallet_id:
            raise HTTPException(status_code=400, detail="User already has a wallet. Cannot generate a new one.")
        
        # Check if user already has an API key (cannot update)
        if user.circle_api_key:
            raise HTTPException(status_code=400, detail="API key already set. Cannot update.")
        
        # Create wallet using user's API key
        try:
            wallet_info = create_wallet_for_user_with_api_key(
                api_key=api_key,
                user_name=user.name,
                user_email=user.email
            )
            
            # Update user record with API key and wallet info
            user.circle_api_key = api_key
            user.wallet_id = wallet_info["wallet_id"]
            user.wallet_address = wallet_info["wallet_address"]
            user.entity_secret = wallet_info["entity_secret"]
            user.wallet_set_id = wallet_info["wallet_set_id"]
            
            db.commit()
            db.refresh(user)
            
            return {
                "success": True,
                "message": "Wallet generated successfully",
                "wallet": {
                    "wallet_id": user.wallet_id,
                    "wallet_address": user.wallet_address
                }
            }
        except Exception as e:
            error_msg = str(e)
            print(f"Error creating wallet: {error_msg}")
            raise HTTPException(status_code=400, detail=f"Failed to create wallet: {error_msg}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wallet generation failed: {str(e)}")

# ============================================
# USER PROFILE ENDPOINT
# ============================================

@app.get("/api/user/profile")
async def get_user_profile(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get user profile information"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Mask API key for display (show last 4 characters)
        api_key_display = None
        if user.circle_api_key:
            api_key_display = f"****-****-****-{user.circle_api_key[-4:]}" if len(user.circle_api_key) > 4 else "****"
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "wallet_id": user.wallet_id,
                "wallet_address": user.wallet_address,
                "has_api_key": bool(user.circle_api_key),
                "has_wallet": bool(user.wallet_id),
                "api_key_display": api_key_display
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# VOICE TRANSCRIPTION ENDPOINT
# ============================================
# Note: This endpoint is completely separate from transaction functionality
# It only handles audio transcription and does not interact with payments or wallets

class TranscribeResponse(BaseModel):
    """Response model for transcription endpoint"""
    success: bool
    transcription: Optional[str] = None
    error: Optional[str] = None
    language: Optional[str] = None

@app.post("/api/transcribe-audio", response_model=TranscribeResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe (WAV, MP3, etc.)"),
    language: Optional[str] = Query("en", description="Language code (default: en)")
):
    """
    Transcribe audio file using ElevenLabs API.
    
    This endpoint is completely isolated from transaction functionality.
    It only handles audio transcription and returns text.
    
    Args:
        audio_file: Audio file to transcribe
        language: Language code (default: "en")
    
    Returns:
        Transcription result with text or error message
    """
    # Check if voice transcription is available
    if not VOICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Voice transcription not available. Please install elevenlabs package and configure ELEVENLABS_API_KEY."
        )
    
    # Check if API key is configured
    if not settings.elevenlabs_api_key:
        raise HTTPException(
            status_code=503,
            detail="ElevenLabs API key not configured. Please set ELEVENLABS_API_KEY in environment variables."
        )
    
    try:
        # Initialize transcription handler
        transcriber = TranscriptionHandler(api_key=settings.elevenlabs_api_key)
        
        # Read audio file
        audio_bytes = await audio_file.read()
        
        # Validate file size (max 25MB for ElevenLabs)
        max_size = 25 * 1024 * 1024  # 25MB
        if len(audio_bytes) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"Audio file too large. Maximum size is 25MB, got {len(audio_bytes) / 1024 / 1024:.2f}MB"
            )
        
        # Transcribe audio
        result = transcriber.transcribe_file(audio_bytes, language=language)
        
        if result["success"]:
            return TranscribeResponse(
                success=True,
                transcription=result["text"],
                language=result["language"]
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {result.get('error', 'Unknown error')}"
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"[TRANSCRIBE] Error transcribing audio: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

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
