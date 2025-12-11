import os
import sys
import threading
import webbrowser
import json
import urllib.request
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, 
    QGroupBox, QCheckBox, QSpinBox, QFileDialog, QMessageBox, QProgressBar, 
    QFrame, QStatusBar, QDialog, QTextBrowser, QSystemTrayIcon, QMenu
)
from PySide6.QtGui import QPixmap, QIcon, QFont, QScreen, QAction, QCursor
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QObject, Slot

from app.utils import (
    get_local_ip, generate_qr_image, get_pixmap_from_base64,
    create_fallback_icon, get_fallback_icon
)
from app.server import run_server
from app.version import __version__, __author__
from app.config import get_config
from app.logger import get_logger
from app.settings_dialog import SettingsDialog

# Path to icon files
ICON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'templates', 'icon')
WINDOW_ICON_PATH = os.path.join(ICON_PATH, 'icon48.png')

class UpdateChecker(QObject):
    """Thread-safe update checker using Qt signals"""
    update_available = Signal(str, str)
    update_not_available = Signal()
    update_error = Signal(str)
    
    def check_for_updates(self):
        """Check for updates from GitHub repository"""
        try:
            # GitHub API URL for releases
            api_url = "https://api.github.com/repos/oop7/WebShare-for-Windows/releases/latest"
            
            # Set a timeout and user agent
            headers = {'User-Agent': f'WebShare-for-Windows/{__version__}'}
            req = urllib.request.Request(api_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get('tag_name', '').lstrip('v')
                download_url = data.get('html_url', '')
                
                # Compare versions
                if latest_version and self._compare_versions(latest_version, __version__) > 0:
                    self.update_available.emit(latest_version, download_url)
                else:
                    self.update_not_available.emit()
        except Exception as e:
            self.update_error.emit(str(e))
    
    def _compare_versions(self, version1, version2):
        """
        Compare two version strings
        
        Returns:
            int: 1 if version1 > version2, -1 if version1 < version2, 0 if equal
        """
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Pad with zeros if needed
            while len(v1_parts) < len(v2_parts):
                v1_parts.append(0)
            while len(v2_parts) < len(v1_parts):
                v2_parts.append(0)
            
            for i in range(len(v1_parts)):
                if v1_parts[i] > v2_parts[i]:
                    return 1
                elif v1_parts[i] < v2_parts[i]:
                    return -1
            
            return 0
        except:
            # If parsing fails, assume versions are equal
            return 0


class AboutDialog(QDialog):
    """About dialog showing application information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About WebShare")
        self.setFixedSize(400, 300)
        
        # Set window icon using actual icon file
        icon_path = WINDOW_ICON_PATH
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            # Fallback only if file doesn't exist
            self.setWindowIcon(get_fallback_icon())
            
        layout = QVBoxLayout()
        
        # App icon
        icon_label = QLabel()
        icon_label.setFixedHeight(64)
        
        # Try to load the actual icon file
        main_icon_path = os.path.join(ICON_PATH, 'icon.png')
        if os.path.exists(main_icon_path):
            pixmap = QPixmap(main_icon_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(pixmap)
            else:
                # Use fallback if loading fails
                pixmap = create_fallback_icon(64)
                icon_label.setPixmap(pixmap)
        else:
            # Use fallback if file doesn't exist
            pixmap = create_fallback_icon(64)
            icon_label.setPixmap(pixmap)
            
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # App title
        title_label = QLabel("WebShare for Windows")
        title_label.setAlignment(Qt.AlignCenter)
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)
        
        # Version
        version_label = QLabel(f"Version {__version__}")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # Description
        info_browser = QTextBrowser()
        info_browser.setOpenExternalLinks(True)
        info_browser.setHtml(f"""
            <p style="text-align:center;">
            A file sharing application that lets you easily share files on your local network.
            </p>
            <p style="text-align:center;">
            Author: {__author__}
            </p>
            <p style="text-align:center;">
            <a href="https://github.com/oop7/WebShare-for-Windows">GitHub Repository</a>
            </p>
            <p style="text-align:center;">
            Licensed under the MIT License
            </p>
        """)
        layout.addWidget(info_browser)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
        
        # Apply the same style as the main app
        self.setStyleSheet(parent.styleSheet())


class WebShareApp(QWidget):
    """Main application window for WebShare"""

    def __init__(self):
        """Initialize the WebShare application"""
        super().__init__()
        self.server_running = False
        self.server_thread = None
        
        # Get configuration and logger
        self.config = get_config()
        self.logger = get_logger()
        
        # Server settings from config
        self.host = self.config.get('server', 'host', '0.0.0.0')
        self.port = self.config.get('server', 'port', 5000)
        self.url = ""
        
        # Upload folder from config
        self.upload_folder = self.config.get('storage', 'upload_folder', 'uploads')
        if not os.path.isabs(self.upload_folder):
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                base_dir = os.path.dirname(sys.executable)
            else:
                # Running as script
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.upload_folder = os.path.join(base_dir, self.upload_folder)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        
        # Create update checker
        self.update_checker = UpdateChecker()
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.update_not_available.connect(self.on_update_not_available)
        self.update_checker.update_error.connect(self.on_update_error)
        
        # System tray icon
        self.tray_icon = None
        
        self.initUI()
        self.setup_system_tray()

    def initUI(self):
        """Initialize the user interface"""
        self.setWindowTitle("WebShare for Windows")
        
        # Try to use the actual icon file for the window
        icon_path = WINDOW_ICON_PATH
        if os.path.exists(icon_path):
            self.app_icon = QIcon(icon_path)
            self.setWindowIcon(self.app_icon)
        else:
            # Use fallback only if file doesn't exist
            self.app_icon = get_fallback_icon()
            self.setWindowIcon(self.app_icon)
            
        self.resize(600, 500)
        
        # Center window on screen
        self.center_on_screen()
        
        # Apply dark mode stylesheet
        self.apply_dark_style()
        
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        
        # Server controls
        server_group = QGroupBox("Server Controls")
        server_layout = QVBoxLayout()
        
        # Server controls - organized in a form layout
        controls_form = QHBoxLayout()
        
        # Start/Stop button
        self.start_button = QPushButton("▶️ Start Server", self)
        self.start_button.clicked.connect(self.toggle_server)
        self.start_button.setMinimumHeight(40)
        self.start_button.setMinimumWidth(200)
        controls_form.addWidget(self.start_button)
        
        controls_form.addSpacing(20)
        
        # Port selection
        port_label = QLabel("Port:")
        port_label.setStyleSheet("font-weight: bold;")
        controls_form.addWidget(port_label)
        
        self.port_spinner = QSpinBox()
        self.port_spinner.setRange(1024, 65535)
        self.port_spinner.setValue(5000)
        self.port_spinner.setMinimumWidth(100)
        self.port_spinner.setMinimumHeight(35)
        self.port_spinner.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        self.port_spinner.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                height: 17px;
            }
        """)
        self.port_spinner.valueChanged.connect(self.update_port)
        controls_form.addWidget(self.port_spinner)
        
        controls_form.addStretch()
        
        server_layout.addLayout(controls_form)
        
        # Server status
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        
        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-weight: bold; min-width: 60px;")
        self.status_text = QLabel("Stopped")
        self.status_text.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 5px; background-color: rgba(231, 76, 60, 0.1); border-radius: 3px;")
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch(1)
        
        # Server URL
        url_label = QLabel("URL:")
        url_label.setStyleSheet("font-weight: bold; min-width: 40px;")
        self.url_text = QLabel("Not available")
        self.url_text.setStyleSheet("color: #3498db; font-weight: bold; padding: 5px; text-decoration: underline;")
        self.url_text.setCursor(QCursor(Qt.PointingHandCursor))
        self.url_text.mousePressEvent = lambda event: self.open_url_in_browser()
        status_layout.addWidget(url_label)
        status_layout.addWidget(self.url_text)
        
        # Copy URL button
        self.copy_url_button = QPushButton("📋")
        self.copy_url_button.setToolTip("Copy URL to clipboard")
        self.copy_url_button.setMaximumWidth(35)
        self.copy_url_button.setMaximumHeight(30)
        self.copy_url_button.clicked.connect(self.copy_url_to_clipboard)
        self.copy_url_button.setVisible(False)  # Hidden until server starts
        status_layout.addWidget(self.copy_url_button)
        
        server_layout.addLayout(status_layout)
        server_group.setLayout(server_layout)
        main_layout.addWidget(server_group)
        
        # QR Code and server information
        middle_layout = QHBoxLayout()
        
        # QR Code
        qr_group = QGroupBox("QR Code")
        qr_layout = QVBoxLayout()
        self.qr_label = QLabel(self)
        self.qr_label.setAlignment(Qt.AlignCenter)
        qr_layout.addWidget(self.qr_label)
        qr_group.setLayout(qr_layout)
        middle_layout.addWidget(qr_group)
        
        # Server stats
        stats_group = QGroupBox("Server Statistics")
        stats_layout = QVBoxLayout()
        
        # File count
        file_count_layout = QHBoxLayout()
        file_count_label = QLabel("Files:")
        self.file_count_text = QLabel("0")
        file_count_layout.addWidget(file_count_label)
        file_count_layout.addWidget(self.file_count_text)
        file_count_layout.addStretch(1)
        stats_layout.addLayout(file_count_layout)
        
        # Total size
        size_layout = QHBoxLayout()
        size_label = QLabel("Total size:")
        self.size_text = QLabel("0 MB")
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_text)
        size_layout.addStretch(1)
        stats_layout.addLayout(size_layout)
        
        # Storage bar
        self.storage_bar = QProgressBar()
        self.storage_bar.setRange(0, 100)
        self.storage_bar.setValue(0)
        stats_layout.addWidget(QLabel("Storage usage:"))
        stats_layout.addWidget(self.storage_bar)
        
        stats_layout.addStretch(1)
        stats_group.setLayout(stats_layout)
        middle_layout.addWidget(stats_group)
        
        main_layout.addLayout(middle_layout)
        
        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        
        # Open folder button
        self.open_folder_button = QPushButton("📁 Open Folder", self)
        self.open_folder_button.clicked.connect(self.open_folder)
        self.open_folder_button.setMinimumHeight(35)
        actions_layout.addWidget(self.open_folder_button)
        
        # Clear files button
        self.clear_files_button = QPushButton("🗑️ Delete All", self)
        self.clear_files_button.clicked.connect(self.clear_files)
        self.clear_files_button.setMinimumHeight(35)
        actions_layout.addWidget(self.clear_files_button)
        
        # Change folder button
        self.change_folder_button = QPushButton("📂 Change Folder", self)
        self.change_folder_button.clicked.connect(self.change_folder)
        self.change_folder_button.setMinimumHeight(35)
        actions_layout.addWidget(self.change_folder_button)
        
        # Settings button
        self.settings_button = QPushButton("⚙️ Settings", self)
        self.settings_button.clicked.connect(self.show_settings)
        self.settings_button.setMinimumHeight(35)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        actions_layout.addWidget(self.settings_button)
        
        actions_group.setLayout(actions_layout)
        main_layout.addWidget(actions_group)
        
        # Help section
        help_group = QGroupBox("Help & Updates")
        help_layout = QHBoxLayout()
        help_layout.setSpacing(8)
        
        # About button
        self.about_button = QPushButton("ℹ️ About", self)
        self.about_button.clicked.connect(self.show_about)
        self.about_button.setMinimumHeight(35)
        help_layout.addWidget(self.about_button)
        
        # Check for updates button
        self.update_button = QPushButton("🔄 Check Updates", self)
        self.update_button.clicked.connect(self.check_for_updates)
        self.update_button.setMinimumHeight(35)
        help_layout.addWidget(self.update_button)
        
        help_group.setLayout(help_layout)
        main_layout.addWidget(help_group)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)

    def apply_dark_style(self):
        """Apply dark mode styling to the application"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e2730;
                color: white;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #2c3e50;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 4px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #3c546d;
            }
            QPushButton:pressed {
                background-color: #233140;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
            QLabel {
                padding: 2px;
            }
            QGroupBox {
                border: 1px solid #34495e;
                border-radius: 5px;
                margin-top: 1em;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QSpinBox {
                background-color: #2c3e50;
                color: white;
                border: 1px solid #34495e;
                border-radius: 4px;
                padding: 2px;
            }
            QProgressBar {
                border: 1px solid #34495e;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2980b9;
                width: 10px;
                margin: 0.5px;
            }
            QStatusBar {
                background-color: #11171d;
                color: #bdc3c7;
            }
            QTextBrowser {
                background-color: #2c3e50;
                color: white;
                border: 1px solid #34495e;
                border-radius: 4px;
            }
            QDialog {
                background-color: #1e2730;
                color: white;
            }
        """)

    def center_on_screen(self):
        """Center the window on the screen"""
        screen = QApplication.primaryScreen().geometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen.center())
        self.move(window_geometry.topLeft())

    def update_port(self):
        """Update the port number"""
        self.port = self.port_spinner.value()
        if self.server_running:
            self.status_bar.showMessage("Port change will take effect after restart", 3000)

    def toggle_server(self):
        """Start or stop the server"""
        if not self.server_running:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        """Start the WebShare server"""
        try:
            self.logger.info("Starting server...")
            local_ip = get_local_ip()
            self.url = f'http://{local_ip}:{self.port}'
            
            # Generate QR code
            qr_path = generate_qr_image(self.url)
            if qr_path and os.path.exists(qr_path):
                pixmap = QPixmap(qr_path)
                if not pixmap.isNull():
                    self.qr_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
                else:
                    # Show text instead of QR code if image loading failed
                    self.qr_label.setText(f"Scan QR or visit:\n{self.url}")
                    self.qr_label.setAlignment(Qt.AlignCenter)
            else:
                # If QR generation failed, just display the URL as text
                self.qr_label.setText(f"Scan QR or visit:\n{self.url}")
                self.qr_label.setAlignment(Qt.AlignCenter)
            
            # Run Flask server in a separate thread
            self.server_thread = threading.Thread(
                target=run_server, 
                args=(self.host, self.port, False),
                daemon=True
            )
            self.server_thread.start()
            
            # Update UI
            self.server_running = True
            self.start_button.setText("⏸️ Stop Server")
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            self.status_text.setText("✅ Running")
            self.status_text.setStyleSheet("color: #2ecc71; font-weight: bold; padding: 5px; background-color: rgba(46, 204, 113, 0.1); border-radius: 3px;")
            self.url_text.setText(self.url)
            self.copy_url_button.setVisible(True)  # Show copy button when server starts
            self.port_spinner.setEnabled(False)
            self.status_bar.showMessage(f"Server started at {self.url}")
            self.logger.log_server_start(self.host, self.port)
            
            # Update tray icon
            if self.tray_icon:
                self.tray_server_action.setText("Stop Server")
                self.tray_icon.showMessage(
                    "Server Started",
                    f"Running at {self.url}",
                    QSystemTrayIcon.Information,
                    1500
                )
            
            # Start stats timer
            self.update_stats()
            self.timer.start(5000)  # Update every 5 seconds
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not start server: {str(e)}")

    def stop_server(self):
        """Stop the WebShare server (note: this is a soft stop)"""
        try:
            # Update UI
            self.server_running = False
            self.start_button.setText("▶️ Start Server")
            self.start_button.setStyleSheet("")  # Reset to default
            self.status_text.setText("⛔ Stopped")
            self.status_text.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 5px; background-color: rgba(231, 76, 60, 0.1); border-radius: 3px;")
            self.url_text.setText("Not available")
            self.copy_url_button.setVisible(False)  # Hide copy button when server stops
            self.port_spinner.setEnabled(True)
            self.status_bar.showMessage("Server stopped")
            
            # Stop stats timer
            self.timer.stop()
            
            # The server thread will continue to run because Flask doesn't have a clean
            # way to stop it. When the application exits, the thread will be killed.
            self.server_thread = None
            
            # Clear QR code
            self.qr_label.clear()
            
            self.logger.log_server_stop()
            
            # Update tray icon
            if self.tray_icon:
                self.tray_server_action.setText("Start Server")
        except Exception as e:
            self.logger.error(f"Error stopping server: {str(e)}")
            QMessageBox.warning(self, "Error", f"Error stopping server: {str(e)}")

    def open_folder(self):
        """Open the upload folder in file explorer"""
        folder_path = os.path.abspath(self.upload_folder)
        try:
            os.startfile(folder_path)
            self.status_bar.showMessage(f"Opened folder: {folder_path}", 3000)
            self.logger.info(f"Opened upload folder: {folder_path}")
        except Exception as e:
            self.logger.error(f"Could not open folder: {str(e)}")
            QMessageBox.warning(self, "Error", f"Could not open folder: {str(e)}")

    def clear_files(self):
        """Delete all files in the upload folder"""
        reply = QMessageBox.question(
            self, 'Confirm Deletion', 
            'Are you sure you want to delete all files?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                deleted = 0
                for filename in os.listdir(self.upload_folder):
                    file_path = os.path.join(self.upload_folder, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted += 1
                        self.logger.log_delete(filename, "local")
                self.status_bar.showMessage(f"Deleted {deleted} files", 3000)
                self.logger.info(f"Cleared all files: {deleted} files deleted")
                self.update_stats()
            except Exception as e:
                self.logger.error(f"Could not delete files: {str(e)}")
                QMessageBox.warning(self, "Error", f"Could not delete files: {str(e)}")

    def change_folder(self):
        """Change the upload folder location"""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Upload Folder", os.path.abspath(self.upload_folder)
        )
        
        if folder:
            # Note: This is a simple implementation. In a real app, we would need
            # to update the config and restart the server.
            QMessageBox.information(
                self, "Information", 
                "Changing folders is not fully implemented in this version."
            )
            self.status_bar.showMessage("Folder selection not implemented yet", 3000)

    def update_stats(self):
        """Update server statistics"""
        try:
            # Count files
            files = [f for f in os.listdir(self.upload_folder) 
                    if os.path.isfile(os.path.join(self.upload_folder, f))]
            file_count = len(files)
            self.file_count_text.setText(str(file_count))
            
            # Calculate total size
            total_size = 0
            for filename in files:
                file_path = os.path.join(self.upload_folder, filename)
                total_size += os.path.getsize(file_path)
                
            # Convert to MB
            total_size_mb = total_size / (1024 * 1024)
            self.size_text.setText(f"{total_size_mb:.2f} MB")
            
            # Get max storage from config and convert to MB
            max_storage_bytes = self.config.get_max_total_size_bytes()
            max_storage = max_storage_bytes / (1024 * 1024)
            storage_percent = min(100, (total_size_mb / max_storage) * 100)
            self.storage_bar.setValue(int(storage_percent))
            
            # Set color based on usage
            if storage_percent < 50:
                self.storage_bar.setStyleSheet("QProgressBar::chunk { background-color: #2ecc71; }")
            elif storage_percent < 80:
                self.storage_bar.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
            else:
                self.storage_bar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
                
        except Exception as e:
            self.logger.error(f"Error updating stats: {str(e)}")
            self.status_bar.showMessage(f"Error updating stats: {str(e)}", 3000)
    
    def show_about(self):
        """Show the About dialog"""
        about_dialog = AboutDialog(self)
        about_dialog.exec()
    
    def show_settings(self):
        """Show the Settings dialog"""
        settings_dialog = SettingsDialog(self)
        settings_dialog.settings_changed.connect(self.on_settings_changed)
        if settings_dialog.exec():
            self.logger.info("Settings saved by user")
    
    def on_settings_changed(self):
        """Handle settings changes"""
        # Reload config
        self.config.load_config()
        
        # Update UI with new settings
        self.host = self.config.get('server', 'host', '0.0.0.0')
        self.port = self.config.get('server', 'port', 5000)
        self.port_spinner.setValue(self.port)
        
        # Update upload folder
        self.upload_folder = self.config.get('storage', 'upload_folder', 'uploads')
        if not os.path.isabs(self.upload_folder):
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                base_dir = os.path.dirname(sys.executable)
            else:
                # Running as script
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.upload_folder = os.path.join(base_dir, self.upload_folder)
        
        # Update stats to reflect new folder
        self.update_stats()
        
        self.status_bar.showMessage("Settings applied successfully", 3000)
        self.logger.info("Settings reloaded after user changes")
    
    def check_for_updates(self):
        """Check for updates from GitHub repository"""
        self.status_bar.showMessage("Checking for updates...", 2000)
        self.update_button.setEnabled(False)
        
        # Run the update check in a separate thread
        update_thread = threading.Thread(
            target=self.update_checker.check_for_updates,
            daemon=True
        )
        update_thread.start()
    
    @Slot(str, str)
    def on_update_available(self, version, url):
        """Slot called when an update is available"""
        self.status_bar.showMessage(f"New version {version} available!", 5000)
        self.update_button.setEnabled(True)
        
        reply = QMessageBox.question(
            self, 'Update Available', 
            f'A new version ({version}) is available. Would you like to download it now?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes and url:
            webbrowser.open(url)
    
    @Slot()
    def on_update_not_available(self):
        """Slot called when no update is available"""
        self.status_bar.showMessage("You have the latest version!", 3000)
        self.update_button.setEnabled(True)
    
    @Slot(str)
    def on_update_error(self, error_msg):
        """Slot called when there is an error checking for updates"""
        self.status_bar.showMessage(f"Error checking for updates: {error_msg}", 3000)
        self.update_button.setEnabled(True)
    
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        if not self.config.get('ui', 'show_system_tray', True):
            return
        
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.logger.warning("System tray not available on this system")
            return
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self.app_icon, self)
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Show uploads action
        show_uploads_action = QAction("Show Uploads", self)
        show_uploads_action.triggered.connect(self.open_folder)
        tray_menu.addAction(show_uploads_action)
        
        tray_menu.addSeparator()
        
        # Start/Stop server action
        self.tray_server_action = QAction("Start Server", self)
        self.tray_server_action.triggered.connect(self.toggle_server)
        tray_menu.addAction(self.tray_server_action)
        
        tray_menu.addSeparator()
        
        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Show tray icon
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.tray_icon and self.config.get('ui', 'minimize_to_tray', True):
            event.ignore()
            self.hide()
            if self.tray_icon:
                self.tray_icon.showMessage(
                    "WebShare",
                    "Minimized to tray",
                    QSystemTrayIcon.Information,
                    1500
                )
        else:
            self.quit_application()
    
    def open_url_in_browser(self):
        """Open the server URL in the default web browser"""
        if self.server_running and self.url:
            try:
                webbrowser.open(self.url)
                self.status_bar.showMessage(f"Opening {self.url} in browser...", 2000)
                self.logger.info(f"Opened URL in browser: {self.url}")
            except Exception as e:
                self.logger.error(f"Could not open URL in browser: {str(e)}")
                QMessageBox.warning(self, "Error", f"Could not open URL in browser: {str(e)}")
    
    def copy_url_to_clipboard(self):
        """Copy the server URL to clipboard"""
        if self.server_running and self.url:
            try:
                clipboard = QApplication.clipboard()
                clipboard.setText(self.url)
                self.status_bar.showMessage("URL copied to clipboard!", 2000)
                self.logger.info("URL copied to clipboard")
            except Exception as e:
                self.logger.error(f"Could not copy URL to clipboard: {str(e)}")
                QMessageBox.warning(self, "Error", f"Could not copy URL to clipboard: {str(e)}")
    
    def quit_application(self):
        """Quit the application"""
        if self.server_running:
            self.stop_server()
        
        if self.tray_icon:
            self.tray_icon.hide()
        
        QApplication.quit() 