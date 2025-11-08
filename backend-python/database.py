"""
============================================
DATABASE MODELS AND OPERATIONS
============================================

SQLAlchemy models for storing payment schedules
and execution history.

Similar to the Cloudflare D1 version, but using
SQLAlchemy ORM for Python.
"""

from sqlalchemy import create_engine, Column, String, Float, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
from typing import List, Optional
import uuid

from config import settings

# ============================================
# DATABASE SETUP
# ============================================

# Create engine (connects to database)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# ============================================
# MODELS
# ============================================

class ScheduledPayment(Base):
    """
    Stores recurring payment schedules.
    
    Each row represents one scheduled payment that
    will execute automatically at intervals.
    """
    __tablename__ = "scheduled_payments"
    
    id = Column(String, primary_key=True, index=True)
    user_wallet_id = Column(String, nullable=False, index=True)
    recipient_address = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    interval_ms = Column(Integer, nullable=False)  # milliseconds
    next_execution_time = Column(Integer, nullable=False, index=True)  # Unix timestamp
    status = Column(String, default="active", index=True)
    created_at = Column(Integer, nullable=False)
    last_executed_at = Column(Integer, nullable=True)
    execution_count = Column(Integer, default=0)
    total_sent = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    
    # Relationship to history
    history = relationship("PaymentHistory", back_populates="scheduled_payment")


class PaymentHistory(Base):
    """
    Permanent record of all payment executions.
    
    Every time a payment runs (success or failure),
    we create a record here.
    """
    __tablename__ = "payment_history"
    
    id = Column(String, primary_key=True, index=True)
    scheduled_payment_id = Column(String, ForeignKey("scheduled_payments.id"), nullable=True)
    from_wallet_id = Column(String, nullable=False, index=True)
    to_address = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # completed, failed, pending
    transaction_hash = Column(String, nullable=True)
    executed_at = Column(Integer, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    
    # Relationship
    scheduled_payment = relationship("ScheduledPayment", back_populates="history")


# ============================================
# DATABASE INITIALIZATION
# ============================================

def init_db():
    """
    Create all tables in the database.
    Run this once at startup.
    """
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")


def get_db():
    """
    Dependency for FastAPI routes.
    
    Yields a database session, then closes it.
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# CRUD OPERATIONS
# ============================================

def create_scheduled_payment(
    db: Session,
    user_wallet_id: str,
    recipient_address: str,
    amount: float,
    interval_ms: int,
    description: str = None
) -> ScheduledPayment:
    """Create a new scheduled payment"""
    
    payment = ScheduledPayment(
        id=f"payment-{uuid.uuid4().hex[:12]}",
        user_wallet_id=user_wallet_id,
        recipient_address=recipient_address,
        amount=amount,
        interval_ms=interval_ms,
        next_execution_time=int(datetime.now().timestamp() * 1000),
        created_at=int(datetime.now().timestamp() * 1000),
        status="active",
        description=description
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    return payment


def get_due_payments(db: Session) -> List[ScheduledPayment]:
    """Get all payments that should execute now"""
    
    now_ms = int(datetime.now().timestamp() * 1000)
    
    return db.query(ScheduledPayment).filter(
        ScheduledPayment.status == "active",
        ScheduledPayment.next_execution_time <= now_ms
    ).all()


def update_payment_after_execution(
    db: Session,
    payment_id: str,
    success: bool
):
    """Update payment schedule after execution"""
    
    payment = db.query(ScheduledPayment).filter(
        ScheduledPayment.id == payment_id
    ).first()
    
    if not payment:
        return
    
    now_ms = int(datetime.now().timestamp() * 1000)
    
    if success:
        # Schedule next execution
        payment.next_execution_time = now_ms + payment.interval_ms
        payment.last_executed_at = now_ms
        payment.execution_count += 1
        payment.total_sent += payment.amount
    else:
        # Retry in 5 minutes on failure
        payment.next_execution_time = now_ms + (5 * 60 * 1000)
    
    db.commit()


def record_payment_history(
    db: Session,
    scheduled_payment_id: Optional[str],
    from_wallet_id: str,
    to_address: str,
    amount: float,
    status: str,
    transaction_hash: Optional[str] = None,
    error_message: Optional[str] = None
) -> PaymentHistory:
    """Record a payment execution in history"""
    
    history = PaymentHistory(
        id=f"history-{uuid.uuid4().hex[:12]}",
        scheduled_payment_id=scheduled_payment_id,
        from_wallet_id=from_wallet_id,
        to_address=to_address,
        amount=amount,
        status=status,
        transaction_hash=transaction_hash,
        executed_at=int(datetime.now().timestamp() * 1000),
        error_message=error_message
    )
    
    db.add(history)
    db.commit()
    db.refresh(history)
    
    return history


def get_user_scheduled_payments(
    db: Session,
    wallet_id: str
) -> List[ScheduledPayment]:
    """Get all active payments for a user"""
    
    return db.query(ScheduledPayment).filter(
        ScheduledPayment.user_wallet_id == wallet_id,
        ScheduledPayment.status == "active"
    ).order_by(ScheduledPayment.next_execution_time).all()


def get_payment_history(
    db: Session,
    wallet_id: str,
    limit: int = 50
) -> List[PaymentHistory]:
    """Get recent payment executions"""
    
    return db.query(PaymentHistory).filter(
        PaymentHistory.from_wallet_id == wallet_id
    ).order_by(PaymentHistory.executed_at.desc()).limit(limit).all()


def cancel_scheduled_payment(db: Session, payment_id: str):
    """Cancel a scheduled payment"""
    
    payment = db.query(ScheduledPayment).filter(
        ScheduledPayment.id == payment_id
    ).first()
    
    if payment:
        payment.status = "cancelled"
        db.commit()

