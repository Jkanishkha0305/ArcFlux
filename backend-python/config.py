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
from pydantic import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    # ============================================
    # CIRCLE API
    # ============================================
    circle_api_key: str = ""
    circle_wallet_id: str = ""
    circle_entity_secret: str = ""
    # Default to sandbox for testing (wallet_creation.py auto-detects based on API key)
    circle_api_base: str = "https://api-sandbox.circle.com/v1"
    
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
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_model: str = "gpt-3.5-turbo"
    
    # ============================================
    # DATABASE
    # ============================================
    database_url: str = "sqlite:///./arcflux.db"
    
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
    
    def __init__(self, **kwargs):
        # Load from environment variables with fallback to defaults
        super().__init__(**kwargs)
        # Override with explicit os.getenv for compatibility
        self.circle_api_key = os.getenv("CIRCLE_API_KEY", self.circle_api_key)
        self.circle_wallet_id = os.getenv("CIRCLE_WALLET_ID", self.circle_wallet_id)
        self.circle_entity_secret = os.getenv("CIRCLE_ENTITY_SECRET", self.circle_entity_secret)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_api_key)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()

