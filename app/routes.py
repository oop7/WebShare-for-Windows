"""
Flask routes for WebShare
Organized route handlers for the web interface
"""

import os
import uuid
from datetime import datetime
from flask import request, send_from_directory, render_template, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename

from app.config import get_config
from app.logger import get_logger
from app.auth import require_auth, check_password, init_password
from app.file_ops import (
    get_files_with_sizes, save_text_to_file, 
    check_rate_limit, record_upload
)
from app.file_validator import (
    sanitize_filename, validate_file_size, validate_total_storage,
    validate_file_count, validate_extension, get_safe_filepath,
    get_storage_stats, is_safe_path
)

config = get_config()
logger = get_logger()

# Dictionary to store shared text (in-memory storage)
shared_texts = {}


def get_upload_folder():
    """Get the configured upload folder path"""
    folder = config.get('storage', 'upload_folder', 'uploads')
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


def register_routes(app):
    """
    Register all routes with the Flask app
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/icon/<filename>')
    def get_icon(filename):
        """Serve icon files from the templates/icon directory"""
        icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'icon')
        return send_from_directory(icon_dir, filename)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Handle user login"""
        if request.method == 'POST':
            password = request.form.get('password', '')
            
            if check_password(password):
                session['authenticated'] = True
                logger.info(f"Successful login from {request.remote_addr}")
                return redirect(url_for('index'))
            else:
                logger.warning(f"Failed login attempt from {request.remote_addr}")
                return render_template('login.html', error="Invalid password")
        
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        """Handle user logout"""
        session.pop('authenticated', None)
        logger.info(f"User logged out from {request.remote_addr}")
        return redirect(url_for('login'))

    @app.route('/', methods=['GET', 'POST'])
    @require_auth
    def index():
        """Handle index route with file upload support"""
        upload_folder = get_upload_folder()
        
        if request.method == 'POST':
            try:
                # Get client IP
                client_ip = request.remote_addr
                
                # Check rate limit
                if not check_rate_limit(client_ip):
                    logger.warning(f"Rate limit exceeded for {client_ip}")
                    return jsonify({'success': False, 'error': 'Too many uploads. Please wait a moment.'}), 429
                
                if 'file' not in request.files:
                    return jsonify({'success': False, 'error': 'No file part'}), 400
                    
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'success': False, 'error': 'No file selected'}), 400
                
                # Sanitize filename
                if config.get('upload', 'sanitize_filenames', True):
                    original_filename = file.filename
                    filename = sanitize_filename(file.filename)
                    if filename != original_filename:
                        logger.info(f"Filename sanitized: '{original_filename}' -> '{filename}'")
                else:
                    filename = secure_filename(file.filename)
                
                # Validate file extension
                allowed_ext = config.get_allowed_extensions()
                blocked_ext = config.get_blocked_extensions()
                is_valid, error_msg = validate_extension(filename, allowed_ext, blocked_ext)
                if not is_valid:
                    logger.warning(f"Blocked file upload: {filename} from {client_ip} - {error_msg}")
                    return jsonify({'success': False, 'error': error_msg}), 400
                
                # Check storage stats
                stats = get_storage_stats(upload_folder)
                
                # Validate file count
                max_files = config.get('upload', 'max_files', 1000)
                is_valid, error_msg = validate_file_count(stats['file_count'], max_files)
                if not is_valid:
                    logger.warning(f"File count limit reached: {stats['file_count']}/{max_files}")
                    return jsonify({'success': False, 'error': error_msg}), 400
                
                # Get file size
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                # Validate file size
                max_size = config.get_max_file_size_bytes()
                is_valid, error_msg = validate_file_size(file_size, max_size)
                if not is_valid:
                    logger.warning(f"File too large: {filename} ({file_size} bytes) from {client_ip}")
                    return jsonify({'success': False, 'error': error_msg}), 400
                
                # Validate total storage
                max_total = config.get_max_total_size_bytes()
                is_valid, error_msg = validate_total_storage(
                    stats['total_size_bytes'], file_size, max_total
                )
                if not is_valid:
                    logger.warning(f"Storage limit would be exceeded: {filename} from {client_ip}")
                    return jsonify({'success': False, 'error': error_msg}), 400
                
                # Get safe file path
                file_path = get_safe_filepath(upload_folder, filename)
                final_filename = os.path.basename(file_path)
                
                # Save the file
                file.save(file_path)
                
                # Record upload for rate limiting
                record_upload(client_ip)
                
                # Log successful upload
                logger.log_upload(final_filename, file_size, client_ip)
                
                return jsonify({
                    'success': True,
                    'message': 'File uploaded successfully',
                    'filename': final_filename
                })
                
            except Exception as e:
                logger.error(f"Error during file upload: {str(e)}", exc_info=True)
                return jsonify({'success': False, 'error': 'An error occurred during upload'}), 500
        
        # GET request - show page
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        logger.log_connection(client_ip, user_agent)
        
        # Get shared text if available
        shared_text = None
        shared_text_title = None
        text_id = request.args.get('text_id')
        if text_id and text_id in shared_texts:
            shared_text = shared_texts[text_id]['text']
            shared_text_title = f"Shared text ({shared_texts[text_id]['timestamp']})"
        
        files = get_files_with_sizes(upload_folder)
        return render_template('index.html', 
                              files=files,
                              shared_text=shared_text,
                              shared_text_title=shared_text_title,
                              password_protected=config.get('security', 'password_protected', False))

    @app.route('/share_text', methods=['POST'])
    @require_auth
    def share_text():
        """Handle text sharing"""
        if 'text' not in request.form:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
            
        text = request.form['text']
        if not text:
            return jsonify({'success': False, 'error': 'Text is empty'}), 400
        
        try:
            upload_folder = get_upload_folder()
            client_ip = request.remote_addr
            
            # Generate a unique ID
            text_id = uuid.uuid4().hex
            
            # Store text in memory
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            shared_texts[text_id] = {
                'text': text,
                'timestamp': timestamp
            }
            
            # Save to file
            filename = save_text_to_file(text, upload_folder)
            
            logger.info(f"Text shared from {client_ip}, saved as {filename}")
            
            return redirect(url_for('index', text_id=text_id))
        except Exception as e:
            logger.error(f"Error sharing text: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': 'An error occurred'}), 500

    @app.route('/uploads/<filename>')
    @require_auth
    def download_file(filename):
        """Download a file"""
        try:
            upload_folder = get_upload_folder()
            filename = os.path.basename(filename)
            
            if not is_safe_path(upload_folder, filename):
                logger.warning(f"Attempted path traversal: {filename} from {request.remote_addr}")
                return jsonify({'success': False, 'error': 'Invalid file path'}), 403
            
            file_path = os.path.join(upload_folder, filename)
            if not os.path.exists(file_path):
                return jsonify({'success': False, 'error': 'File not found'}), 404
            
            logger.log_download(filename, request.remote_addr)
            
            return send_from_directory(upload_folder, filename, as_attachment=True)
        except Exception as e:
            logger.error(f"Error during file download: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': 'An error occurred'}), 500

    @app.route('/delete/<filename>', methods=['DELETE'])
    @require_auth
    def delete_file(filename):
        """Delete a file"""
        try:
            upload_folder = get_upload_folder()
            filename = os.path.basename(filename)
            
            if not is_safe_path(upload_folder, filename):
                logger.warning(f"Attempted path traversal in delete: {filename} from {request.remote_addr}")
                return jsonify({'success': False, 'error': 'Invalid file path'}), 403
            
            file_path = os.path.join(upload_folder, filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.log_delete(filename, request.remote_addr)
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'File not found'}), 404
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': 'An error occurred'}), 500
