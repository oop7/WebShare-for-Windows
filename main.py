#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebShare for Windows
A file sharing application with a PySide6 (Qt6) GUI and Flask web server
"""

import sys
import os
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from app import WebShareApp
from app.version import __version__
from app.logger import init_logger
from app.config import get_config


def excepthook(exc_type, exc_value, exc_tb):
    """Global exception handler to show error messages in a user-friendly way"""
    # Format the error
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    
    # Log the error using the logging system
    try:
        from app.logger import get_logger
        logger = get_logger()
        logger.critical(f"Unhandled exception: {str(exc_value)}", exc_info=True)
    except:
        # Fallback to old error_log.txt if logger fails
        try:
            log_file = "error_log.txt"
            with open(log_file, "a") as f:
                f.write(f"\n\n{'='*50}\n")
                f.write(f"WebShare v{__version__} Error\n")
                f.write(f"{'='*50}\n")
                f.write(tb)
        except:
            pass  # If logging fails, we still want to show the error
    
    # Display error message to user
    error_box = QMessageBox()
    error_box.setWindowTitle("WebShare Error")
    error_box.setText(f"An unexpected error occurred: {str(exc_value)}")
    error_box.setInformativeText("Error details have been written to logs/error.log")
    error_box.setDetailedText(tb)
    error_box.setIcon(QMessageBox.Critical)
    error_box.exec()
    
    # Exit the application
    sys.exit(1)


def main():
    """Main application entry point"""
    try:
        # Set up global exception handler
        sys.excepthook = excepthook
        
        # Initialize configuration
        config = get_config()
        
        # Initialize logging
        log_dir = config.get('logging', 'log_folder', 'logs')
        init_logger(log_dir)
        
        from app.logger import get_logger
        logger = get_logger()
        logger.info(f"Starting WebShare for Windows v{__version__}")
        
        # Make sure required directories exist
        upload_dir = config.get('storage', 'upload_folder', 'uploads')
        if not os.path.isabs(upload_dir):
            upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), upload_dir)
        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            logger.info(f"Created upload directory: {upload_dir}")
        
        temp_dir = config.get('storage', 'temp_folder', 'temp')
        if not os.path.isabs(temp_dir):
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), temp_dir)
        
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            logger.info(f"Created temp directory: {temp_dir}")
            
        # Create and run Qt application
        qt_app = QApplication(sys.argv)
        webshare = WebShareApp()
        webshare.show()
        
        logger.info("Application started successfully")
        exit_code = qt_app.exec()
        
        logger.info("Application closed")
        sys.exit(exit_code)
    except Exception as e:
        excepthook(type(e), e, e.__traceback__)


if __name__ == '__main__':
    main()
