import os
import base64
import humanize
import uuid
import time
from datetime import datetime
from flask import Flask, request, send_from_directory, render_template, jsonify, redirect, url_for

# Flask app
app = Flask(__name__)

# Folder to save uploaded files
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Dictionary to store shared text (in-memory storage)
# In a production app, this would be in a database
shared_texts = {}

def get_formatted_size(file_path):
    """
    Get human-readable file size
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Human-readable file size (e.g., "1.2 MB")
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return humanize.naturalsize(size_bytes)
    except:
        return "Unknown size"

def get_files_with_sizes():
    """
    Get a list of files in the upload folder with their sizes
    
    Returns:
        list: List of tuples (filename, size)
    """
    try:
        files = os.listdir(UPLOAD_FOLDER)
        result = []
        for filename in files:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                file_size = get_formatted_size(file_path)
                result.append((filename, file_size))
        return result
    except Exception as e:
        print(f"Error getting files: {str(e)}")
        return []

def save_text_to_file(text):
    """
    Save shared text to a file
    
    Args:
        text (str): Text to save
        
    Returns:
        str: Path to the saved file
    """
    try:
        # Create a unique filename
        filename = f"shared_text_{int(time.time())}_{uuid.uuid4().hex[:6]}.txt"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Write text to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
        return filename
    except Exception as e:
        print(f"Error saving text to file: {str(e)}")
        return None

@app.route('/icon/<filename>')
def get_icon(filename):
    """Serve icon files from the templates/icon directory"""
    icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'icon')
    return send_from_directory(icon_dir, filename)

@app.route('/', methods=['GET', 'POST'])
def index():
    """Handle index route with file upload support"""
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
            
        try:
            # Save the file securely
            filename = os.path.basename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            return jsonify({'success': True, 'message': 'File uploaded successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Get shared text if available
    shared_text = None
    shared_text_title = None
    text_id = request.args.get('text_id')
    if text_id and text_id in shared_texts:
        shared_text = shared_texts[text_id]['text']
        shared_text_title = f"Shared text ({shared_texts[text_id]['timestamp']})"
    
    # For GET requests
    files = get_files_with_sizes()
    return render_template('index.html', 
                          files=files,
                          shared_text=shared_text,
                          shared_text_title=shared_text_title)

@app.route('/share_text', methods=['POST'])
def share_text():
    """Handle text sharing"""
    if 'text' not in request.form:
        return jsonify({'success': False, 'error': 'No text provided'}), 400
        
    text = request.form['text']
    if not text:
        return jsonify({'success': False, 'error': 'Text is empty'}), 400
    
    try:
        # Generate a unique ID for this text
        text_id = uuid.uuid4().hex
        
        # Store text in memory
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shared_texts[text_id] = {
            'text': text,
            'timestamp': timestamp
        }
        
        # Also save to file for permanence
        filename = save_text_to_file(text)
        
        # Redirect to the index with the text ID
        return redirect(url_for('index', text_id=text_id))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/uploads/<filename>')
def download_file(filename):
    """
    Route to download a file
    
    Args:
        filename (str): The name of the file to download
        
    Returns:
        Response: The file to download
    """
    try:
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """
    Route to delete a file
    
    Args:
        filename (str): The name of the file to delete
        
    Returns:
        Response: JSON response indicating success or failure
    """
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def run_server(host='0.0.0.0', port=5000, debug=False):
    """
    Run the Flask server
    
    Args:
        host (str): The host to run the server on
        port (int): The port to run the server on
        debug (bool): Whether to run the server in debug mode
    """
    try:
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        print(f"Error starting Flask server: {str(e)}")
        # Here we could implement some fallback or recovery mechanism 