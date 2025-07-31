#!/usr/bin/env python3
"""
Script to run transfer integrity tests on Kali server.
This script is designed to run inside the Docker Kali environment.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "kali-server"))

def check_environment():
    """Check if we're running in the correct environment."""
    print("🔍 Checking environment...")
    
    # Check if we can import required modules
    try:
        from utils.transfer_manager import FileTransferManager
        print("✅ FileTransferManager imported successfully")
    except ImportError as e:
        print(f"❌ Cannot import FileTransferManager: {e}")
        return False
    
    try:
        from core.ssh_manager import SSHManager
        print("✅ SSHManager imported successfully")
    except ImportError as e:
        print(f"⚠️  SSHManager import failed: {e}")
        print("   This is expected on Windows - SSH tests will be skipped")
    
    try:
        from core.reverse_shell_manager import ReverseShellManager
        print("✅ ReverseShellManager imported successfully")
    except ImportError as e:
        print(f"⚠️  ReverseShellManager import failed: {e}")
        print("   This is expected on Windows - shell tests will be skipped")
    
    return True

def run_basic_tests():
    """Run basic tests that don't require full Kali environment."""
    print("\n🧪 Running basic transfer integrity tests...")
    
    try:
        # Import the test class
        from test_transfer_integrity import TestTransferIntegrity
        
        test_instance = TestTransferIntegrity()
        test_instance.setup_method()
        
        basic_tests = [
            ("Checksum Calculations", test_instance.test_checksum_calculations),
            ("Performance Estimation", test_instance.test_performance_estimation),
            ("Performance Stats", test_instance.test_performance_stats_initialization),
            ("Transfer Optimization", test_instance.test_transfer_optimization_levels),
            ("Corruption Detection", test_instance.test_checksum_verification_with_corrupted_data),
            ("Base64 Consistency", test_instance.test_base64_encoding_consistency),
        ]
        
        passed = 0
        total = len(basic_tests)
        
        for test_name, test_func in basic_tests:
            try:
                test_func()
                print(f"✅ {test_name}: PASSED")
                passed += 1
            except Exception as e:
                print(f"❌ {test_name}: FAILED - {str(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"\n📊 Basic Tests: {passed}/{total} passed")
        return passed == total
        
    except ImportError as e:
        print(f"❌ Cannot run basic tests: {e}")
        return False

def run_integration_tests():
    """Run integration tests that require full Kali environment."""
    print("\n🔗 Running integration tests...")
    
    try:
        from test_transfer_integrity import TestTransferIntegrity
        
        test_instance = TestTransferIntegrity()
        test_instance.setup_method()
        
        integration_tests = [
            ("Direct Kali Transfer", test_instance.test_direct_kali_transfer),
        ]
        
        passed = 0
        total = len(integration_tests)
        
        for test_name, test_func in integration_tests:
            try:
                test_func()
                print(f"✅ {test_name}: PASSED")
                passed += 1
            except Exception as e:
                print(f"❌ {test_name}: FAILED - {str(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"\n📊 Integration Tests: {passed}/{total} passed")
        return passed == total
        
    except ImportError as e:
        print(f"❌ Cannot run integration tests: {e}")
        return False

def main():
    """Main test runner."""
    print("🔒 MCP Kali Server - Transfer Integrity Test Suite")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        sys.exit(1)
    
    # Run basic tests
    basic_success = run_basic_tests()
    
    # Run integration tests if basic tests pass
    integration_success = True
    if basic_success:
        integration_success = run_integration_tests()
    else:
        print("⚠️  Skipping integration tests due to basic test failures")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   Basic Tests: {'✅ PASSED' if basic_success else '❌ FAILED'}")
    print(f"   Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    
    overall_success = basic_success and integration_success
    
    if overall_success:
        print("\n🎉 All tests passed! Transfer integrity system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
    
    # Environment-specific notes
    print("\n📝 Environment Notes:")
    if os.name == 'nt':  # Windows
        print("   - Running on Windows: SSH/Shell tests may be limited")
        print("   - For full testing, run on Kali Linux environment")
    else:
        print("   - Running on Unix-like system: Full testing available")
    
    print("   - Integration tests require Kali server to be running")
    print("   - Use Docker environment for complete test coverage")
    
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main()
