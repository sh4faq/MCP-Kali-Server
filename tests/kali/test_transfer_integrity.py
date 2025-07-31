#!/usr/bin/env python3
"""
Test script for file transfer integrity verification.
Tests the new checksum verification system for all transfer methods.
These tests are designed to run on the Kali server with Docker environment.
"""

import unittest
import requests
import time
import base64
import binascii
import hashlib
import tempfile
import pytest
import sys
import os
from pathlib import Path

# Import unified configuration
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_config import (
    KALI_SERVER_CONFIG, SSH_TARGETS, TEST_FILES, TIMEOUTS,
    get_ssh_target, get_test_file_content, get_large_test_content,
    validate_environment
)

# Display Docker configuration (only supported option)
print("🐳 Docker configuration loaded")
print(f"   SSH target: {SSH_TARGETS['default_target']['host']}:{SSH_TARGETS['default_target']['port']}")


class TestTransferIntegrity(unittest.TestCase):
    """Test suite for transfer integrity verification using unittest."""
    
    @classmethod
    def setUpClass(cls):
        """Setup before all tests."""
        print("\n" + "="*60)
        print("🔒 TRANSFER INTEGRITY TESTS - Kali Server")
        print("="*60)
        
        # Validate environment
        env_checks = validate_environment()
        if not env_checks["kali_server"]:
            raise unittest.SkipTest("❌ Kali server not accessible")
        
        cls.base_url = KALI_SERVER_CONFIG["base_url"]
        cls.ssh_config = get_ssh_target()
        cls.session_prefix = f"test_integrity_{int(time.time())}"
        cls.active_sessions = []
        
        print(f"🎯 SSH Target: {cls.ssh_config['username']}@{cls.ssh_config['host']}:{cls.ssh_config['port']}")
        print(f"🚀 Server: {cls.base_url}")
        print("-"*60)
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests."""
        print("\n" + "-"*60)
        print("🧹 Cleaning up sessions and files...")
        
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
    
    def _start_ssh_session(self, session_id: str = None) -> requests.Response:
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
    
    def _stop_ssh_session(self, session_id: str) -> requests.Response:
        """Stop an SSH session."""
        response = requests.post(
            f"{self.base_url}/api/ssh/session/{session_id}/stop",
            timeout=TIMEOUTS["quick"]
        )
        
        if session_id in self.active_sessions:
            self.active_sessions.remove(session_id)
        
        return response
    
    def create_test_content(self, size_kb=1):
        """Create test content of specified size."""
        content = "Test file content " * (size_kb * 64)  # Approximate KB
        return content[:size_kb * 1024]  # Exact KB
    
    def calculate_sha256(self, content):
        """Calculate SHA256 hash of content."""
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    @pytest.mark.integrity
    def test_01_checksum_calculations(self):
        """Test: Checksum calculation methods."""
        print("\n🔐 Test: Checksum calculations")
        
        test_data = "Hello, World! This is a test for checksum verification."
        expected_checksum = self.calculate_sha256(test_data)
        
        # Test direct calculation
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file.flush()
            temp_filename = temp_file.name
        
        # File is now closed, safe to read and delete on Windows
        try:
            with open(temp_filename, 'r') as f:
                file_content = f.read()
            file_checksum = self.calculate_sha256(file_content)
            
            self.assertEqual(file_checksum, expected_checksum, "File checksum should match content checksum")
            print(f"   ✅ Checksum calculated: {expected_checksum[:16]}...")
        finally:
            try:
                os.unlink(temp_filename)
            except (OSError, PermissionError) as e:
                # On Windows, sometimes files are still locked, try again after a brief delay
                import time
                time.sleep(0.1)
                try:
                    os.unlink(temp_filename)
                except (OSError, PermissionError):
                    # If still can't delete, log but don't fail the test
                    print(f"   ⚠️  Warning: Could not delete temp file: {e}")
    
    @pytest.mark.integrity
    def test_02_kali_upload_with_verification(self):
        """Test: Upload to Kali server with checksum verification."""
        print("\n⬆️  Test: Kali upload with verification")
        
        # Create test content
        test_content = self.create_test_content(1)  # 1KB
        expected_checksum = self.calculate_sha256(test_content)
        
        # Prepare upload
        content_b64 = base64.b64encode(test_content.encode()).decode()
        remote_path = f"/tmp/test_upload_{int(time.time())}.txt"
        
        payload = {
            "content": content_b64,
            "remote_path": remote_path
        }
        
        try:
            # Upload file
            response = requests.post(
                f"{self.base_url}/api/kali/upload",
                json=payload,
                timeout=TIMEOUTS["medium"]
            )
            
            self.assertEqual(response.status_code, 200, "Upload should succeed")
            result = response.json()
            self.assertTrue(result.get("success"), f"Upload failed: {result.get('error')}")
            
            print(f"   ✅ File uploaded to: {remote_path}")
            
            # Now download and verify checksum
            download_response = requests.post(
                f"{self.base_url}/api/kali/download",
                json={"remote_file": remote_path},
                timeout=TIMEOUTS["medium"]
            )
            
            self.assertEqual(download_response.status_code, 200, "Download should succeed")
            download_result = download_response.json()
            self.assertTrue(download_result.get("success"), f"Download failed: {download_result.get('error')}")
            
            # Verify content
            downloaded_content = base64.b64decode(download_result.get("content")).decode()
            downloaded_checksum = self.calculate_sha256(downloaded_content)
            
            self.assertEqual(downloaded_checksum, expected_checksum, "Checksums should match")
            self.assertEqual(downloaded_content, test_content, "Content should match")
            
            print(f"   ✅ Checksum verified: {expected_checksum[:16]}... == {downloaded_checksum[:16]}...")
            
        finally:
            # Cleanup - try to remove the file using command endpoint
            try:
                requests.post(f"{self.base_url}/api/command", 
                             json={"command": f"rm -f {remote_path}"}, 
                             timeout=TIMEOUTS["quick"])
            except:
                pass
    
    @pytest.mark.integrity
    def test_03_ssh_upload_with_verification(self):
        """Test: SSH upload with checksum verification."""
        print("\n🔐 Test: SSH upload with verification")
        
        # Start SSH session
        response = self._start_ssh_session()
        self.assertEqual(response.status_code, 200, "SSH session should start")
        
        # Create test content
        test_content = self.create_test_content(1)  # 1KB
        expected_checksum = self.calculate_sha256(test_content)
        
        # Prepare upload
        content_b64 = base64.b64encode(test_content.encode()).decode()
        remote_path = f"/tmp/ssh_test_upload_{int(time.time())}.txt"
        
        payload = {
            "content": content_b64,
            "remote_file": remote_path,
            "encoding": "base64"
        }
        
        try:
            # Upload via SSH
            upload_response = requests.post(
                f"{self.base_url}/api/ssh/session/{self.session_id}/upload_content",
                json=payload,
                timeout=TIMEOUTS["medium"]
            )
            
            self.assertEqual(upload_response.status_code, 200, "SSH upload should succeed")
            upload_result = upload_response.json()
            self.assertTrue(upload_result.get("success"), f"SSH upload failed: {upload_result.get('error')}")
            
            print(f"   ✅ File uploaded via SSH to: {remote_path}")
            
            # Download via SSH and verify
            download_response = requests.post(
                f"{self.base_url}/api/ssh/session/{self.session_id}/download_content",
                json={"remote_file": remote_path},
                timeout=TIMEOUTS["medium"]
            )
            
            self.assertEqual(download_response.status_code, 200, "SSH download should succeed")
            download_result = download_response.json()
            self.assertTrue(download_result.get("success"), f"SSH download failed: {download_result.get('error')}")
            
            # Verify content
            download_content_raw = download_result.get("content", "")
            print(f"   🔍 Downloaded content length: {len(download_content_raw)} chars")
            print(f"   🔍 First 50 chars: {download_content_raw[:50]}...")
            
            try:
                downloaded_content = base64.b64decode(download_content_raw).decode()
                downloaded_checksum = self.calculate_sha256(downloaded_content)
                
                self.assertEqual(downloaded_checksum, expected_checksum, "Checksums should match")
                self.assertEqual(downloaded_content, test_content, "Content should match")
                
                print(f"   ✅ SSH checksum verified: {expected_checksum[:16]}... == {downloaded_checksum[:16]}...")
            except (UnicodeDecodeError, base64.binascii.Error) as e:
                print(f"   ❌ Content decode error: {e}")
                # Try to decode as raw content without base64
                try:
                    downloaded_content = download_content_raw
                    downloaded_checksum = self.calculate_sha256(downloaded_content)
                    
                    self.assertEqual(downloaded_checksum, expected_checksum, "Checksums should match (raw content)")
                    self.assertEqual(downloaded_content, test_content, "Content should match (raw content)")
                    
                    print(f"   ✅ SSH checksum verified (raw): {expected_checksum[:16]}... == {downloaded_checksum[:16]}...")
                except Exception as e2:
                    print(f"   ❌ Raw content verification also failed: {e2}")
                    self.fail(f"Content verification failed: base64 decode error: {e}, raw decode error: {e2}")
            
        finally:
            # Cleanup file via SSH
            try:
                cleanup_payload = {"command": f"rm -f {remote_path}", "timeout": 5}
                requests.post(f"{self.base_url}/api/ssh/session/{self.session_id}/command",
                             json=cleanup_payload, timeout=10)
            except:
                pass
    
    @pytest.mark.integrity
    def test_04_corruption_detection(self):
        """Test: Checksum detects data corruption."""
        print("\n🚨 Test: Corruption detection")
        
        original_content = "This is test content for corruption detection."
        corrupted_content = "This is TEST content for corruption detection."  # Changed case
        
        original_checksum = self.calculate_sha256(original_content)
        corrupted_checksum = self.calculate_sha256(corrupted_content)
        
        self.assertNotEqual(original_checksum, corrupted_checksum, "Checksums should differ for different content")
        
        print(f"   ✅ Original:  {original_checksum[:16]}...")
        print(f"   ✅ Corrupted: {corrupted_checksum[:16]}...")
        print("   ✅ Corruption detected successfully")
    
    @pytest.mark.integrity
    def test_05_base64_encoding_consistency(self):
        """Test: Base64 encoding/decoding maintains data integrity."""
        print("\n🔄 Test: Base64 encoding consistency")
        
        test_data = "Test data with special characters: éàüñ@#$%^&*()"
        
        # Encode to base64
        encoded = base64.b64encode(test_data.encode('utf-8')).decode('ascii')
        
        # Decode back
        decoded = base64.b64decode(encoded).decode('utf-8')
        
        self.assertEqual(decoded, test_data, "Base64 encoding/decoding should preserve data")
        
        # Checksums should match
        original_checksum = self.calculate_sha256(test_data)
        decoded_checksum = self.calculate_sha256(decoded)
        
        self.assertEqual(original_checksum, decoded_checksum, "Checksums should match after base64 round-trip")
        
        print(f"   ✅ Original checksum:  {original_checksum[:16]}...")
        print(f"   ✅ Decoded checksum:   {decoded_checksum[:16]}...")
        print("   ✅ Base64 consistency verified")
    
    @pytest.mark.integrity
    def test_06_large_file_integrity(self):
        """Test: Large file transfer integrity."""
        print("\n📦 Test: Large file integrity")
        
        # Create larger test content (10KB)
        large_content = self.create_test_content(10)  # 10KB
        expected_checksum = self.calculate_sha256(large_content)
        
        # Upload to Kali
        content_b64 = base64.b64encode(large_content.encode()).decode()
        remote_path = f"/tmp/large_test_{int(time.time())}.txt"
        
        payload = {
            "content": content_b64,
            "remote_path": remote_path
        }
        
        try:
            # Upload
            response = requests.post(
                f"{self.base_url}/api/kali/upload",
                json=payload,
                timeout=TIMEOUTS["long"]
            )
            
            self.assertEqual(response.status_code, 200, "Large file upload should succeed")
            result = response.json()
            self.assertTrue(result.get("success"), f"Large upload failed: {result.get('error')}")
            
            # Download and verify
            download_response = requests.post(
                f"{self.base_url}/api/kali/download",
                json={"remote_file": remote_path},
                timeout=TIMEOUTS["long"]
            )
            
            self.assertEqual(download_response.status_code, 200, "Large file download should succeed")
            download_result = download_response.json()
            self.assertTrue(download_result.get("success"), f"Large download failed: {download_result.get('error')}")
            
            # Verify integrity
            downloaded_content = base64.b64decode(download_result.get("content")).decode()
            downloaded_checksum = self.calculate_sha256(downloaded_content)
            
            self.assertEqual(downloaded_checksum, expected_checksum, "Large file checksums should match")
            self.assertEqual(len(downloaded_content), len(large_content), "Large file sizes should match")
            
            print(f"   ✅ Large file ({len(large_content)} bytes) integrity verified")
            print(f"   ✅ Checksum: {expected_checksum[:16]}...")
            
        finally:
            # Cleanup
            try:
                requests.post(f"{self.base_url}/api/command", 
                             json={"command": f"rm -f {remote_path}"}, 
                             timeout=TIMEOUTS["quick"])
            except:
                pass


if __name__ == "__main__":
    # Run with unittest
    unittest.main(verbosity=2)


# Standalone execution for manual testing
if __name__ == "__main__":
    print("🔒 Running File Transfer Integrity Tests")
    print("=" * 60)
    
    test_instance = TestTransferIntegrity()
    test_instance.setup_method()
    
    tests = [
        ("Checksum Calculations", test_instance.test_checksum_calculations),
        ("Performance Estimation", test_instance.test_performance_estimation), 
        ("Performance Stats", test_instance.test_performance_stats_initialization),
        ("Transfer Optimization", test_instance.test_transfer_optimization_levels),
        ("Corruption Detection", test_instance.test_checksum_verification_with_corrupted_data),
        ("Base64 Consistency", test_instance.test_base64_encoding_consistency),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name}: PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Transfer integrity system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        
    # Note about integration tests
    print("\nℹ️  Note: Integration tests require Kali server environment.")
    print("   Run with: pytest -m integration")
    
    sys.exit(0 if passed == total else 1)
