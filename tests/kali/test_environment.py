#!/usr/bin/env python3
"""
Pre-check test - Run before complete tests.
Verifies that environment is ready for SSH tests.
"""

import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_config import KALI_SERVER_CONFIG, SSH_TARGETS, validate_environment

def test_kali_server():
    """Test if Kali server is accessible."""
    print("🔍 Testing Kali server...")
    try:
        response = requests.get(f"{KALI_SERVER_CONFIG['base_url']}/health", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Kali server accessible: {KALI_SERVER_CONFIG['base_url']}")
            return True
        else:
            print(f"   ❌ Server responds but error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Kali server not accessible: {e}")
        print(f"   💡 Start server: cd kali-server && sudo python kali_server_modular.py")
        return False

def test_ssh_connectivity():
    """Basic SSH connectivity test."""
    print("🔍 Testing SSH connectivity...")
    ssh_config = SSH_TARGETS["default_target"]
    
    payload = {
        "target": ssh_config["host"],
        "username": ssh_config["username"],
        "password": ssh_config["password"],
        "port": ssh_config["port"],
        "session_id": "connectivity_test"
    }
    
    try:
        # Test session start
        start_response = requests.post(
            f"{KALI_SERVER_CONFIG['base_url']}/api/ssh/session/start",
            json=payload,
            timeout=30
        )
        
        if start_response.status_code != 200:
            print(f"   ❌ SSH API error: {start_response.status_code}")
            return False
        
        data = start_response.json()
        if not data.get("success"):
            print(f"   ❌ SSH failed: {data.get('error', 'Unknown')}")
            print(f"   💡 Check: {ssh_config['username']}@{ssh_config['host']}:{ssh_config['port']}")
            print(f"   💡 Password: {ssh_config['password']}")
            return False
        
        print(f"   ✅ SSH OK: {ssh_config['username']}@{ssh_config['host']}:{ssh_config['port']}")
        
        # Clean up test session
        try:
            requests.post(
                f"{KALI_SERVER_CONFIG['base_url']}/api/ssh/session/connectivity_test/stop",
                timeout=10
            )
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"   ❌ SSH test error: {e}")
        return False

def main():
    """Complete environment verification."""
    print("🧪 SSH TESTS ENVIRONMENT VERIFICATION")
    print("="*50)
    
    all_ok = True
    
    # Test 1: Kali Server
    if not test_kali_server():
        all_ok = False
    
    # Test 2: SSH (only if server OK)
    if all_ok:
        if not test_ssh_connectivity():
            all_ok = False
    
    # Test 3: General validation
    print("\n🔍 General environment validation...")
    env_checks = validate_environment()
    for check, status in env_checks.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {check}")
        if not status:
            all_ok = False
    
    # Final result
    print("\n" + "="*50)
    if all_ok:
        print("🎉 ENVIRONMENT READY FOR TESTS!")
        print("💡 Run tests: pytest test_ssh_manager.py")
        return 0
    else:
        print("❌ ENVIRONMENT NOT READY")
        print("💡 Fix errors above before running tests")
        return 1

if __name__ == "__main__":
    sys.exit(main())
