"""
Unit tests for configuration management
"""

import pytest
import os
import json
import tempfile
from app.config import Config, get_config, DEFAULT_CONFIG


class TestConfig:
    """Test cases for Config class"""
    
    def test_default_config_creation(self):
        """Test that default configuration is created properly"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            # Remove the file so config creates it
            os.unlink(config_path)
            config = Config(config_path)
            
            # Check that file was created
            assert os.path.exists(config_path)
            
            # Verify default values
            assert config.get('server', 'port') == 5000
            assert config.get('server', 'host') == '0.0.0.0'
            assert config.get('upload', 'max_file_size_mb') == 500
            assert config.get('security', 'password_protected') == False
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)
    
    def test_load_existing_config(self):
        """Test loading an existing configuration file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            test_config = {
                'server': {'port': 8080, 'host': '127.0.0.1'},
                'security': {'password_protected': True}
            }
            json.dump(test_config, f)
            config_path = f.name
        
        try:
            config = Config(config_path)
            
            # Check custom values
            assert config.get('server', 'port') == 8080
            assert config.get('server', 'host') == '127.0.0.1'
            assert config.get('security', 'password_protected') == True
            
            # Check that defaults are still available
            assert config.get('upload', 'max_file_size_mb') == 500
        finally:
            os.unlink(config_path)
    
    def test_get_with_default(self):
        """Test getting values with default fallback"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            os.unlink(config_path)
            config = Config(config_path)
            
            # Get non-existent value with default
            assert config.get('nonexistent', 'key', 'default_value') == 'default_value'
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)
    
    def test_set_config_value(self):
        """Test setting configuration values"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            os.unlink(config_path)
            config = Config(config_path)
            
            # Set a value
            config.set('server', 'port', 9000)
            assert config.get('server', 'port') == 9000
            
            # Save and reload
            config.save_config()
            config2 = Config(config_path)
            assert config2.get('server', 'port') == 9000
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)
    
    def test_get_max_file_size_bytes(self):
        """Test conversion of file size to bytes"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            os.unlink(config_path)
            config = Config(config_path)
            
            # Default 500 MB should be 500 * 1024 * 1024 bytes
            assert config.get_max_file_size_bytes() == 500 * 1024 * 1024
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)
    
    def test_is_extension_allowed(self):
        """Test file extension validation"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            os.unlink(config_path)
            config = Config(config_path)
            
            # Test blocked extensions
            assert not config.is_extension_allowed('malware.exe')
            assert not config.is_extension_allowed('script.bat')
            assert not config.is_extension_allowed('virus.ps1')
            
            # Test allowed extensions (when no whitelist)
            assert config.is_extension_allowed('document.pdf')
            assert config.is_extension_allowed('image.jpg')
            assert config.is_extension_allowed('archive.zip')
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)
    
    def test_extension_whitelist(self):
        """Test extension whitelist functionality"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            test_config = {
                'upload': {
                    'allowed_extensions': ['.jpg', '.png', '.pdf'],
                    'blocked_extensions': []
                }
            }
            json.dump(test_config, f)
            config_path = f.name
        
        try:
            config = Config(config_path)
            
            # Only whitelisted extensions should be allowed
            assert config.is_extension_allowed('photo.jpg')
            assert config.is_extension_allowed('image.png')
            assert config.is_extension_allowed('doc.pdf')
            assert not config.is_extension_allowed('video.mp4')
            assert not config.is_extension_allowed('archive.zip')
        finally:
            os.unlink(config_path)


def test_get_config_singleton():
    """Test that get_config returns singleton instance"""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2
