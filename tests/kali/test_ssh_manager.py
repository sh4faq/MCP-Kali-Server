#!/usr/bin/env python3
"""
Complete tests for SSH Manager of the Kali server.
This file tests all SSH manager functionalities.
"""

import unittest
import requests
import time
import base64
import hashlib
import json
from typing import Dict, Any
import sys
import os
import pytest

# Import unified configuration
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_config import (
    KALI_SERVER_CONFIG, SSH_TARGETS, TEST_FILES, TIMEOUTS,
    get_ssh_target, get_test_file_content, get_large_test_content,
    validate_environment
)

# Display Docker configuration (only supported option)
print("� Docker configuration loaded")
print(f"   SSH target: {SSH_TARGETS['default_target']['host']}:{SSH_TARGETS['default_target']['port']}")


class TestSSHManager(unittest.TestCase):
    """Tests for SSH Manager"""
    
    @classmethod
    def setUpClass(cls):
        """Setup before all tests."""
        print("\n" + "="*60)
        print("🧪 SSH MANAGER TESTS - Kali Server")
        print("="*60)
        
        # Validate environment
        env_checks = validate_environment()
        if not env_checks["kali_server"]:
            raise unittest.SkipTest("❌ Kali server not accessible")
        
        cls.base_url = KALI_SERVER_CONFIG["base_url"]
        cls.ssh_config = get_ssh_target()
        cls.session_prefix = f"test_ssh_{int(time.time())}"
        cls.active_sessions = []
        
        print(f"🎯 SSH Target: {cls.ssh_config['username']}@{cls.ssh_config['host']}:{cls.ssh_config['port']}")
        print(f"🚀 Server: {cls.base_url}")
        print("-"*60)
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests."""
        print("\n" + "-"*60)
        print("🧹 Cleaning up SSH sessions...")
        
        # Stop all active sessions
        for session_id in cls.active_sessions:
            try:
                requests.post(f"{cls.base_url}/api/ssh/session/{session_id}/stop", timeout=10)
                print(f"   ✅ Session {session_id} stopped")
            except:
                print(f"   ⚠️  Error stopping session {session_id}")
        
        print("="*60)
    
    def setUp(self):
        """Setup before each test."""
        self.session_id = f"{self.session_prefix}_{len(self.active_sessions)}"
    
    def tearDown(self):
        """Cleanup after each test."""
        # Stop session if it exists
        if hasattr(self, 'session_id') and self.session_id in self.active_sessions:
            try:
                self._stop_ssh_session(self.session_id)
            except:
                pass
    
    def _start_ssh_session(self, session_id: str = None) -> Dict[str, Any]:
        """Start an SSH session."""
        if session_id is None:
            session_id = self.session_id
        
        payload = {
            "target": self.ssh_config["host"],
            "username": self.ssh_config["username"],
            "password": self.ssh_config["password"],
            "port": self.ssh_config["port"],
            "session_id": session_id
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/ssh/session/start",
                json=payload,
                timeout=TIMEOUTS["medium"]
            )
            
            if response.status_code == 200:
                self.active_sessions.append(session_id)
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Kali server connection error: {e}")
            self.fail(f"Cannot connect to Kali server: {e}")
            
        return response
    
    def _stop_ssh_session(self, session_id: str) -> requests.Response:
        """Stop an SSH session."""
        response = requests.post(
            f"{self.base_url}/api/ssh/session/{session_id}/stop",
            timeout=TIMEOUTS["quick"]
        )
        
        if session_id in self.active_sessions:
            self.active_sessions.remove(session_id)
        
        return response
    
    def _execute_ssh_command(self, session_id: str, command: str, timeout: int = None) -> requests.Response:
        """Execute an SSH command."""
        if timeout is None:
            timeout = TIMEOUTS["medium"]
        
        payload = {
            "command": command,
            "timeout": timeout
        }
        
        return requests.post(
            f"{self.base_url}/api/ssh/session/{session_id}/command",
            json=payload,
            timeout=timeout + 5
        )
    
    @pytest.mark.ssh
    def test_01_ssh_session_start_stop(self):
        """Test: SSH session start and stop."""
        print("\n🔌 Test: SSH session start/stop")
        
        # Start session
        response = self._start_ssh_session()
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        if not data.get("success"):
            print(f"   ❌ SSH error: {data.get('error', 'Unknown')}")
            self.fail(f"SSH session failed: {data.get('error', 'Unknown')}")
        
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("session_id"), self.session_id)
        print(f"   ✅ Session started: {self.session_id}")
        
        # Check status
        status_response = requests.get(f"{self.base_url}/api/ssh/session/{self.session_id}/status")
        self.assertEqual(status_response.status_code, 200)
        
        status_data = status_response.json()
        self.assertTrue(status_data.get("is_connected"))
        print(f"   ✅ Status verified: connected")
        
        # Stop session
        stop_response = self._stop_ssh_session(self.session_id)
        self.assertEqual(stop_response.status_code, 200)
        print(f"   ✅ Session stopped")
    
    def test_02_ssh_command_execution(self):
        """Test: SSH command execution."""
        print("\n💻 Test: SSH command execution")
        
        # Start session
        response = self._start_ssh_session()
        self.assertEqual(response.status_code, 200)
        print(f"   📡 Session started: {self.session_id}")
        
        # Test simple commands
        test_commands = [
            ("echo 'Hello SSH'", "Hello SSH"),
            ("whoami", self.ssh_config["username"]),
            ("pwd", "/"),
            ("uname -s", "Linux")
        ]
        
        for command, expected_in_output in test_commands:
            with self.subTest(command=command):
                cmd_response = self._execute_ssh_command(self.session_id, command)
                self.assertEqual(cmd_response.status_code, 200)
                
                cmd_data = cmd_response.json()
                self.assertTrue(cmd_data.get("success"))
                
                output = cmd_data.get("output", "")
                self.assertIn(expected_in_output, output)
                print(f"   ✅ '{command}' → '{output.strip()}'")
    
    def test_03_ssh_file_operations(self):
        """Test: SSH file operations."""
        print("\n📁 Test: SSH file operations")
        
        # Start session
        response = self._start_ssh_session()
        self.assertEqual(response.status_code, 200)
        print(f"   📡 Session started: {self.session_id}")
        
        # Create test file
        test_file = f"{TEST_FILES['temp_dir']}/ssh_test_{int(time.time())}.txt"
        test_content = "SSH File Operations Test Content"
        
        # Create file
        create_cmd = f"echo '{test_content}' > {test_file}"
        create_response = self._execute_ssh_command(self.session_id, create_cmd)
        self.assertEqual(create_response.status_code, 200)
        print(f"   ✅ File created: {test_file}")
        
        # Check existence
        check_cmd = f"test -f {test_file} && echo 'EXISTS' || echo 'NOT_EXISTS'"
        check_response = self._execute_ssh_command(self.session_id, check_cmd)
        self.assertEqual(check_response.status_code, 200)
        self.assertIn("EXISTS", check_response.json().get("output", ""))
        print(f"   ✅ Existence verified")
        
        # Read content
        read_cmd = f"cat {test_file}"
        read_response = self._execute_ssh_command(self.session_id, read_cmd)
        self.assertEqual(read_response.status_code, 200)
        self.assertIn(test_content, read_response.json().get("output", ""))
        print(f"   ✅ Content read and verified")
        
        # Delete file
        rm_cmd = f"rm -f {test_file}"
        rm_response = self._execute_ssh_command(self.session_id, rm_cmd)
        self.assertEqual(rm_response.status_code, 200)
        print(f"   ✅ File deleted")
    
    @pytest.mark.ssh
    @pytest.mark.upload
    def test_04_ssh_upload_content(self):
        """Test: SSH content upload."""
        print("\n📤 Test: SSH content upload")
        
        # Start session
        response = self._start_ssh_session()
        self.assertEqual(response.status_code, 200)
        print(f"   📡 Session started: {self.session_id}")
        
        # Prepare content to upload
        test_content = get_test_file_content("upload", session_id=self.session_id)
        content_b64 = base64.b64encode(test_content.encode()).decode()
        remote_file = f"{TEST_FILES['temp_dir']}/upload_test_{int(time.time())}.txt"
        
        # Upload content
        upload_payload = {
            "content": content_b64,
            "remote_file": remote_file,
            "encoding": "base64"
        }
        
        upload_response = requests.post(
            f"{self.base_url}/api/ssh/session/{self.session_id}/upload_content",
            json=upload_payload,
            timeout=TIMEOUTS["medium"]
        )
        
        self.assertEqual(upload_response.status_code, 200)
        upload_data = upload_response.json()
        self.assertTrue(upload_data.get("success"))
        print(f"   ✅ Upload successful: {len(test_content)} bytes")
        
        # Verify uploaded file
        verify_cmd = f"cat {remote_file}"
        verify_response = self._execute_ssh_command(self.session_id, verify_cmd)
        self.assertEqual(verify_response.status_code, 200)
        
        uploaded_content = verify_response.json().get("output", "")
        self.assertIn("upload", uploaded_content)
        self.assertIn(self.session_id, uploaded_content)
        print(f"   ✅ Content verified on target")
        
        # Clean up
        cleanup_cmd = f"rm -f {remote_file}"
        self._execute_ssh_command(self.session_id, cleanup_cmd)
        print(f"   🧹 File cleaned up")
    
    @pytest.mark.ssh
    @pytest.mark.download
    def test_05_ssh_download_content(self):
        """Test: SSH content download."""
        print("\n📥 Test: SSH content download")
        
        # Start session
        response = self._start_ssh_session()
        self.assertEqual(response.status_code, 200)
        print(f"   📡 Session started: {self.session_id}")
        
        # Create file on target
        test_content = get_test_file_content("download", session_id=self.session_id)
        remote_file = f"{TEST_FILES['temp_dir']}/download_test_{int(time.time())}.txt"
        
        create_cmd = f"cat > {remote_file} << 'EOL'\n{test_content}\nEOL"
        create_response = self._execute_ssh_command(self.session_id, create_cmd, timeout=TIMEOUTS["quick"])
        self.assertEqual(create_response.status_code, 200)
        print(f"   ✅ File created on target: {len(test_content)} bytes")
        
        # Download content
        download_payload = {
            "remote_file": remote_file,
            "method": "direct"
        }
        
        download_response = requests.post(
            f"{self.base_url}/api/ssh/session/{self.session_id}/download_content",
            json=download_payload,
            timeout=TIMEOUTS["medium"]
        )
        
        self.assertEqual(download_response.status_code, 200)
        download_data = download_response.json()
        self.assertTrue(download_data.get("success"))
        
        # Decode and verify content
        content_b64 = download_data.get("content", "")
        self.assertTrue(len(content_b64) > 0, "Empty base64 content")
        
        decoded_content = base64.b64decode(content_b64).decode()
        self.assertIn("download", decoded_content)
        self.assertIn(self.session_id, decoded_content)
        print(f"   ✅ Download successful: {len(decoded_content)} bytes")
        print(f"   ✅ Content verified")
        
        # Clean up
        cleanup_cmd = f"rm -f {remote_file}"
        self._execute_ssh_command(self.session_id, cleanup_cmd)
        print(f"   🧹 File cleaned up")
    
    @pytest.mark.ssh
    @pytest.mark.slow
    def test_06_ssh_large_file_operations(self):
        """Test: SSH large file operations."""
        print("\n📊 Test: SSH large files")
        
        # Start session
        response = self._start_ssh_session()
        self.assertEqual(response.status_code, 200)
        print(f"   📡 Session started: {self.session_id}")
        
        # Create large content (100KB)
        large_content = get_large_test_content(100 * 1024)  # 100KB
        content_md5 = hashlib.md5(large_content.encode()).hexdigest()
        content_b64 = base64.b64encode(large_content.encode()).decode()
        remote_file = f"{TEST_FILES['temp_dir']}/large_test_{int(time.time())}.txt"
        
        print(f"   📊 Content size: {len(large_content)} bytes (MD5: {content_md5[:8]}...)")
        
        # Upload large file
        upload_payload = {
            "content": content_b64,
            "remote_file": remote_file,
            "encoding": "base64"
        }
        
        upload_start = time.time()
        upload_response = requests.post(
            f"{self.base_url}/api/ssh/session/{self.session_id}/upload_content",
            json=upload_payload,
            timeout=TIMEOUTS["long"]
        )
        upload_time = time.time() - upload_start
        
        self.assertEqual(upload_response.status_code, 200)
        self.assertTrue(upload_response.json().get("success"))
        print(f"   ✅ Large file upload: {upload_time:.2f}s")
        
        # Download and verify
        download_payload = {
            "remote_file": remote_file,
            "method": "auto",  # Automatic method selection
            "max_size_mb": 1   # Accept up to 1MB
        }
        
        download_start = time.time()
        download_response = requests.post(
            f"{self.base_url}/api/ssh/session/{self.session_id}/download_content",
            json=download_payload,
            timeout=TIMEOUTS["long"]
        )
        download_time = time.time() - download_start
        
        self.assertEqual(download_response.status_code, 200)
        download_data = download_response.json()
        self.assertTrue(download_data.get("success"))
        
        # Verify integrity
        downloaded_content = base64.b64decode(download_data.get("content", "")).decode()
        downloaded_md5 = hashlib.md5(downloaded_content.encode()).hexdigest()
        
        self.assertEqual(content_md5, downloaded_md5)
        print(f"   ✅ Large file download: {download_time:.2f}s")
        print(f"   ✅ Integrity verified (MD5 match)")
        
        # Clean up
        cleanup_cmd = f"rm -f {remote_file}"
        self._execute_ssh_command(self.session_id, cleanup_cmd)
        print(f"   🧹 Large file cleaned up")
    
    def test_07_ssh_multiple_sessions(self):
        """Test: Multiple SSH session management."""
        print("\n🔀 Test: Multiple SSH sessions")
        
        session_ids = [f"{self.session_prefix}_multi_{i}" for i in range(3)]
        
        # Start multiple sessions
        for i, session_id in enumerate(session_ids):
            response = self._start_ssh_session(session_id)
            self.assertEqual(response.status_code, 200)
            print(f"   ✅ Session {i+1}/3 started: {session_id}")
        
        # Test commands on each session
        for i, session_id in enumerate(session_ids):
            test_cmd = f"echo 'Session {i+1} test'"
            cmd_response = self._execute_ssh_command(session_id, test_cmd)
            self.assertEqual(cmd_response.status_code, 200)
            
            output = cmd_response.json().get("output", "")
            self.assertIn(f"Session {i+1}", output)
            print(f"   ✅ Command session {i+1}: '{output.strip()}'")
        
        # List all sessions
        list_response = requests.get(f"{self.base_url}/api/ssh/sessions")
        if list_response.status_code == 200:
            sessions_data = list_response.json()
            active_count = len([s for s in sessions_data.get("sessions", {}).values() 
                             if s.get("is_connected")])
            self.assertGreaterEqual(active_count, 3)
            print(f"   ✅ Active sessions listed: {active_count}")
        
        # Stop all sessions
        for session_id in session_ids:
            self._stop_ssh_session(session_id)
            print(f"   🛑 Session stopped: {session_id}")
    
    def test_08_ssh_error_handling(self):
        """Test: SSH error handling."""
        print("\n⚠️  Test: SSH error handling")
        
        # Test nonexistent session
        fake_session = "fake_session_123"
        cmd_response = requests.post(
            f"{self.base_url}/api/ssh/session/{fake_session}/command",
            json={"command": "echo test"}
        )
        self.assertEqual(cmd_response.status_code, 404)
        print(f"   ✅ Nonexistent session error detected")
        
        # Test command on closed session
        response = self._start_ssh_session()
        self.assertEqual(response.status_code, 200)
        
        # Stop session
        self._stop_ssh_session(self.session_id)
        
        # Try command on closed session
        cmd_response = self._execute_ssh_command(self.session_id, "echo test")
        self.assertEqual(cmd_response.status_code, 404)
        print(f"   ✅ Closed session error detected")
        
        # Test download nonexistent file
        response = self._start_ssh_session(f"{self.session_id}_error")
        self.assertEqual(response.status_code, 200)
        
        download_response = requests.post(
            f"{self.base_url}/api/ssh/session/{self.session_id}_error/download_content",
            json={"remote_file": "/nonexistent/file.txt"}
        )
        self.assertEqual(download_response.status_code, 404)
        print(f"   ✅ Nonexistent file error detected")


def run_ssh_tests():
    """Run all SSH tests with detailed report."""
    print("\n🚀 STARTING SSH MANAGER TESTS")
    print("="*60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSSHManager)
    
    # Runner with detailed report
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    # Run tests
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Final report
    print("\n" + "="*60)
    print("📊 SSH TESTS FINAL REPORT")
    print("="*60)
    print(f"🕒 Total duration: {end_time - start_time:.2f} seconds")
    print(f"✅ Successful tests: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed tests: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    print(f"🏁 Total tests: {result.testsRun}")
    
    if result.failures:
        print(f"\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n⚠️  ERRORS:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\n🎯 Success rate: {success_rate:.1f}%")
    print("="*60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Check environment before running tests
    print("🔍 Environment verification...")
    env_checks = validate_environment()
    
    for check, status in env_checks.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {check}")
    
    if not all(env_checks.values()):
        print("\n❌ Incomplete environment. Check configuration.")
        sys.exit(1)
    
    # Run tests
    success = run_ssh_tests()
    sys.exit(0 if success else 1)
