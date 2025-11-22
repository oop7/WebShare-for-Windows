"""
Unit tests for logging functionality
"""

import pytest
import os
import tempfile
import logging
from app.logger import WebShareLogger, init_logger, get_logger


class TestWebShareLogger:
    """Test cases for WebShareLogger class"""
    
    def test_logger_initialization(self):
        """Test that logger initializes properly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WebShareLogger(name="TestLogger", log_dir=tmpdir)
            
            assert logger.logger is not None
            assert os.path.exists(tmpdir)
    
    def test_log_files_created(self):
        """Test that log files are created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WebShareLogger(name="TestLogger", log_dir=tmpdir)
            logger.info("Test message")
            
            # Check that log files exist
            log_file = os.path.join(tmpdir, 'webshare.log')
            error_log = os.path.join(tmpdir, 'error.log')
            
            assert os.path.exists(log_file)
            assert os.path.exists(error_log)
    
    def test_log_levels(self):
        """Test different log levels"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WebShareLogger(name="TestLogger", log_dir=tmpdir)
            
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")
            
            log_file = os.path.join(tmpdir, 'webshare.log')
            assert os.path.exists(log_file)
            
            # Check that messages were written
            with open(log_file, 'r') as f:
                content = f.read()
                assert 'Info message' in content
                assert 'Warning message' in content
                assert 'Error message' in content
    
    def test_error_log_separation(self):
        """Test that errors are logged separately"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WebShareLogger(name="TestLogger", log_dir=tmpdir)
            
            logger.info("Info message")
            logger.error("Error message")
            
            error_log = os.path.join(tmpdir, 'error.log')
            with open(error_log, 'r') as f:
                content = f.read()
                assert 'Error message' in content
                assert 'Info message' not in content
    
    def test_log_upload(self):
        """Test logging file uploads"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WebShareLogger(name="TestLogger", log_dir=tmpdir)
            logger.log_upload("test.txt", 1024, "192.168.1.1")
            
            log_file = os.path.join(tmpdir, 'webshare.log')
            with open(log_file, 'r') as f:
                content = f.read()
                assert 'test.txt' in content
                assert '1024' in content
                assert '192.168.1.1' in content
    
    def test_log_download(self):
        """Test logging file downloads"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WebShareLogger(name="TestLogger", log_dir=tmpdir)
            logger.log_download("document.pdf", "192.168.1.2")
            
            log_file = os.path.join(tmpdir, 'webshare.log')
            with open(log_file, 'r') as f:
                content = f.read()
                assert 'document.pdf' in content
                assert '192.168.1.2' in content
    
    def test_log_server_events(self):
        """Test logging server start/stop"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WebShareLogger(name="TestLogger", log_dir=tmpdir)
            logger.log_server_start("0.0.0.0", 5000)
            logger.log_server_stop()
            
            log_file = os.path.join(tmpdir, 'webshare.log')
            with open(log_file, 'r') as f:
                content = f.read()
                assert '0.0.0.0:5000' in content
                assert 'Server started' in content
                assert 'Server stopped' in content


def test_init_logger():
    """Test logger initialization function"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = init_logger(log_dir=tmpdir)
        assert logger is not None
        assert isinstance(logger, WebShareLogger)


def test_get_logger_singleton():
    """Test that get_logger returns singleton instance"""
    logger1 = get_logger()
    logger2 = get_logger()
    assert logger1 is logger2
