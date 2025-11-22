"""
Configuration management for WebShare
Handles loading and validation of application settings
"""

import os
import json
from typing import Dict, Any, List

# Default configuration
DEFAULT_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 5000,
        "max_connections": 100
    },
    "upload": {
        "max_file_size_mb": 500,
        "max_total_size_gb": 10,
        "max_files": 1000,
        "allowed_extensions": [],  # Empty means all allowed
        "blocked_extensions": [
            ".exe", ".bat", ".cmd", ".com", ".pif", ".scr",
            ".vbs", ".js", ".jar", ".msi", ".app", ".deb",
            ".rpm", ".sh", ".ps1", ".psm1"
        ],
        "sanitize_filenames": True
    },
    "storage": {
        "upload_folder": "uploads",
        "temp_folder": "temp",
        "auto_cleanup_days": 0  # 0 means no auto cleanup
    },
    "logging": {
        "enabled": True,
        "level": "INFO",
        "max_file_size_mb": 10,
        "backup_count": 5,
        "log_folder": "logs"
    },
    "security": {
        "password_protected": False,
        "password": "",
        "rate_limit_enabled": True,
        "max_uploads_per_minute": 10
    },
    "ui": {
        "show_system_tray": True,
        "minimize_to_tray": True,
        "start_server_on_launch": False,
        "theme": "dark"
    }
}


class Config:
    """Configuration manager for WebShare"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to the configuration file
        """
        if config_path is None:
            # Default to config.json in the application directory
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(app_dir, 'config.json')
        
        self.config_path = config_path
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file, create with defaults if not exists"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self._merge_config(user_config)
            except Exception as e:
                print(f"Error loading config file: {e}")
                print("Using default configuration")
        else:
            # Try to copy from config.example.json if it exists
            app_dir = os.path.dirname(self.config_path)
            example_config_path = os.path.join(app_dir, 'config.example.json')
            
            if os.path.exists(example_config_path):
                try:
                    print(f"Creating config.json from config.example.json...")
                    with open(example_config_path, 'r', encoding='utf-8') as f:
                        example_config = json.load(f)
                        self._merge_config(example_config)
                    print(f"✓ Configuration file created at {self.config_path}")
                except Exception as e:
                    print(f"Error reading example config: {e}")
                    print("Using default configuration")
            
            # Save the config (either from example or defaults)
            self.save_config()
    
    def _merge_config(self, user_config: Dict[str, Any]) -> None:
        """
        Merge user configuration with defaults
        
        Args:
            user_config: User-provided configuration dictionary
        """
        for section, values in user_config.items():
            if section in self.config and isinstance(values, dict):
                self.config[section].update(values)
            else:
                self.config[section] = values
    
    def save_config(self) -> bool:
        """
        Save current configuration to file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config file: {e}")
            return False
    
    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """
        Get a configuration value
        
        Args:
            section: Configuration section name
            key: Key within the section (optional)
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        if key is None:
            return self.config.get(section, default)
        
        section_data = self.config.get(section, {})
        return section_data.get(key, default)
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value
        
        Args:
            section: Configuration section name
            key: Key within the section
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
    
    def get_max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes"""
        mb = self.get('upload', 'max_file_size_mb', 500)
        return mb * 1024 * 1024
    
    def get_max_total_size_bytes(self) -> int:
        """Get maximum total storage size in bytes"""
        gb = self.get('upload', 'max_total_size_gb', 10)
        return gb * 1024 * 1024 * 1024
    
    def is_extension_allowed(self, filename: str) -> bool:
        """
        Check if a file extension is allowed
        
        Args:
            filename: Name of the file to check
            
        Returns:
            bool: True if allowed, False otherwise
        """
        ext = os.path.splitext(filename)[1].lower()
        
        # Check blocked extensions first
        blocked = self.get('upload', 'blocked_extensions', [])
        if ext in [b.lower() for b in blocked]:
            return False
        
        # Check allowed extensions (if list is not empty)
        allowed = self.get('upload', 'allowed_extensions', [])
        if allowed:
            return ext in [a.lower() for a in allowed]
        
        return True
    
    def get_blocked_extensions(self) -> List[str]:
        """Get list of blocked file extensions"""
        return self.get('upload', 'blocked_extensions', [])
    
    def get_allowed_extensions(self) -> List[str]:
        """Get list of allowed file extensions"""
        return self.get('upload', 'allowed_extensions', [])


# Global config instance
_config_instance = None


def get_config() -> Config:
    """
    Get the global configuration instance
    
    Returns:
        Config: Global configuration object
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reload_config() -> None:
    """Reload configuration from file"""
    global _config_instance
    if _config_instance is not None:
        _config_instance.load_config()
