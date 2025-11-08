"""
============================================
PAYMENT SCHEDULER
============================================

Background job that runs periodically to check
for due payments and execute them.

Uses APScheduler for cron-like functionality.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from database import SessionLocal, get_due_payments, update_payment_after_execution, record_payment_history
from circle_integration import circle_api
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaymentScheduler:
    """
    Background scheduler for automatic payment execution.
    
    Runs every minute (configurable) and:
    1. Checks database for due payments
    2. Executes each payment via Circle API
    3. Records results
    4. Schedules next execution
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.running = False
    
    def start(self):
        """Start the scheduler"""
        if not settings.scheduler_enabled:
            logger.info("Scheduler is disabled in config")
            return
        
        interval = settings.scheduler_interval_seconds
        
        self.scheduler.add_job(
            self.process_due_payments,
            'interval',
            seconds=interval,
            id='payment_processor',
            name='Process Due Payments',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.running = True
        logger.info(f"✓ Payment scheduler started (interval: {interval}s)")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.running = False
            logger.info("✓ Payment scheduler stopped")
    
    def process_due_payments(self):
        """
        Main job function that executes payments.
        
        This runs every minute (or configured interval).
        """
        logger.info("🔄 Checking for due payments...")
        
        db = SessionLocal()
        
        try:
            # Get payments that need to execute
            due_payments = get_due_payments(db)
            
            if not due_payments:
                logger.info("✓ No payments due at this time")
                return
            
            logger.info(f"Found {len(due_payments)} payments to process")
            
            success_count = 0
            failure_count = 0
            
            for payment in due_payments:
                try:
                    self._execute_payment(db, payment)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to execute payment {payment.id}: {e}")
                    failure_count += 1
                    
                    # Record failure
                    record_payment_history(
                        db=db,
                        scheduled_payment_id=payment.id,
                        from_wallet_id=payment.user_wallet_id,
                        to_address=payment.recipient_address,
                        amount=payment.amount,
                        status="failed",
                        error_message=str(e)
                    )
                    
                    # Update for retry
                    update_payment_after_execution(db, payment.id, success=False)
            
            logger.info(f"✓ Processed {len(due_payments)} payments (Success: {success_count}, Failed: {failure_count})")
        
        except Exception as e:
            logger.error(f"Error in payment processing: {e}")
        
        finally:
            db.close()
    
    def _execute_payment(self, db: Session, payment):
        """
        Execute a single payment.
        
        Args:
            db: Database session
            payment: ScheduledPayment object
        
        Raises:
            Exception if payment fails
        """
        logger.info(f"💸 Executing payment {payment.id}")
        logger.info(f"   From: {payment.user_wallet_id}")
        logger.info(f"   To: {payment.recipient_address}")
        logger.info(f"   Amount: {payment.amount} USDC")
        
        # Validate address
        if not circle_api.is_valid_address(payment.recipient_address):
            raise Exception("Invalid recipient address")
        
        # Check balance
        balance = circle_api.get_wallet_balance(payment.user_wallet_id)
        balance_float = float(balance)
        
        if balance_float < payment.amount:
            raise Exception(
                f"Insufficient balance: have {balance} USDC, need {payment.amount} USDC"
            )
        
        # Execute transfer
        transaction = circle_api.transfer_usdc(
            from_wallet_id=payment.user_wallet_id,
            to_address=payment.recipient_address,
            amount=payment.amount
        )
        
        transaction_id = transaction.get("transactionId")
        logger.info(f"✓ Transaction submitted: {transaction_id} (status: {transaction.get('status')})")
        
        # Wait a moment for transaction to process, then get transaction hash
        import time
        time.sleep(2)  # Wait 2 seconds for transaction to be processed
        
        # Get transaction details to retrieve txHash
        tx_hash = None
        if transaction_id:
            try:
                tx_status = circle_api.get_transaction_status(transaction_id)
                tx_hash = tx_status.get("txHash")
                if tx_hash:
                    logger.info(f"✓ Transaction hash: {tx_hash}")
            except Exception as e:
                logger.warning(f"Could not get transaction hash yet: {e}")
        
        # Record success (transaction may still be pending)
        record_payment_history(
            db=db,
            scheduled_payment_id=payment.id,
            from_wallet_id=payment.user_wallet_id,
            to_address=payment.recipient_address,
            amount=payment.amount,
            status="completed" if transaction.get("status") in ["COMPLETE", "CONFIRMED"] else "pending",
            transaction_hash=tx_hash
        )
        
        # Update next execution time
        # For one-time payments (interval_ms = 0), mark as completed after execution
        if payment.interval_ms == 0:
            # One-time payment - mark as completed, don't schedule again
            from database import cancel_scheduled_payment
            cancel_scheduled_payment(db, payment.id)
            logger.info(f"✓ One-time payment {payment.id} completed and cancelled")
        else:
            # Recurring payment - schedule next execution
            update_payment_after_execution(db, payment.id, success=True)
        
        logger.info(f"✓ Payment {payment.id} completed successfully")


# Global scheduler instance
payment_scheduler = PaymentScheduler()

