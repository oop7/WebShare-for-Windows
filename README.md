# WebShare for Windows

WebShare for Windows is a file-sharing application that utilizes PyQt5 for a dark mode GUI and Flask for a local web server. Users can upload and download files easily through a web interface, with QR code support for quick access.

## 💪 Features

- **Local File Sharing**: Upload files from your PC and share them with other devices on the network.
- **QR Code Generation**: Automatically generates a QR code for easy access to the server URL.
- **Dark Mode UI**: A modern, visually appealing interface.
- **File Upload & Download**: List and download files from the web interface.

## 📄 Requirements

- Python 3.x
- See `requirements.txt` for a complete list of dependencies.

## 💻 Installation & Usage

1. Download the latest executable from the [Releases](https://github.com/oop7/WebShare-for-Windows/releases) Section.
  
2. Install the required packages:
```bash
pip install -r requirements.txt
```
3. Run the application:
```bash
Run.bat
```
### **Usage**

1. Click "Start WebShare Server" to launch the local server.
2. A QR code will be generated; scan it to access the web interface.
3. Use the web interface to upload and download files.

## 📜 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 📙 Acknowledgments

- PyQt5
- Flask
- QRCode
