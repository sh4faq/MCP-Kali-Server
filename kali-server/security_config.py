"""
Security configuration for MCP-Kali-Server
This module provides security hardening for the API server
"""

import hashlib
import hmac
import time
from functools import wraps
from flask import request, jsonify

# Configuration
API_KEY = "change-this-to-a-strong-random-key"  # Change this!
ALLOWED_IPS = ["127.0.0.1", "192.168.229.0/24"]  # Adjust for your network
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB max request size
RATE_LIMIT = 100  # Max requests per minute per IP

# Rate limiting storage (simple in-memory for demonstration)
request_counts = {}

def check_ip_whitelist(ip_address):
    """Check if IP is in whitelist"""
    import ipaddress
    
    client_ip = ipaddress.ip_address(ip_address)
    
    for allowed in ALLOWED_IPS:
        if '/' in allowed:  # CIDR notation
            if client_ip in ipaddress.ip_network(allowed):
                return True
        elif str(client_ip) == allowed:
            return True
    
    return False

def rate_limit_check(ip_address):
    """Simple rate limiting"""
    current_minute = int(time.time() / 60)
    key = f"{ip_address}:{current_minute}"
    
    if key in request_counts:
        if request_counts[key] >= RATE_LIMIT:
            return False
        request_counts[key] += 1
    else:
        # Clean old entries
        old_keys = [k for k in request_counts if not k.endswith(str(current_minute))]
        for k in old_keys:
            del request_counts[k]
        request_counts[key] = 1
    
    return True

def security_check(f):
    """Decorator for security checks"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check IP whitelist
        client_ip = request.remote_addr
        if not check_ip_whitelist(client_ip):
            return jsonify({"error": "Unauthorized IP"}), 403
        
        # Check rate limit
        if not rate_limit_check(client_ip):
            return jsonify({"error": "Rate limit exceeded"}), 429
        
        # Check request size
        if request.content_length and request.content_length > MAX_REQUEST_SIZE:
            return jsonify({"error": "Request too large"}), 413
        
        # Check API key (optional - uncomment to enable)
        # api_key = request.headers.get('X-API-Key')
        # if api_key != API_KEY:
        #     return jsonify({"error": "Invalid API key"}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

# Command sanitization
def sanitize_command(command):
    """Basic command sanitization"""
    # Prevent common injection patterns
    dangerous_patterns = [';', '&&', '||', '|', '`', '$', '>', '<', '&']
    for pattern in dangerous_patterns:
        if pattern in command:
            # Use shlex.quote for proper escaping instead
            import shlex
            return shlex.quote(command)
    return command
