#!/usr/bin/env python3
"""
Configuration for Kali server tests.
Simple configuration for Docker environment tests.
"""

import os
from typing import Dict, Any

# Kali server configuration
KALI_SERVER_CONFIG = {
    "host": "localhost",
    "port": 5000,
    "base_url": "http://localhost:5000",
    "timeout": 30
}

# SSH targets configuration - Docker only
SSH_TARGETS = {
    "default_target": {
        "host": "localhost",
        "port": 2222,
        "username": "testuser",
        "password": "testpass",
        "description": "Docker container for SSH tests"
    },
    "root_target": {
        "host": "localhost",
        "port": 2222,
        "username": "root",
        "password": "rootpass",
        "description": "Docker container - root access"
    }
}

# Reverse shell configuration - Docker environment  
REVERSE_SHELL_CONFIG = {
    "listener_port": 4500,  # Use ports not mapped by Docker container
    "alternative_port": 4501,
    "payload_types": ["bash", "python", "netcat", "php"],
    "test_ip": "172.17.0.1"  # Docker bridge IP that works for container communication
}

# Test files and directories
TEST_FILES = {
    "temp_dir": "/tmp",
    "test_file_prefix": "docker_test_",
    "upload_test_file": "upload_test.txt",
    "download_test_file": "download_test.txt",
    "large_file_size": 1024 * 1024,  # 1MB
    "small_file_size": 1024  # 1KB
}

# Configuration des outils Kali pour les tests
KALI_TOOLS_CONFIG = {
    "nmap": {
        "target": REVERSE_SHELL_CONFIG["test_ip"],  # Use Docker IP for tests
        "ports": "22,80,443",
        "scan_types": ["-sT", "-sS", "-sV"]
    },
    "wordlists": {
        "common": "/usr/share/wordlists/dirb/common.txt",
        "rockyou": "/usr/share/wordlists/rockyou.txt"
    }
}

# Timeouts configuration
TIMEOUTS = {
    "quick": 10,
    "medium": 30,
    "long": 180,
    "extended": 300
}

# Messages de test
TEST_MESSAGES = {
    "ssh_test": "SSH Connection Test - {timestamp}",
    "upload_test": "Test file for upload - Generated: {timestamp}",
    "download_test": "Content for download test - Session: {session_id}"
}

def get_ssh_target(target_name: str = "default_target") -> Dict[str, Any]:
    """Get SSH target configuration."""
    return SSH_TARGETS.get(target_name, SSH_TARGETS["default_target"])

def get_test_file_content(test_type: str, **kwargs) -> str:
    """Generate test file content."""
    import time
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    env_type = "Docker Container"
    base_content = f"""# Test File - {test_type.upper()}
Generated: {timestamp}
Test Type: {test_type}
Environment: {env_type}
"""
    
    for key, value in kwargs.items():
        base_content += f"{key}: {value}\n"
    
    base_content += f"""
This is test content for {test_type} operations.
The file should be used for testing upload/download functionality.
Random data: {hash(timestamp) % 1000000}
"""
    return base_content

def get_large_test_content(size_bytes: int) -> str:
    """Generate test content of specific size."""
    import time
    env_type = "Docker"
    base_content = f"Large {env_type} test file - Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    base_content += f"Target size: {size_bytes} bytes\n"
    
    padding_size = size_bytes - len(base_content.encode())
    
    if padding_size > 0:
        # More varied pattern for better testing
        pattern = f"{env_type}_TEST_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
        repetitions = (padding_size // len(pattern)) + 1
        padding = (pattern * repetitions)[:padding_size]
        base_content += padding
    
    return base_content

def validate_environment() -> Dict[str, bool]:
    """Validate that test environment is ready."""
    checks = {}
    
    # Check Kali server accessibility
    try:
        import requests
        response = requests.get(f"{KALI_SERVER_CONFIG['base_url']}/health", timeout=5)
        checks["kali_server"] = response.status_code == 200
    except:
        checks["kali_server"] = False
    
    # Docker-specific checks
    try:
        import subprocess
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        checks["docker_installed"] = result.returncode == 0
    except:
        checks["docker_installed"] = False
        
    # Check container running
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 
                               'name=kali-test-ssh',
                               '--format', '{{.Status}}'], 
                              capture_output=True, text=True)
        checks["container_running"] = "Up" in result.stdout
    except:
        checks["container_running"] = False
        
    # Check SSH port accessible
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 2222))
        checks["ssh_port_open"] = result == 0
        sock.close()
    except:
        checks["ssh_port_open"] = False
    
    # Common checks
    checks["temp_dir"] = os.path.exists("/tmp") if os.name != 'nt' else True  # Windows compatibility
    
    return checks

def get_docker_test_ip() -> str:
    """Get the Docker bridge IP for tests."""
    return REVERSE_SHELL_CONFIG["test_ip"]

def get_pentest_ip() -> str:
    """Get the IP to use for pentest scenarios (fallback to Docker IP for tests)."""
    return REVERSE_SHELL_CONFIG["test_ip"]

# Environment info
print("🐳 Using Docker configuration with fixed IPs")

# Environment variables for configuration override
def load_env_overrides():
    """Load overrides from environment variables."""
    
    # Override Kali server configuration
    if os.getenv("KALI_SERVER_HOST"):
        KALI_SERVER_CONFIG["host"] = os.getenv("KALI_SERVER_HOST")
    if os.getenv("KALI_SERVER_PORT"):
        KALI_SERVER_CONFIG["port"] = int(os.getenv("KALI_SERVER_PORT"))
        KALI_SERVER_CONFIG["base_url"] = f"http://{KALI_SERVER_CONFIG['host']}:{KALI_SERVER_CONFIG['port']}"

# Load environment overrides on import
load_env_overrides()

if __name__ == "__main__":
    env_type = "Docker"
    print(f"=== {env_type} Test Configuration ===")
    print(f"Environment: Docker containers only")
    print(f"Kali server: {KALI_SERVER_CONFIG['base_url']}")
    print(f"SSH target: {SSH_TARGETS['default_target']['username']}@{SSH_TARGETS['default_target']['host']}:{SSH_TARGETS['default_target']['port']}")
    print(f"Temp directory: {TEST_FILES['temp_dir']}")
    
    print(f"\n=== Environment Validation ===")
    env_checks = validate_environment()
    for check, status in env_checks.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check}: {'OK' if status else 'FAIL'}")
