"""
============================================
DATABASE MODELS AND OPERATIONS
============================================

SQLAlchemy models for storing payment schedules
and execution history.

Similar to the Cloudflare D1 version, but using
SQLAlchemy ORM for Python.
"""

from sqlalchemy import create_engine, Column, String, Float, Integer, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
from typing import List, Optional
import uuid
import bcrypt

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


# ============================================
# CONTACT MODEL
# ============================================

class Contact(Base):
    """
    User's saved contacts (name + wallet address).
    """
    __tablename__ = "contacts"
    
    id = Column(String, primary_key=True, index=True)
    user_wallet_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    created_at = Column(Integer, nullable=False)


def create_contact(
    db: Session,
    user_wallet_id: str,
    name: str,
    address: str
) -> Contact:
    """Create a new contact"""
    
    contact = Contact(
        id=f"contact-{uuid.uuid4().hex[:12]}",
        user_wallet_id=user_wallet_id,
        name=name,
        address=address,
        created_at=int(datetime.now().timestamp() * 1000)
    )
    
    db.add(contact)
    db.commit()
    db.refresh(contact)
    
    return contact


def get_user_contacts(
    db: Session,
    wallet_id: str
) -> List[Contact]:
    """Get all contacts for a user"""
    
    return db.query(Contact).filter(
        Contact.user_wallet_id == wallet_id
    ).order_by(Contact.name).all()


def delete_contact(db: Session, contact_id: str, wallet_id: str):
    """Delete a contact (only if owned by user)"""
    
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_wallet_id == wallet_id
    ).first()
    
    if contact:
        db.delete(contact)
        db.commit()
        return True
    return False


# ============================================
# USER MODEL (for authentication)
# ============================================

class User(Base):
    """
    User accounts for authentication.
    """
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    circle_api_key = Column(String, nullable=True)  # User's Circle API key (plaintext)
    wallet_id = Column(String, nullable=True, index=True)  # Made nullable for initial creation
    wallet_address = Column(String, nullable=True)  # Wallet blockchain address
    entity_secret = Column(String, nullable=True)  # Encrypted entity secret (hex)
    wallet_set_id = Column(String, nullable=True)  # Wallet set ID
    created_at = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def create_user(
    db: Session,
    email: str,
    password: str,
    name: str,
    circle_api_key: str = None,
    wallet_id: str = None,
    wallet_address: str = None,
    entity_secret: str = None,
    wallet_set_id: str = None
) -> User:
    """Create a new user account"""
    
    # Check if user already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("User with this email already exists")
    
    user = User(
        id=f"user-{uuid.uuid4().hex[:12]}",
        email=email,
        password_hash=hash_password(password),
        name=name,
        circle_api_key=circle_api_key,
        wallet_id=wallet_id,
        wallet_address=wallet_address,
        entity_secret=entity_secret,
        wallet_set_id=wallet_set_id,
        created_at=int(datetime.now().timestamp() * 1000),
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user

