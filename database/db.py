import sqlite3
import os
import logging
from typing import Dict, Any, Optional, Tuple

# Set up logging
logger = logging.getLogger(__name__)

# Database file path
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'wallets.db')

# Ensure the data directory exists
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

def init_db():
    """Initialize the database and create tables if they don't exist."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Create wallets table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            telegram_id TEXT PRIMARY KEY,
            wallet_id TEXT NOT NULL,
            admin_key TEXT NOT NULL,
            inkey TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            balance_sat INTEGER DEFAULT 0
        )
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {str(e)}")
        
    finally:
        if conn:
            conn.close()

def user_has_wallet(telegram_id: str) -> bool:
    """Check if a user already has a wallet.
    
    Args:
        telegram_id: The Telegram user ID
        
    Returns:
        True if the user has a wallet, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM wallets WHERE telegram_id = ?", (telegram_id,))
        count = cursor.fetchone()[0]
        
        return count > 0
        
    except sqlite3.Error as e:
        logger.error(f"Database error checking user wallet: {str(e)}")
        return False
        
    finally:
        if conn:
            conn.close()

def save_wallet(telegram_id: str, wallet_id: str, admin_key: str, inkey: str) -> bool:
    """Save a new wallet to the database.
    
    Args:
        telegram_id: The Telegram user ID
        wallet_id: The LNBits wallet ID
        admin_key: The admin key for the wallet
        inkey: The inkey for receiving payments
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO wallets (telegram_id, wallet_id, admin_key, inkey) VALUES (?, ?, ?, ?)",
            (telegram_id, wallet_id, admin_key, inkey)
        )
        
        conn.commit()
        logger.info(f"Wallet saved for user {telegram_id}")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error saving wallet: {str(e)}")
        return False
        
    finally:
        if conn:
            conn.close()

def get_wallet(telegram_id: str) -> Optional[Dict[str, Any]]:
    """Get wallet information for a user.
    
    Args:
        telegram_id: The Telegram user ID
        
    Returns:
        Dictionary with wallet information or None if not found
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT wallet_id, admin_key, inkey, created_at, balance_sat FROM wallets WHERE telegram_id = ?",
            (telegram_id,)
        )
        
        row = cursor.fetchone()
        
        if row:
            return {
                "wallet_id": row["wallet_id"],
                "admin_key": row["admin_key"],
                "inkey": row["inkey"],
                "created_at": row["created_at"],
                "balance_sat": row["balance_sat"]
            }
        
        return None
        
    except sqlite3.Error as e:
        logger.error(f"Database error getting wallet: {str(e)}")
        return None
        
    finally:
        if conn:
            conn.close()

def update_wallet_balance(telegram_id: str, balance_sat: int) -> bool:
    """Update the wallet balance for a user.
    
    Args:
        telegram_id: The Telegram user ID
        balance_sat: The new balance in satoshis
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE wallets SET balance_sat = ? WHERE telegram_id = ?",
            (balance_sat, telegram_id)
        )
        
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Balance updated for user {telegram_id}: {balance_sat} sats")
            return True
        else:
            logger.warning(f"No wallet found for user {telegram_id} to update balance")
            return False
        
    except sqlite3.Error as e:
        logger.error(f"Database error updating wallet balance: {str(e)}")
        return False
        
    finally:
        if conn:
            conn.close()

# Initialize the database when the module is imported
init_db()
