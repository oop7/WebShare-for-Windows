"""
Logging configuration for WebShare
Provides structured logging with file rotation
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


class WebShareLogger:
    """Custom logger for WebShare application"""
    
    def __init__(self, name: str = "WebShare", log_dir: str = "logs"):
        """
        Initialize logger
        
        Args:
            name: Logger name
            log_dir: Directory to store log files
        """
        self.name = name
        self.log_dir = log_dir
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Setup logger with file and console handlers"""
        # Create logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler for all logs (rotating)
        log_file = os.path.join(self.log_dir, f'webshare.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # File handler for errors only
        error_log_file = os.path.join(self.log_dir, f'error.log')
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str) -> None:
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False) -> None:
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False) -> None:
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info)
    
    def log_upload(self, filename: str, size: int, ip_address: str) -> None:
        """Log file upload event"""
        self.info(f"File uploaded: {filename} ({size} bytes) from {ip_address}")
    
    def log_download(self, filename: str, ip_address: str) -> None:
        """Log file download event"""
        self.info(f"File downloaded: {filename} by {ip_address}")
    
    def log_delete(self, filename: str, ip_address: str = "local") -> None:
        """Log file deletion event"""
        self.info(f"File deleted: {filename} by {ip_address}")
    
    def log_server_start(self, host: str, port: int) -> None:
        """Log server start event"""
        self.info(f"Server started on {host}:{port}")
    
    def log_server_stop(self) -> None:
        """Log server stop event"""
        self.info("Server stopped")
    
    def log_connection(self, ip_address: str, user_agent: str = None) -> None:
        """Log client connection"""
        msg = f"Connection from {ip_address}"
        if user_agent:
            msg += f" - {user_agent}"
        self.info(msg)


# Global logger instance
_logger_instance = None


def get_logger() -> WebShareLogger:
    """
    Get the global logger instance
    
    Returns:
        WebShareLogger: Global logger object
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = WebShareLogger()
    return _logger_instance


def init_logger(log_dir: str = "logs") -> WebShareLogger:
    """
    Initialize the global logger
    
    Args:
        log_dir: Directory to store log files
        
    Returns:
        WebShareLogger: Initialized logger object
    """
    global _logger_instance
    _logger_instance = WebShareLogger(log_dir=log_dir)
    return _logger_instance
