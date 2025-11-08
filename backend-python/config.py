"""
============================================
CONFIGURATION SETTINGS
============================================

Loads environment variables and provides
application configuration.
"""

import os
from dotenv import load_dotenv
from typing import List

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # ============================================
    # CIRCLE API
    # ============================================
    circle_api_key: str = os.getenv("CIRCLE_API_KEY", "")
    circle_wallet_id: str = os.getenv("CIRCLE_WALLET_ID", "")
    circle_entity_secret: str = os.getenv("CIRCLE_ENTITY_SECRET", "")
    circle_api_base: str = "https://api.circle.com/v1"
    
    # ============================================
    # ARC BLOCKCHAIN
    # ============================================
    arc_rpc_url: str = "https://rpc-testnet.arc.network"
    arc_chain_id: int = 462050
    arc_explorer_url: str = "https://testnet.arcscan.com"
    
    # Circle blockchain identifier for Arc
    circle_blockchain: str = "ARC-TESTNET"
    
    # ============================================
    # AI CONFIGURATION
    # ============================================
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    ai_model: str = "gpt-3.5-turbo"
    
    # ============================================
    # DATABASE
    # ============================================
    database_url: str = "sqlite:///./arcpay.db"
    
    # ============================================
    # API SERVER
    # ============================================
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # ============================================
    # SCHEDULER
    # ============================================
    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 60
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()

