import sys
import os
import qrcode
import base64
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QIcon
from flask import Flask, request, send_from_directory, render_template_string
import threading
import socket

# Flask app
flask_app = Flask(__name__)

# Folder to save uploaded files
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

BASE64_IMAGE = "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"  # Replace with your actual Base64 image string

def get_pixmap_from_base64(base64_string):
    image_data = base64.b64decode(base64_string)
    pixmap = QPixmap()
    pixmap.loadFromData(image_data)
    return pixmap

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebShare</title>
    <link rel="icon" href="data:image/png;base64,{image}" type="image/png">
    <style>
        body {{
            background-color: #11171d;
            color: white;
            font-family: Arial, sans-serif;
        }}
        img {{
            display: block;
            margin: 0 auto;
            max-width: 150px;
            padding-top: 20px;
        }}
        h1, h2 {{
            text-align: center;
        }}
        form {{
            text-align: center;
            margin-bottom: 20px;
        }}
        input[type="submit"] {{
            background-color: #ffffff;
            color: #11171d;
            padding: 10px;
            border: none;
            cursor: pointer;
        }}
        a {{
            color: white;
        }}
    </style>
</head>
<body>
    <img src="data:image/png;base64,{image}" alt="Logo">
    <h1>File Sharing</h1>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" style="margin-bottom: 10px;">
        <input type="submit" value="Upload">
    </form>
    <h2>Files:</h2>
    <ul>
        {{% for filename in files %}}
        <li><a href="{{{{ url_for('download_file', filename=filename) }}}}">{{{{ filename }}}}</a></li>
        {{% endfor %}}
    </ul>
</body>
</html>
'''.format(image=BASE64_IMAGE)

@flask_app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    files = os.listdir(UPLOAD_FOLDER)
    return render_template_string(HTML_TEMPLATE, files=files)

@flask_app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def run_flask():
    flask_app.run(host='0.0.0.0', port=5000)

class WebShareApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("WebShare for Windows")
        
        # Set window icon
        self.setWindowIcon(QIcon(get_pixmap_from_base64(BASE64_IMAGE)))

        layout = QVBoxLayout()

        # Apply dark mode stylesheet
        self.setStyleSheet("""
            QWidget {
                background-color: #11171d;
                color: white;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #444;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QLabel {
                margin: 10px;
            }
        """)

        # Start Server Button
        self.start_button = QPushButton("Start WebShare Server", self)
        self.start_button.clicked.connect(self.start_server)
        layout.addWidget(self.start_button)

        # QR Code Display
        self.qr_label = QLabel(self)
        layout.addWidget(self.qr_label)

        # Open Folder Button
        self.open_folder_button = QPushButton("Open Upload Folder", self)
        self.open_folder_button.clicked.connect(self.open_folder)
        layout.addWidget(self.open_folder_button)

        self.setLayout(layout)

    def start_server(self):
        local_ip = get_local_ip()
        url = f'http://{local_ip}:5000'
        self.generate_qr(url)

        # Run Flask server in a separate thread
        threading.Thread(target=run_flask, daemon=True).start()
        self.start_button.setText(f"Server running at {url}")

    def generate_qr(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        img.save('qr_code.png')

        pixmap = QPixmap('qr_code.png')
        self.qr_label.setPixmap(pixmap)

    def open_folder(self):
        folder_path = os.path.abspath(UPLOAD_FOLDER)
        os.startfile(folder_path)

# Main function
if __name__ == '__main__':
    qt_app = QApplication(sys.argv)
    webshare = WebShareApp()
    webshare.show()
    sys.exit(qt_app.exec_())
