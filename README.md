# WebShare for Windows

WebShare for Windows is a file-sharing application that utilizes PyQt5 for a dark mode GUI and Flask for a local web server. Users can upload and download files easily through a web interface, with QR code support for quick access.

## 💪 Features

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

## 🏗️ Project Structure

```
WebShare-for-Windows/
├── app/                    # Application package
│   ├── static/             # Static files for Flask
│   ├── templates/          # HTML templates
│   ├── utils/              # Utility functions
│   ├── __init__.py         # Package initialization
│   ├── gui.py              # PyQt5 GUI implementation
│   └── server.py           # Flask server implementation
├── uploads/                # Default upload directory
├── .gitignore              # Git ignore file
├── LICENSE                 # MIT License
├── main.py                 # Main application entry point
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
└── Run.bat                 # Windows batch script to run the app
```

## 📜 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 📙 Acknowledgments

- PyQt5 for the GUI framework
- Flask for the web server
- QRCode for QR code generation
- Humanize for human-readable file sizes
