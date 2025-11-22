"""
File operations and utilities for WebShare
Handles file listing, saving, and rate limiting
"""

import os
import time
import uuid
import humanize

from app.config import get_config
from app.logger import get_logger

config = get_config()
logger = get_logger()

# Rate limiting dictionary (simple in-memory implementation)
upload_timestamps = {}


def get_formatted_size(file_path):
    """
    Get human-readable file size
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Human-readable file size (e.g., "1.2 MB")
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return humanize.naturalsize(size_bytes)
    except:
        return "Unknown size"


def get_files_with_sizes(upload_folder):
    """
    Get a list of files in the upload folder with their sizes
    
    Args:
        upload_folder (str): Path to upload folder
        
    Returns:
        list: List of tuples (filename, size)
    """
    try:
        files = os.listdir(upload_folder)
        result = []
        for filename in files:
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path):
                file_size = get_formatted_size(file_path)
                result.append((filename, file_size))
        return result
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}", exc_info=True)
        return []


def save_text_to_file(text, upload_folder):
    """
    Save shared text to a file
    
    Args:
        text (str): Text to save
        upload_folder (str): Path to upload folder
        
    Returns:
        str: Filename of saved file, or None on error
    """
    try:
        # Create a unique filename
        filename = f"shared_text_{int(time.time())}_{uuid.uuid4().hex[:6]}.txt"
        file_path = os.path.join(upload_folder, filename)
        
        # Write text to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
        return filename
    except Exception as e:
        logger.error(f"Error saving text to file: {str(e)}", exc_info=True)
        return None


def check_rate_limit(ip_address):
    """
    Check if IP has exceeded rate limit
    
    Args:
        ip_address (str): IP address to check
        
    Returns:
        bool: True if within limits, False if exceeded
    """
    if not config.get('security', 'rate_limit_enabled', True):
        return True
    
    max_uploads = config.get('security', 'max_uploads_per_minute', 10)
    current_time = time.time()
    
    # Clean old entries (older than 1 minute)
    if ip_address in upload_timestamps:
        upload_timestamps[ip_address] = [
            ts for ts in upload_timestamps[ip_address]
            if current_time - ts < 60
        ]
    
    # Check count
    if ip_address in upload_timestamps:
        if len(upload_timestamps[ip_address]) >= max_uploads:
            return False
    
    return True


def record_upload(ip_address):
    """
    Record an upload timestamp for rate limiting
    
    Args:
        ip_address (str): IP address to record
    """
    if ip_address not in upload_timestamps:
        upload_timestamps[ip_address] = []
    upload_timestamps[ip_address].append(time.time())
