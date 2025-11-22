"""
Unit tests for Flask server routes
"""

import pytest
import os
import tempfile
import json
from werkzeug.datastructures import FileStorage
from io import BytesIO
from app.server import app, init_password, _password_hash
from werkzeug.security import check_password_hash, generate_password_hash
from app.config import get_config


@pytest.fixture
def test_app():
    """Configure test Flask app"""
    config = get_config()
    original_folder = config.get('storage', 'upload_folder')
    original_protected = config.get('security', 'password_protected', False)
    
    # Create temporary directory
    tmpdir = tempfile.mkdtemp()
    config.data['storage'] = config.data.get('storage', {})
    config.data['storage']['upload_folder'] = tmpdir
    config.data['security'] = config.data.get('security', {})
    config.data['security']['password_protected'] = False
    
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    
    yield app
    
    # Cleanup
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
    config.data['storage']['upload_folder'] = original_folder
    config.data['security']['password_protected'] = original_protected


@pytest.fixture
def client(test_app):
    """Create test client"""
    return test_app.test_client()


@pytest.fixture
def auth_client(test_app):
    """Create authenticated test client"""
    config = get_config()
    config.data['security'] = config.data.get('security', {})
    config.data['security']['password_protected'] = True
    config.data['security']['password'] = 'testpass123'
    
    init_password()
    
    client = test_app.test_client()
    
    # Login
    with client.session_transaction() as sess:
        sess['authenticated'] = True
    
    yield client
    
    config.data['security']['password_protected'] = False


class TestRoutes:
    """Test Flask routes"""
    
    def test_index_no_auth(self, client):
        """Test index route without authentication"""
        config = get_config()
        config.set('password_protected', False)
        
        response = client.get('/')
        assert response.status_code == 200
    
    def test_index_requires_auth(self, client):
        """Test index route requires auth when enabled"""
        config = get_config()
        config.set('password_protected', True)
        
        response = client.get('/')
        # Should redirect to login
        assert response.status_code == 302 or response.status_code == 401
    
    def test_login_page(self, client):
        """Test login page is accessible"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_login_success(self, client):
        """Test successful login"""
        init_password('testpass123')
        
        response = client.post('/login', data={
            'password': 'testpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_login_failure(self, client):
        """Test failed login with wrong password"""
        init_password('testpass123')
        
        response = client.post('/login', data={
            'password': 'wrongpassword'
        })
        
        assert b'Invalid password' in response.data or response.status_code == 401
    
    def test_logout(self, auth_client):
        """Test logout functionality"""
        response = auth_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


class TestFileOperations:
    """Test file upload/download/delete operations"""
    
    def test_upload_file(self, client):
        """Test file upload"""
        config = get_config()
        shared_folder = config.get('storage', 'upload_folder')
        
        # Create test file
        data = {
            'files[]': (BytesIO(b'test content'), 'test.txt')
        }
        
        response = client.post('/upload', 
                              data=data,
                              content_type='multipart/form-data')
        
        assert response.status_code == 200
        
        # Check file was created
        uploaded_file = os.path.join(shared_folder, 'test.txt')
        assert os.path.exists(uploaded_file)
    
    def test_upload_multiple_files(self, client):
        """Test multiple file upload"""
        config = get_config()
        shared_folder = config.get('storage', 'upload_folder')
        
        data = {
            'files[]': [
                (BytesIO(b'content 1'), 'file1.txt'),
                (BytesIO(b'content 2'), 'file2.txt')
            ]
        }
        
        response = client.post('/upload',
                              data=data,
                              content_type='multipart/form-data')
        
        assert response.status_code == 200
        assert os.path.exists(os.path.join(shared_folder, 'file1.txt'))
        assert os.path.exists(os.path.join(shared_folder, 'file2.txt'))
    
    def test_download_file(self, client):
        """Test file download"""
        config = get_config()
        shared_folder = config.get('storage', 'upload_folder')
        
        # Create test file
        test_file = os.path.join(shared_folder, 'download_test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        response = client.get('/download/download_test.txt')
        assert response.status_code == 200
        assert response.data == b'test content'
    
    def test_download_nonexistent_file(self, client):
        """Test downloading file that doesn't exist"""
        response = client.get('/download/nonexistent.txt')
        assert response.status_code == 404
    
    def test_delete_file(self, client):
        """Test file deletion"""
        config = get_config()
        shared_folder = config.get('storage', 'upload_folder')
        
        # Create test file
        test_file = os.path.join(shared_folder, 'delete_test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        response = client.post('/delete/delete_test.txt')
        assert response.status_code == 200
        assert not os.path.exists(test_file)
    
    def test_delete_nonexistent_file(self, client):
        """Test deleting file that doesn't exist"""
        response = client.post('/delete/nonexistent.txt')
        assert response.status_code == 404


class TestSecurity:
    """Test security features"""
    
    def test_path_traversal_upload(self, client):
        """Test that path traversal is prevented in upload"""
        data = {
            'files[]': (BytesIO(b'malicious'), '../../../etc/passwd')
        }
        
        response = client.post('/upload',
                              data=data,
                              content_type='multipart/form-data')
        
        # Should be rejected or sanitized
        config = get_config()
        shared_folder = config.get('storage', 'upload_folder')
        
        # Check that file is not in parent directories
        assert not os.path.exists(os.path.join(shared_folder, '..', '..', '..', 'etc', 'passwd'))
    
    def test_path_traversal_download(self, client):
        """Test that path traversal is prevented in download"""
        response = client.get('/download/../../../etc/passwd')
        assert response.status_code == 400 or response.status_code == 404
    
    def test_path_traversal_delete(self, client):
        """Test that path traversal is prevented in delete"""
        response = client.post('/delete/../../../etc/passwd')
        assert response.status_code == 400 or response.status_code == 404
    
    def test_extension_validation(self, client):
        """Test file extension validation"""
        config = get_config()
        config.set('allowed_extensions', ['.txt', '.pdf'])
        
        # Try uploading disallowed extension
        data = {
            'files[]': (BytesIO(b'executable'), 'malware.exe')
        }
        
        response = client.post('/upload',
                              data=data,
                              content_type='multipart/form-data')
        
        # Should be rejected
        shared_folder = config.get('storage', 'upload_folder')
        assert not os.path.exists(os.path.join(shared_folder, 'malware.exe'))


class TestPasswordProtection:
    """Test password protection functionality"""
    
    def test_init_password(self):
        """Test password initialization"""
        config = get_config()
        config.data['security'] = {'password': 'mypassword'}
        
        init_password()
        
        # Import the password hash
        import app.server as server
        assert server._password_hash is not None
        assert check_password_hash(server._password_hash, 'mypassword')
        assert not check_password_hash(server._password_hash, 'wrongpassword')
    
    def test_check_password_hash_storage(self):
        """Test that passwords are stored as hashes"""
        config = get_config()
        config.data['security'] = {'password': 'securepass', 'password_protected': True}
        
        init_password()
        
        import app.server as server
        # Verify it's not stored in plain text
        assert server._password_hash != 'securepass'
        assert check_password_hash(server._password_hash, 'securepass')
