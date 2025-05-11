import os
import sys
import threading
import webbrowser
import json
import urllib.request
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, 
    QGroupBox, QCheckBox, QSpinBox, QFileDialog, QMessageBox, QProgressBar, 
    QDesktopWidget, QFrame, QStatusBar, QDialog, QTextBrowser
)
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize, QObject, pyqtSlot

from app.utils import (
    get_local_ip, generate_qr_image, get_pixmap_from_base64,
    create_fallback_icon, get_fallback_icon
)
from app.server import UPLOAD_FOLDER, run_server
from app.version import __version__, __author__

# Path to icon files
ICON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'templates', 'icon')
WINDOW_ICON_PATH = os.path.join(ICON_PATH, 'icon48.png')

class UpdateChecker(QObject):
    """Thread-safe update checker using Qt signals"""
    update_available = pyqtSignal(str, str)
    update_not_available = pyqtSignal()
    update_error = pyqtSignal(str)
    
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
        self.host = "0.0.0.0"
        self.port = 5000
        self.url = ""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        
        # Create update checker
        self.update_checker = UpdateChecker()
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.update_not_available.connect(self.on_update_not_available)
        self.update_checker.update_error.connect(self.on_update_error)
        
        self.initUI()

    def initUI(self):
        """Initialize the user interface"""
        self.setWindowTitle("WebShare for Windows")
        
        # Try to use the actual icon file for the window
        icon_path = WINDOW_ICON_PATH
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            # Use fallback only if file doesn't exist
            self.setWindowIcon(get_fallback_icon())
            
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
        
        # Server controls - top row
        controls_layout = QHBoxLayout()
        
        # Start/Stop button
        self.start_button = QPushButton("Start WebShare Server", self)
        self.start_button.clicked.connect(self.toggle_server)
        controls_layout.addWidget(self.start_button)
        
        # Port selection
        port_layout = QHBoxLayout()
        port_label = QLabel("Port:")
        self.port_spinner = QSpinBox()
        self.port_spinner.setRange(1024, 65535)
        self.port_spinner.setValue(5000)
        self.port_spinner.valueChanged.connect(self.update_port)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_spinner)
        controls_layout.addLayout(port_layout)
        
        server_layout.addLayout(controls_layout)
        
        # Server status
        status_layout = QHBoxLayout()
        status_label = QLabel("Status:")
        self.status_text = QLabel("Stopped")
        self.status_text.setStyleSheet("color: #e74c3c;")
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch(1)
        
        # Server URL
        url_label = QLabel("URL:")
        self.url_text = QLabel("Not available")
        status_layout.addWidget(url_label)
        status_layout.addWidget(self.url_text)
        
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
        
        # Open folder button
        self.open_folder_button = QPushButton("Open Upload Folder", self)
        self.open_folder_button.clicked.connect(self.open_folder)
        actions_layout.addWidget(self.open_folder_button)
        
        # Clear files button
        self.clear_files_button = QPushButton("Delete All Files", self)
        self.clear_files_button.clicked.connect(self.clear_files)
        actions_layout.addWidget(self.clear_files_button)
        
        # Change folder button
        self.change_folder_button = QPushButton("Change Upload Folder", self)
        self.change_folder_button.clicked.connect(self.change_folder)
        actions_layout.addWidget(self.change_folder_button)
        
        actions_group.setLayout(actions_layout)
        main_layout.addWidget(actions_group)
        
        # Help section
        help_group = QGroupBox("Help & Updates")
        help_layout = QHBoxLayout()
        
        # About button
        self.about_button = QPushButton("About", self)
        self.about_button.clicked.connect(self.show_about)
        help_layout.addWidget(self.about_button)
        
        # Check for updates button
        self.update_button = QPushButton("Check for Updates", self)
        self.update_button.clicked.connect(self.check_for_updates)
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
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

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
            self.start_button.setText("Stop Server")
            self.status_text.setText("Running")
            self.status_text.setStyleSheet("color: #2ecc71;")
            self.url_text.setText(self.url)
            self.port_spinner.setEnabled(False)
            self.status_bar.showMessage(f"Server started at {self.url}")
            
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
            self.start_button.setText("Start WebShare Server")
            self.status_text.setText("Stopped")
            self.status_text.setStyleSheet("color: #e74c3c;")
            self.url_text.setText("Not available")
            self.port_spinner.setEnabled(True)
            self.status_bar.showMessage("Server stopped")
            
            # Stop stats timer
            self.timer.stop()
            
            # The server thread will continue to run because Flask doesn't have a clean
            # way to stop it. When the application exits, the thread will be killed.
            self.server_thread = None
            
            # Clear QR code
            self.qr_label.clear()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error stopping server: {str(e)}")

    def open_folder(self):
        """Open the upload folder in file explorer"""
        folder_path = os.path.abspath(UPLOAD_FOLDER)
        try:
            os.startfile(folder_path)
            self.status_bar.showMessage(f"Opened folder: {folder_path}", 3000)
        except Exception as e:
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
                for filename in os.listdir(UPLOAD_FOLDER):
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted += 1
                self.status_bar.showMessage(f"Deleted {deleted} files", 3000)
                self.update_stats()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete files: {str(e)}")

    def change_folder(self):
        """Change the upload folder location"""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Upload Folder", os.path.abspath(UPLOAD_FOLDER)
        )
        
        if folder:
            # Note: This is a simple implementation. In a real app, we would need
            # to update the global UPLOAD_FOLDER and restart the server.
            QMessageBox.information(
                self, "Information", 
                "Changing folders is not fully implemented in this version."
            )
            self.status_bar.showMessage("Folder selection not implemented yet", 3000)

    def update_stats(self):
        """Update server statistics"""
        try:
            # Count files
            files = [f for f in os.listdir(UPLOAD_FOLDER) 
                    if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
            file_count = len(files)
            self.file_count_text.setText(str(file_count))
            
            # Calculate total size
            total_size = 0
            for filename in files:
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                total_size += os.path.getsize(file_path)
                
            # Convert to MB
            total_size_mb = total_size / (1024 * 1024)
            self.size_text.setText(f"{total_size_mb:.2f} MB")
            
            # Update storage bar (arbitrary max of 1GB for demonstration)
            max_storage = 1024  # 1GB in MB
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
            self.status_bar.showMessage(f"Error updating stats: {str(e)}", 3000)
    
    def show_about(self):
        """Show the About dialog"""
        about_dialog = AboutDialog(self)
        about_dialog.exec_()
    
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
    
    @pyqtSlot(str, str)
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
    
    @pyqtSlot()
    def on_update_not_available(self):
        """Slot called when no update is available"""
        self.status_bar.showMessage("You have the latest version!", 3000)
        self.update_button.setEnabled(True)
    
    @pyqtSlot(str)
    def on_update_error(self, error_msg):
        """Slot called when there is an error checking for updates"""
        self.status_bar.showMessage(f"Error checking for updates: {error_msg}", 3000)
        self.update_button.setEnabled(True) 