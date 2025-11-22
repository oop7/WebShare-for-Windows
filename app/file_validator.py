"""
File validation and security utilities for WebShare
Handles file size checks, filename sanitization, and extension validation
"""

import os
import re
import unicodedata
from typing import Tuple, Optional


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename to prevent path traversal and other security issues
    
    Args:
        filename: Original filename
        max_length: Maximum allowed filename length
        
    Returns:
        str: Sanitized filename
    """
    # Get the filename without directory path
    filename = os.path.basename(filename)
    
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)
    
    # Remove any null bytes
    filename = filename.replace('\x00', '')
    
    # Replace path separators and other dangerous characters
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*', '\0']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = 'unnamed_file'
    
    # Truncate if too long, preserving extension
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext)
        filename = name[:max_name_length] + ext
    
    return filename


def validate_file_size(file_size: int, max_size: int) -> Tuple[bool, Optional[str]]:
    """
    Validate file size against maximum allowed
    
    Args:
        file_size: Size of the file in bytes
        max_size: Maximum allowed size in bytes
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if file_size <= 0:
        return False, "File is empty"
    
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"File size exceeds maximum allowed size of {max_mb:.1f} MB"
    
    return True, None


def validate_total_storage(current_size: int, new_file_size: int, max_total: int) -> Tuple[bool, Optional[str]]:
    """
    Validate that adding a new file won't exceed total storage limit
    
    Args:
        current_size: Current total storage used in bytes
        new_file_size: Size of the new file in bytes
        max_total: Maximum total storage allowed in bytes
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if current_size + new_file_size > max_total:
        max_gb = max_total / (1024 * 1024 * 1024)
        return False, f"Total storage limit of {max_gb:.1f} GB would be exceeded"
    
    return True, None


def validate_file_count(current_count: int, max_count: int) -> Tuple[bool, Optional[str]]:
    """
    Validate that file count doesn't exceed maximum
    
    Args:
        current_count: Current number of files
        max_count: Maximum allowed number of files
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if current_count >= max_count:
        return False, f"Maximum file count of {max_count} reached"
    
    return True, None


def validate_extension(filename: str, allowed: list, blocked: list) -> Tuple[bool, Optional[str]]:
    """
    Validate file extension against allowed and blocked lists
    
    Args:
        filename: Name of the file
        allowed: List of allowed extensions (empty list means all allowed)
        blocked: List of blocked extensions
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    ext = os.path.splitext(filename)[1].lower()
    
    # Check if extension is empty
    if not ext:
        return False, "File must have an extension"
    
    # Check blocked extensions first
    if ext in [b.lower() for b in blocked]:
        return False, f"File type '{ext}' is not allowed for security reasons"
    
    # Check allowed extensions (if list is not empty)
    if allowed:
        if ext not in [a.lower() for a in allowed]:
            allowed_str = ', '.join(allowed)
            return False, f"Only these file types are allowed: {allowed_str}"
    
    return True, None


def get_safe_filepath(upload_dir: str, filename: str) -> str:
    """
    Generate a safe file path, handling duplicate filenames
    
    Args:
        upload_dir: Directory where file will be saved
        filename: Desired filename
        
    Returns:
        str: Safe file path with unique filename if needed
    """
    base_path = os.path.join(upload_dir, filename)
    
    # If file doesn't exist, use as-is
    if not os.path.exists(base_path):
        return base_path
    
    # Handle duplicate by adding a number
    name, ext = os.path.splitext(filename)
    counter = 1
    
    while True:
        new_filename = f"{name}_{counter}{ext}"
        new_path = os.path.join(upload_dir, new_filename)
        if not os.path.exists(new_path):
            return new_path
        counter += 1
        
        # Safety check to prevent infinite loop
        if counter > 9999:
            # Use timestamp as last resort
            import time
            timestamp = int(time.time())
            new_filename = f"{name}_{timestamp}{ext}"
            return os.path.join(upload_dir, new_filename)


def get_storage_stats(upload_dir: str) -> dict:
    """
    Get storage statistics for the upload directory
    
    Args:
        upload_dir: Directory to analyze
        
    Returns:
        dict: Dictionary with file_count and total_size_bytes
    """
    file_count = 0
    total_size = 0
    
    try:
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                file_path = os.path.join(upload_dir, filename)
                if os.path.isfile(file_path):
                    file_count += 1
                    total_size += os.path.getsize(file_path)
    except Exception as e:
        print(f"Error getting storage stats: {e}")
    
    return {
        'file_count': file_count,
        'total_size_bytes': total_size
    }


def is_safe_path(base_dir: str, path: str) -> bool:
    """
    Check if a path is safe (doesn't escape the base directory)
    
    Args:
        base_dir: Base directory that should contain the path
        path: Path to check
        
    Returns:
        bool: True if path is safe, False otherwise
    """
    # Get absolute paths
    abs_base = os.path.abspath(base_dir)
    abs_path = os.path.abspath(os.path.join(base_dir, path))
    
    # Check if the path starts with base directory
    return abs_path.startswith(abs_base)
