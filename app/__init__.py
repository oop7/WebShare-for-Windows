"""
WebShare for Windows application package
"""

# Import version information
from app.version import __version__, __author__

# Import utility functions first
from app.utils import get_local_ip, generate_qr_image, get_pixmap_from_base64

# Then import server functionality
from app.server import app, run_server

# Finally import the GUI class
from app.gui import WebShareApp

# Export all needed symbols
__all__ = ['WebShareApp', 'app', 'run_server', '__version__', '__author__'] 