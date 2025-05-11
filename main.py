#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebShare for Windows
A file sharing application with a PyQt5 GUI and Flask web server
"""

import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from app import WebShareApp
from app.version import __version__


def excepthook(exc_type, exc_value, exc_tb):
    """Global exception handler to show error messages in a user-friendly way"""
    # Format the error
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    
    # Log the error to file
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
    error_box.setInformativeText("Error details have been written to error_log.txt")
    error_box.setDetailedText(tb)
    error_box.setIcon(QMessageBox.Critical)
    error_box.exec_()
    
    # Exit the application
    sys.exit(1)


def main():
    """Main application entry point"""
    try:
        # Set up global exception handler
        sys.excepthook = excepthook
        
        # Make sure upload directory exists
        upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        # Create and run Qt application
        qt_app = QApplication(sys.argv)
        webshare = WebShareApp()
        webshare.show()
        sys.exit(qt_app.exec_())
    except Exception as e:
        excepthook(type(e), e, e.__traceback__)


if __name__ == '__main__':
    main()
