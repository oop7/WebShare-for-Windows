"""
Authentication utilities for WebShare
Handles password hashing and session management
"""

from functools import wraps
from flask import session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.config import get_config
from app.logger import get_logger

config = get_config()
logger = get_logger()

# Password hash storage
_password_hash = None


def init_password():
    """Initialize password hash from configuration"""
    global _password_hash
    if config.get('security', 'password_protected', False):
        password = config.get('security', 'password', '')
        if password:
            _password_hash = generate_password_hash(password)
            logger.info("Password protection enabled")
        else:
            logger.warning("Password protection enabled but no password set")


def check_password(password):
    """
    Check if provided password matches stored hash
    
    Args:
        password (str): Password to check
        
    Returns:
        bool: True if password is correct
    """
    return _password_hash and check_password_hash(_password_hash, password)


def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if config.get('security', 'password_protected', False):
            if not session.get('authenticated'):
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def is_authenticated():
    """Check if current session is authenticated"""
    if not config.get('security', 'password_protected', False):
        return True
    return session.get('authenticated', False)
