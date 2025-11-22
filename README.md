# WebShare for Windows

WebShare for Windows is a file-sharing application that utilizes PySide6 (Qt6) for a dark mode GUI and Flask for a local web server. Users can upload and download files easily through a web interface, with QR code support for quick access.

## 💪 Features

### Core Features
- **Local File Sharing**: Upload files from your PC and share them with other devices on the network.
- **QR Code Generation**: Automatically generates a QR code for easy access to the server URL.
- **Dark Mode UI**: A modern, visually appealing interface.
- **File Upload & Download**: List and download files from the web interface.
- **File Management**: Delete files from the web interface or application.
- **Storage Statistics**: Track file count and storage usage.
- **Upload Progress**: Visual feedback during file uploads.
- **Customizable Port**: Configure the server port as needed.
- **About Dialog**: View information about the application.
- **Update Checker**: Check for and download new versions of the application.

### Advanced Features
- **Password Protection**: Secure your server with optional password authentication
- **Multiple File Upload**: Upload multiple files at once with batch processing
- **Drag & Drop**: Drag files directly from your desktop into the browser
- **File Preview**: Preview images, text files, and PDFs without downloading
- **System Tray**: Minimize to system tray with quick server control
- **Enhanced Progress**: Real-time progress tracking for multiple file uploads

### Security & Performance
- **File Upload Limits**: Configurable maximum file size (default 500 MB) and total storage (default 10 GB)
- **File Type Validation**: Block dangerous file types (executables, scripts) and optionally whitelist allowed extensions
- **Filename Sanitization**: Automatically sanitize filenames to prevent path traversal and security issues
- **Rate Limiting**: Prevent abuse with configurable upload rate limits
- **Production Server**: Uses Waitress WSGI server for better performance and stability
- **Comprehensive Logging**: Structured logging with rotation for all server events, uploads, downloads, and errors
- **Configuration System**: JSON-based configuration file for easy customization
- **Error Handling**: Improved error handling with user-friendly messages

## 📄 Requirements

- Python 3.x
- See `requirements.txt` for a complete list of dependencies.

## 💻 Installation & Usage

1. Clone this repository:
```bash
git clone https://github.com/oop7/WebShare-for-Windows.git
cd WebShare-for-Windows
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

Alternatively, you can download the latest executable from the [Releases](https://github.com/oop7/WebShare-for-Windows/releases) section.

### **Usage**

1. Click "Start WebShare Server" to launch the local server.
2. A QR code will be generated; scan it to access the web interface.
3. Use the web interface to upload and download files.
4. View storage statistics in the application.
5. Delete files individually from the web interface or all at once from the application.
6. Click "About" to view information about the application.
7. Click "Check for Updates" to check for and download new versions.

### **Configuration**

On first run, a `config.json` file will be created in the application directory. You can customize:

- **Upload Limits**: Maximum file size and total storage
- **File Type Restrictions**: Allowed/blocked file extensions
- **Server Settings**: Port, host, connection limits
- **Security**: Rate limiting, filename sanitization
- **Logging**: Log levels, file rotation settings

Example configuration:
```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 5000,
        "max_connections": 100
    },
    "upload": {
        "max_file_size_mb": 500,
        "max_total_size_gb": 10,
        "sanitize_filenames": true
    },
    "security": {
        "password_protected": false,
        "password": "your_secure_password"
    },
    "ui": {
        "show_system_tray": true,
        "minimize_to_tray": true
    }
}
```

**Enable Password Protection:**
Set `"password_protected": true` and specify your desired password in `config.json`.

Logs are stored in the `logs/` directory with automatic rotation.

## 🏗️ Project Structure

```
WebShare-for-Windows/
├── app/                    # Application package
│   ├── templates/          # HTML templates
│   │   ├── icon/           # Application icons
│   │   └── index.html      # Web interface
│   ├── utils/              # Utility functions
│   │   ├── icon_fallback.py
│   │   ├── network.py
│   │   └── qr_helper.py
│   ├── __init__.py         # Package initialization
│   ├── config.py           # Configuration management
│   ├── file_validator.py   # File validation and security
│   ├── gui.py              # PySide6 GUI implementation
│   ├── logger.py           # Logging system
│   ├── server.py           # Flask server implementation
│   └── version.py          # Version information
├── logs/                   # Log files directory
├── uploads/                # Default upload directory
├── .gitignore              # Git ignore file
├── config.json             # Configuration file (auto-generated)
├── LICENSE                 # MIT License
├── main.py                 # Main application entry point
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
└── Run.bat                 # Windows batch script to run the app
```

## 📜 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 📙 Acknowledgments

- PySide6 (Qt6) for the GUI framework
- Flask for the web server
- Waitress for production WSGI server
- QRCode for QR code generation
- Humanize for human-readable file sizes

## 🔒 Security Notes

- By default, dangerous file types (executables, scripts) are blocked
- All filenames are sanitized to prevent path traversal attacks
- Rate limiting is enabled to prevent abuse
- The server binds to all interfaces (0.0.0.0) by default - use firewall rules to restrict access
- For additional security, consider using the application only on trusted networks
- Check `config.json` to customize security settings