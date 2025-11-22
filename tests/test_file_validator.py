"""
Unit tests for file validation and security utilities
"""

import pytest
import os
import tempfile
from app.file_validator import (
    sanitize_filename, validate_file_size, validate_total_storage,
    validate_file_count, validate_extension, get_safe_filepath,
    get_storage_stats, is_safe_path
)


class TestFilenameSanitization:
    """Test cases for filename sanitization"""
    
    def test_basic_filename(self):
        """Test that normal filenames pass through"""
        assert sanitize_filename('document.pdf') == 'document.pdf'
        assert sanitize_filename('photo.jpg') == 'photo.jpg'
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked"""
        assert '../../../etc/passwd' not in sanitize_filename('../../../etc/passwd')
        assert '..' not in sanitize_filename('../../file.txt')
        assert sanitize_filename('..\\..\\windows\\system32') != '..\\..\\windows\\system32'
    
    def test_dangerous_characters_removed(self):
        """Test that dangerous characters are removed"""
        result = sanitize_filename('file<>:"|?*.txt')
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result
        assert '"' not in result
        assert '|' not in result
        assert '?' not in result
        assert '*' not in result
    
    def test_null_bytes_removed(self):
        """Test that null bytes are removed"""
        result = sanitize_filename('file\x00.txt')
        assert '\x00' not in result
    
    def test_leading_trailing_dots_spaces(self):
        """Test that leading/trailing dots and spaces are removed"""
        assert sanitize_filename('  file.txt  ') == 'file.txt'
        assert sanitize_filename('..file.txt..') == 'file.txt'
        assert sanitize_filename('. file.txt .') == 'file.txt'
    
    def test_empty_filename_default(self):
        """Test that empty filenames get a default name"""
        assert sanitize_filename('') == 'unnamed_file'
        assert sanitize_filename('   ') == 'unnamed_file'
    
    def test_max_length_truncation(self):
        """Test that long filenames are truncated"""
        long_name = 'a' * 300 + '.txt'
        result = sanitize_filename(long_name, max_length=255)
        assert len(result) <= 255
        assert result.endswith('.txt')


class TestFileValidation:
    """Test cases for file validation"""
    
    def test_validate_file_size_valid(self):
        """Test validation of valid file sizes"""
        max_size = 10 * 1024 * 1024  # 10 MB
        valid, error = validate_file_size(5 * 1024 * 1024, max_size)
        assert valid is True
        assert error is None
    
    def test_validate_file_size_too_large(self):
        """Test validation of oversized files"""
        max_size = 10 * 1024 * 1024  # 10 MB
        valid, error = validate_file_size(20 * 1024 * 1024, max_size)
        assert valid is False
        assert error is not None
        assert 'exceeds maximum' in error.lower()
    
    def test_validate_file_size_empty(self):
        """Test validation of empty files"""
        valid, error = validate_file_size(0, 10 * 1024 * 1024)
        assert valid is False
        assert 'empty' in error.lower()
    
    def test_validate_total_storage_valid(self):
        """Test total storage validation when within limits"""
        current = 5 * 1024 * 1024 * 1024  # 5 GB
        new_file = 1 * 1024 * 1024 * 1024  # 1 GB
        max_total = 10 * 1024 * 1024 * 1024  # 10 GB
        
        valid, error = validate_total_storage(current, new_file, max_total)
        assert valid is True
        assert error is None
    
    def test_validate_total_storage_exceeded(self):
        """Test total storage validation when limit would be exceeded"""
        current = 9 * 1024 * 1024 * 1024  # 9 GB
        new_file = 2 * 1024 * 1024 * 1024  # 2 GB
        max_total = 10 * 1024 * 1024 * 1024  # 10 GB
        
        valid, error = validate_total_storage(current, new_file, max_total)
        assert valid is False
        assert 'storage limit' in error.lower()
    
    def test_validate_file_count_valid(self):
        """Test file count validation when within limits"""
        valid, error = validate_file_count(50, 100)
        assert valid is True
        assert error is None
    
    def test_validate_file_count_exceeded(self):
        """Test file count validation when limit reached"""
        valid, error = validate_file_count(100, 100)
        assert valid is False
        assert 'maximum file count' in error.lower()


class TestExtensionValidation:
    """Test cases for file extension validation"""
    
    def test_validate_extension_allowed(self):
        """Test validation of allowed extensions"""
        allowed = ['.pdf', '.jpg', '.png']
        blocked = ['.exe', '.bat']
        
        valid, error = validate_extension('document.pdf', allowed, blocked)
        assert valid is True
        assert error is None
    
    def test_validate_extension_blocked(self):
        """Test validation of blocked extensions"""
        allowed = []
        blocked = ['.exe', '.bat', '.ps1']
        
        valid, error = validate_extension('malware.exe', allowed, blocked)
        assert valid is False
        assert 'not allowed' in error.lower()
    
    def test_validate_extension_not_in_whitelist(self):
        """Test validation when extension not in whitelist"""
        allowed = ['.pdf', '.jpg']
        blocked = []
        
        valid, error = validate_extension('document.docx', allowed, blocked)
        assert valid is False
        assert 'only these file types' in error.lower()
    
    def test_validate_extension_no_extension(self):
        """Test validation of files without extension"""
        valid, error = validate_extension('README', [], [])
        assert valid is False
        assert 'must have an extension' in error.lower()


class TestSafePath:
    """Test cases for safe path handling"""
    
    def test_safe_filepath_simple(self):
        """Test getting safe filepath for non-existent file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = get_safe_filepath(tmpdir, 'test.txt')
            assert filepath == os.path.join(tmpdir, 'test.txt')
    
    def test_safe_filepath_duplicate(self):
        """Test getting safe filepath when file exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing file
            existing = os.path.join(tmpdir, 'test.txt')
            with open(existing, 'w') as f:
                f.write('test')
            
            # Get safe path for duplicate
            filepath = get_safe_filepath(tmpdir, 'test.txt')
            assert filepath != existing
            assert 'test_1.txt' in filepath
    
    def test_is_safe_path_valid(self):
        """Test that safe paths are recognized"""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert is_safe_path(tmpdir, 'file.txt') is True
            assert is_safe_path(tmpdir, 'subfolder/file.txt') is True
    
    def test_is_safe_path_traversal(self):
        """Test that path traversal attempts are blocked"""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert is_safe_path(tmpdir, '../../../etc/passwd') is False
            assert is_safe_path(tmpdir, '..\\..\\windows\\system32') is False


class TestStorageStats:
    """Test cases for storage statistics"""
    
    def test_get_storage_stats_empty(self):
        """Test getting stats for empty directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats = get_storage_stats(tmpdir)
            assert stats['file_count'] == 0
            assert stats['total_size_bytes'] == 0
    
    def test_get_storage_stats_with_files(self):
        """Test getting stats for directory with files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            for i in range(3):
                filepath = os.path.join(tmpdir, f'file{i}.txt')
                with open(filepath, 'w') as f:
                    f.write('x' * 100)  # 100 bytes each
            
            stats = get_storage_stats(tmpdir)
            assert stats['file_count'] == 3
            assert stats['total_size_bytes'] == 300
    
    def test_get_storage_stats_nonexistent(self):
        """Test getting stats for non-existent directory"""
        stats = get_storage_stats('/nonexistent/path')
        assert stats['file_count'] == 0
        assert stats['total_size_bytes'] == 0
