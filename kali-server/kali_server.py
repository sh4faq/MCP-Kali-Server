#!/usr/bin/env python3
"""
Kali Linux Tools API Server - Modular Version

This script connects the MCP AI agent to Kali Linux terminal and API Server.
Refactored into modules for better maintainability.

Some of the code here was inspired from https://github.com/whit3rabbit0/project_astro
"""

import argparse
import logging
import os
import signal
import sys
from flask import Flask

# Import configuration and modules
from core.config import API_PORT, DEBUG_MODE, logger
from api.routes import setup_routes


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    
    # Clean up active sessions
    from core.config import active_sessions, active_ssh_sessions
    
    logger.info("Cleaning up active reverse shell sessions...")
    for session_id, manager in list(active_sessions.items()):
        try:
            manager.stop()
            logger.info(f"Stopped reverse shell session: {session_id}")
        except Exception as e:
            logger.error(f"Error stopping reverse shell session {session_id}: {e}")
    
    logger.info("Cleaning up active SSH sessions...")
    for session_id, manager in list(active_ssh_sessions.items()):
        try:
            manager.stop()
            logger.info(f"Stopped SSH session: {session_id}")
        except Exception as e:
            logger.error(f"Error stopping SSH session {session_id}: {e}")
    
    logger.info("Shutdown complete")
    sys.exit(0)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Setup all API routes
    setup_routes(app)
    
    return app


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Kali Linux API Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=API_PORT, help=f"Port for the API server (default: {API_PORT})")
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    # Parse command line arguments
    args = parse_args()
    
    # Set configuration from command line arguments
    global API_PORT, DEBUG_MODE
    if args.debug:
        DEBUG_MODE = True
        os.environ["DEBUG_MODE"] = "1"
        logger.setLevel(logging.DEBUG)
    
    if args.port != API_PORT:
        API_PORT = args.port
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create Flask application
    app = create_app()
    
    logger.info("="*60)
    logger.info("Kali Linux Tools API Server - Modular Version 2.0")
    logger.info("="*60)
    logger.info(f"Starting server on port {API_PORT}")
    logger.info(f"Debug mode: {DEBUG_MODE}")
    logger.info("Available modules:")
    logger.info("  - SSH Manager: SSH session management")
    logger.info("  - Reverse Shell Manager: Reverse shell handling")
    logger.info("  - Kali Tools: Network scanning and penetration testing tools")
    logger.info("  - File Operations: File upload/download operations")
    logger.info("  - API Routes: RESTful API endpoints")
    logger.info("="*60)
    
    try:
        # Start the Flask server
        app.run(host="0.0.0.0", port=API_PORT, debug=DEBUG_MODE)
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
