"""
Settings Dialog for WebShare
Comprehensive GUI for all configuration options
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QSpinBox, QCheckBox, QPushButton,
    QFileDialog, QGroupBox, QComboBox, QTextEdit, QListWidget,
    QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator

from app.config import get_config


class SettingsDialog(QDialog):
    """Settings dialog with tabbed interface"""
    
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self.setWindowTitle("WebShare Settings")
        self.setMinimumSize(700, 600)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Add tabs
        self.tabs.addTab(self.create_server_tab(), "Server")
        self.tabs.addTab(self.create_storage_tab(), "Storage")
        self.tabs.addTab(self.create_security_tab(), "Security")
        self.tabs.addTab(self.create_upload_tab(), "Upload Rules")
        self.tabs.addTab(self.create_extensions_tab(), "File Extensions")
        self.tabs.addTab(self.create_advanced_tab(), "Advanced")
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_and_close)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def create_server_tab(self):
        """Create server configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Server group
        server_group = QGroupBox("Server Configuration")
        server_layout = QFormLayout()
        
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("0.0.0.0")
        server_layout.addRow("Host:", self.host_edit)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(5000)
        server_layout.addRow("Port:", self.port_spin)
        
        self.max_connections_spin = QSpinBox()
        self.max_connections_spin.setRange(1, 1000)
        self.max_connections_spin.setValue(100)
        server_layout.addRow("Max Connections:", self.max_connections_spin)
        
        self.auto_open_browser = QCheckBox("Auto-open browser on start")
        server_layout.addRow("", self.auto_open_browser)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # QR Code group
        qr_group = QGroupBox("QR Code")
        qr_layout = QFormLayout()
        
        self.show_qr = QCheckBox("Show QR code on start")
        qr_layout.addRow("", self.show_qr)
        
        qr_group.setLayout(qr_layout)
        layout.addWidget(qr_group)
        
        layout.addStretch()
        return widget
    
    def create_storage_tab(self):
        """Create storage configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Upload folder group
        folder_group = QGroupBox("Upload Folder")
        folder_layout = QVBoxLayout()
        
        folder_select_layout = QHBoxLayout()
        self.upload_folder_edit = QLineEdit()
        folder_select_layout.addWidget(self.upload_folder_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_upload_folder)
        folder_select_layout.addWidget(browse_btn)
        
        folder_layout.addLayout(folder_select_layout)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        # Storage limits group
        limits_group = QGroupBox("Storage Limits")
        limits_layout = QFormLayout()
        
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setRange(1, 10000)
        self.max_file_size_spin.setValue(100)
        self.max_file_size_spin.setSuffix(" MB")
        limits_layout.addRow("Max File Size:", self.max_file_size_spin)
        
        self.max_total_size_spin = QSpinBox()
        self.max_total_size_spin.setRange(100, 100000)
        self.max_total_size_spin.setValue(10000)
        self.max_total_size_spin.setSuffix(" MB")
        limits_layout.addRow("Max Total Storage:", self.max_total_size_spin)
        
        self.max_files_spin = QSpinBox()
        self.max_files_spin.setRange(1, 10000)
        self.max_files_spin.setValue(1000)
        limits_layout.addRow("Max File Count:", self.max_files_spin)
        
        limits_group.setLayout(limits_layout)
        layout.addWidget(limits_group)
        
        layout.addStretch()
        return widget
    
    def create_security_tab(self):
        """Create security configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Password protection group
        password_group = QGroupBox("Password Protection")
        password_layout = QFormLayout()
        
        self.password_enabled = QCheckBox("Enable password protection")
        self.password_enabled.toggled.connect(self.on_password_enabled_changed)
        password_layout.addRow("", self.password_enabled)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter password...")
        password_layout.addRow("Password:", self.password_edit)
        
        password_group.setLayout(password_layout)
        layout.addWidget(password_group)
        
        # Rate limiting group
        rate_group = QGroupBox("Rate Limiting")
        rate_layout = QFormLayout()
        
        self.rate_limit_enabled = QCheckBox("Enable rate limiting")
        self.rate_limit_enabled.toggled.connect(self.on_rate_limit_enabled_changed)
        rate_layout.addRow("", self.rate_limit_enabled)
        
        self.max_uploads_spin = QSpinBox()
        self.max_uploads_spin.setRange(1, 100)
        self.max_uploads_spin.setValue(10)
        rate_layout.addRow("Max uploads per minute:", self.max_uploads_spin)
        
        rate_group.setLayout(rate_layout)
        layout.addWidget(rate_group)
        
        layout.addStretch()
        return widget
    
    def create_upload_tab(self):
        """Create upload rules configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # File validation group
        validation_group = QGroupBox("File Validation")
        validation_layout = QFormLayout()
        
        self.sanitize_filenames = QCheckBox("Sanitize filenames")
        validation_layout.addRow("", self.sanitize_filenames)
        
        self.allow_overwrite = QCheckBox("Allow overwriting existing files")
        validation_layout.addRow("", self.allow_overwrite)
        
        validation_group.setLayout(validation_layout)
        layout.addWidget(validation_group)
        
        # Extension mode group
        extension_mode_group = QGroupBox("Extension Filtering Mode")
        extension_mode_layout = QVBoxLayout()
        
        self.extension_mode_combo = QComboBox()
        self.extension_mode_combo.addItems([
            "Blacklist (Block specific extensions)",
            "Whitelist (Allow only specific extensions)"
        ])
        extension_mode_layout.addWidget(self.extension_mode_combo)
        
        extension_mode_group.setLayout(extension_mode_layout)
        layout.addWidget(extension_mode_group)
        
        layout.addStretch()
        return widget
    
    def create_extensions_tab(self):
        """Create file extensions configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Allowed extensions group
        allowed_group = QGroupBox("Allowed Extensions (Whitelist Mode)")
        allowed_layout = QVBoxLayout()
        
        allowed_help = QLabel("Extensions that ARE allowed when whitelist mode is enabled.\nSeparate with commas (e.g., .jpg, .png, .pdf)")
        allowed_help.setWordWrap(True)
        allowed_layout.addWidget(allowed_help)
        
        self.allowed_extensions_edit = QTextEdit()
        self.allowed_extensions_edit.setMaximumHeight(100)
        self.allowed_extensions_edit.setPlaceholderText(".jpg, .png, .pdf, .txt, .zip")
        allowed_layout.addWidget(self.allowed_extensions_edit)
        
        allowed_group.setLayout(allowed_layout)
        layout.addWidget(allowed_group)
        
        # Blocked extensions group
        blocked_group = QGroupBox("Blocked Extensions (Blacklist Mode)")
        blocked_layout = QVBoxLayout()
        
        blocked_help = QLabel("Extensions that are BLOCKED when blacklist mode is enabled.\nSeparate with commas (e.g., .exe, .bat, .sh)")
        blocked_help.setWordWrap(True)
        blocked_layout.addWidget(blocked_help)
        
        self.blocked_extensions_edit = QTextEdit()
        self.blocked_extensions_edit.setMaximumHeight(100)
        self.blocked_extensions_edit.setPlaceholderText(".exe, .bat, .sh, .cmd, .scr")
        blocked_layout.addWidget(self.blocked_extensions_edit)
        
        blocked_group.setLayout(blocked_layout)
        layout.addWidget(blocked_group)
        
        # Common presets
        presets_group = QGroupBox("Quick Presets")
        presets_layout = QHBoxLayout()
        
        images_btn = QPushButton("Images Only")
        images_btn.clicked.connect(lambda: self.apply_preset("images"))
        presets_layout.addWidget(images_btn)
        
        documents_btn = QPushButton("Documents Only")
        documents_btn.clicked.connect(lambda: self.apply_preset("documents"))
        presets_layout.addWidget(documents_btn)
        
        safe_btn = QPushButton("Safe Files Only")
        safe_btn.clicked.connect(lambda: self.apply_preset("safe"))
        presets_layout.addWidget(safe_btn)
        
        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)
        
        layout.addStretch()
        return widget
    
    def create_advanced_tab(self):
        """Create advanced configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Logging group
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout()
        
        log_folder_layout = QHBoxLayout()
        self.log_folder_edit = QLineEdit()
        log_folder_layout.addWidget(self.log_folder_edit)
        
        log_browse_btn = QPushButton("Browse...")
        log_browse_btn.clicked.connect(self.browse_log_folder)
        log_folder_layout.addWidget(log_browse_btn)
        
        logging_layout.addRow("Log Folder:", log_folder_layout)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        logging_layout.addRow("Log Level:", self.log_level_combo)
        
        logging_group.setLayout(logging_layout)
        layout.addWidget(logging_group)
        
        # System tray group
        tray_group = QGroupBox("System Tray")
        tray_layout = QFormLayout()
        
        self.minimize_to_tray = QCheckBox("Minimize to system tray")
        tray_layout.addRow("", self.minimize_to_tray)
        
        self.start_minimized = QCheckBox("Start minimized to tray")
        tray_layout.addRow("", self.start_minimized)
        
        tray_group.setLayout(tray_layout)
        layout.addWidget(tray_group)
        
        # Updates group
        updates_group = QGroupBox("Updates")
        updates_layout = QFormLayout()
        
        self.check_updates = QCheckBox("Check for updates on startup")
        updates_layout.addRow("", self.check_updates)
        
        updates_group.setLayout(updates_layout)
        layout.addWidget(updates_group)
        
        layout.addStretch()
        return widget
    
    def load_settings(self):
        """Load settings from config into UI"""
        # Server tab
        self.host_edit.setText(self.config.get('server', 'host', '0.0.0.0'))
        self.port_spin.setValue(self.config.get('server', 'port', 5000))
        self.max_connections_spin.setValue(self.config.get('server', 'max_connections', 100))
        self.auto_open_browser.setChecked(self.config.get('server', 'auto_open_browser', False))
        self.show_qr.setChecked(self.config.get('qr_code', 'show_on_start', True))
        
        # Storage tab
        self.upload_folder_edit.setText(self.config.get('storage', 'upload_folder', 'uploads'))
        self.max_file_size_spin.setValue(self.config.get('upload', 'max_file_size_mb', 100))
        self.max_total_size_spin.setValue(self.config.get('upload', 'max_total_size_mb', 10000))
        self.max_files_spin.setValue(self.config.get('upload', 'max_files', 1000))
        
        # Security tab
        password_protected = self.config.get('security', 'password_protected', False)
        self.password_enabled.setChecked(password_protected)
        self.password_edit.setText(self.config.get('security', 'password', ''))
        
        rate_limit_enabled = self.config.get('security', 'rate_limit_enabled', True)
        self.rate_limit_enabled.setChecked(rate_limit_enabled)
        self.max_uploads_spin.setValue(self.config.get('security', 'max_uploads_per_minute', 10))
        
        # Upload tab
        self.sanitize_filenames.setChecked(self.config.get('upload', 'sanitize_filenames', True))
        self.allow_overwrite.setChecked(self.config.get('upload', 'allow_overwrite', False))
        
        whitelist_mode = self.config.get('upload', 'use_whitelist', False)
        self.extension_mode_combo.setCurrentIndex(1 if whitelist_mode else 0)
        
        # Extensions tab
        allowed = self.config.get('upload', 'allowed_extensions', [])
        self.allowed_extensions_edit.setPlainText(', '.join(allowed))
        
        blocked = self.config.get('upload', 'blocked_extensions', [])
        self.blocked_extensions_edit.setPlainText(', '.join(blocked))
        
        # Advanced tab
        self.log_folder_edit.setText(self.config.get('logging', 'log_folder', 'logs'))
        self.log_level_combo.setCurrentText(self.config.get('logging', 'log_level', 'INFO'))
        self.minimize_to_tray.setChecked(self.config.get('ui', 'minimize_to_tray', True))
        self.start_minimized.setChecked(self.config.get('ui', 'start_minimized', False))
        self.check_updates.setChecked(self.config.get('updates', 'check_on_startup', True))
        
        # Update enabled states
        self.on_password_enabled_changed(password_protected)
        self.on_rate_limit_enabled_changed(rate_limit_enabled)
    
    def save_settings(self):
        """Save UI settings to config"""
        # Server settings
        self.config.set('server', 'host', self.host_edit.text())
        self.config.set('server', 'port', self.port_spin.value())
        self.config.set('server', 'max_connections', self.max_connections_spin.value())
        self.config.set('server', 'auto_open_browser', self.auto_open_browser.isChecked())
        self.config.set('qr_code', 'show_on_start', self.show_qr.isChecked())
        
        # Storage settings
        self.config.set('storage', 'upload_folder', self.upload_folder_edit.text())
        self.config.set('upload', 'max_file_size_mb', self.max_file_size_spin.value())
        self.config.set('upload', 'max_total_size_mb', self.max_total_size_spin.value())
        self.config.set('upload', 'max_files', self.max_files_spin.value())
        
        # Security settings
        self.config.set('security', 'password_protected', self.password_enabled.isChecked())
        if self.password_enabled.isChecked() and self.password_edit.text():
            self.config.set('security', 'password', self.password_edit.text())
        
        self.config.set('security', 'rate_limit_enabled', self.rate_limit_enabled.isChecked())
        self.config.set('security', 'max_uploads_per_minute', self.max_uploads_spin.value())
        
        # Upload settings
        self.config.set('upload', 'sanitize_filenames', self.sanitize_filenames.isChecked())
        self.config.set('upload', 'allow_overwrite', self.allow_overwrite.isChecked())
        self.config.set('upload', 'use_whitelist', self.extension_mode_combo.currentIndex() == 1)
        
        # Extensions
        allowed_text = self.allowed_extensions_edit.toPlainText()
        allowed_list = [ext.strip() for ext in allowed_text.split(',') if ext.strip()]
        self.config.set('upload', 'allowed_extensions', allowed_list)
        
        blocked_text = self.blocked_extensions_edit.toPlainText()
        blocked_list = [ext.strip() for ext in blocked_text.split(',') if ext.strip()]
        self.config.set('upload', 'blocked_extensions', blocked_list)
        
        # Advanced settings
        self.config.set('logging', 'log_folder', self.log_folder_edit.text())
        self.config.set('logging', 'log_level', self.log_level_combo.currentText())
        self.config.set('ui', 'minimize_to_tray', self.minimize_to_tray.isChecked())
        self.config.set('ui', 'start_minimized', self.start_minimized.isChecked())
        self.config.set('updates', 'check_on_startup', self.check_updates.isChecked())
        
        self.config.save_config()
    
    def apply_settings(self):
        """Apply settings without closing"""
        self.save_settings()
        self.settings_changed.emit()
        QMessageBox.information(self, "Settings Applied", "Settings have been saved successfully.")
    
    def save_and_close(self):
        """Save settings and close dialog"""
        self.save_settings()
        self.settings_changed.emit()
        self.accept()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            from app.config import DEFAULT_CONFIG
            self.config.config = DEFAULT_CONFIG.copy()
            self.config.save_config()
            self.load_settings()
            QMessageBox.information(self, "Reset Complete", "All settings have been reset to defaults.")
    
    def browse_upload_folder(self):
        """Browse for upload folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Upload Folder",
            self.upload_folder_edit.text()
        )
        if folder:
            self.upload_folder_edit.setText(folder)
    
    def browse_log_folder(self):
        """Browse for log folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Log Folder",
            self.log_folder_edit.text()
        )
        if folder:
            self.log_folder_edit.setText(folder)
    
    def on_password_enabled_changed(self, checked):
        """Handle password protection toggle"""
        self.password_edit.setEnabled(checked)
    
    def on_rate_limit_enabled_changed(self, checked):
        """Handle rate limiting toggle"""
        self.max_uploads_spin.setEnabled(checked)
    
    def apply_preset(self, preset_name):
        """Apply extension preset"""
        presets = {
            'images': {
                'whitelist': True,
                'allowed': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'],
                'blocked': []
            },
            'documents': {
                'whitelist': True,
                'allowed': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt'],
                'blocked': []
            },
            'safe': {
                'whitelist': False,
                'allowed': [],
                'blocked': ['.exe', '.bat', '.cmd', '.sh', '.ps1', '.vbs', '.scr', '.com', '.pif', '.msi', '.dll']
            }
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            self.extension_mode_combo.setCurrentIndex(1 if preset['whitelist'] else 0)
            self.allowed_extensions_edit.setPlainText(', '.join(preset['allowed']))
            self.blocked_extensions_edit.setPlainText(', '.join(preset['blocked']))
            
            QMessageBox.information(
                self,
                "Preset Applied",
                f"The '{preset_name}' preset has been applied. Click Save to keep these changes."
            )
