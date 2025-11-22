"""
WebShare Flask Server - Refactored
Main server initialization and runner
"""

import os
from flask import Flask

from app.config import get_config
from app.logger import get_logger
from app.auth import init_password
from app.routes import register_routes

# Get configuration and logger
config = get_config()
logger = get_logger()


def create_app():
    """
    Create and configure the Flask application
    
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = None  # Manual checking with better error handling
    app.config['SECRET_KEY'] = os.urandom(24)  # For session management
    
    # Register all routes
    register_routes(app)
    
    return app


# Create the app instance
app = create_app()


def run_server(host='0.0.0.0', port=5000, debug=False):
    """
    Run the Flask server using Waitress (production WSGI server)
    
    Args:
        host (str): The host to run the server on
        port (int): The port to run the server on
        debug (bool): Whether to run in debug mode (uses Flask dev server if True)
    """
    try:
        # Initialize password protection
        init_password()
        
        logger.log_server_start(host, port)
        
        if debug:
            # Use Flask development server in debug mode
            logger.warning("Running in DEBUG mode with Flask development server")
            app.run(host=host, port=port, debug=True)
        else:
            # Use Waitress production server
            from waitress import serve
            logger.info(f"Starting Waitress production server on {host}:{port}")
            serve(app, host=host, port=port, threads=config.get('server', 'max_connections', 100))
    except ImportError:
        logger.error("Waitress not installed, falling back to Flask development server")
        logger.warning("For production use, please install waitress: pip install waitress")
        app.run(host=host, port=port, debug=False)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}", exc_info=True)
        raise
