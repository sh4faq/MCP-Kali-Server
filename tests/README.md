# Docker + Pytest Tests - Simple Setup

## Quick Start

### Run all tests:
```batch
# SSH Manager tests
python -m pytest kali\test_ssh_manager.py -v

# Reverse Shell Manager tests
python -m pytest kali\test_reverse_shell_manager.py -v

# Transfer integrity tests
python -m pytest kali\test_transfer_integrity.py -v
```
### Or run step by step:

1. **Start Docker container manually (if needed)**
2. **Run tests:**
```batch
python -m pytest kali\test_ssh_manager.py -v
python -m pytest kali\test_reverse_shell_manager.py -v
python -m pytest kali\test_transfer_integrity.py -v
```

## Available Tests

### Core Tests
- `test_ssh_manager.py` - SSH connection and session management tests
- `test_reverse_shell_manager.py` - Reverse shell connection and session management tests
- `test_transfer_integrity.py` - File transfer integrity and checksum verification tests
- `test_config.py` - Configuration management tests
- `test_environment.py` - Environment setup and validation tests

### Reverse Shell Manager Tests
The reverse shell manager tests validate the complete reverse shell functionality:

#### Test Categories:
- **Listener Management**: Start/stop reverse shell listeners on different ports
- **Payload Generation**: Generate various types of reverse shell payloads (bash, python, netcat, PHP)
- **Session Management**: Handle multiple concurrent reverse shell sessions
- **Command Execution**: Test command execution through established reverse shell sessions
- **File Operations**: Upload/download files through reverse shell sessions
- **Web Triggering**: Trigger reverse shells via vulnerable web applications
- **Error Handling**: Test error scenarios and edge cases
- **Status Checking**: Verify session status and connection information

#### Usage:
```batch
# Run all reverse shell tests
python -m pytest kali\test_reverse_shell_manager.py -v

# Run specific test methods
python -m pytest kali\test_reverse_shell_manager.py::TestReverseShellManager::test_01_reverse_shell_listener_start_stop -v
python -m pytest kali\test_reverse_shell_manager.py::TestReverseShellManager::test_02_reverse_shell_payload_generation -v
```

### Transfer Integrity Tests
The transfer integrity tests validate the new checksum verification system:

#### Basic Tests (can run anywhere):
- Checksum calculation consistency
- Performance estimation accuracy
- Transfer optimization logic
- Corruption detection
- Base64 encoding/decoding integrity

#### Integration Tests (require Kali environment):
- Direct Kali server file transfers with verification
- SSH-based transfers with checksum validation
- Reverse shell transfers with integrity checks

#### Running Transfer Tests:

**On Windows (limited tests):**
```batch
cd kali
python run_integrity_tests.py
```

**On Kali/Linux (full tests):**
```bash
cd kali
python3 run_integrity_tests.py
# Or with pytest:
python3 -m pytest test_transfer_integrity.py -v
python3 -m pytest test_transfer_integrity.py -m integration -v
```

## Environment Requirements

### For Basic Tests:
- Python 3.8+
- No external dependencies

### For Full Integration Tests:
- Kali Linux environment (or Docker)
- Running Kali server instance
- SSH server availability
- Network connectivity

## What it does

- Starts Ubuntu container with SSH server
- Maps port 2222 → 22 (SSH)
- Creates test users: `testuser:testpass` and `root:rootpass`
- Runs comprehensive test suite with pytest
- Validates file transfer integrity across all methods
- Cleans up automatically

## Files

- `run_all.bat` - Complete automation (start Docker + run tests + cleanup)
- `docker/start.bat` - Just start Docker container
- `docker/Dockerfile` - Container configuration
- `kali/test_ssh_manager.py` - SSH tests
- `kali/test_transfer_integrity.py` - Transfer integrity tests
- `kali/run_integrity_tests.py` - Standalone integrity test runner
- `kali/test_config.py` - Configuration tests
- `kali/test_environment.py` - Environment tests

## Notes

- Transfer integrity tests are designed for the Kali server environment
- Windows users can run basic checksum and logic tests
- Full integration testing requires Docker or Kali Linux
- All transfer methods (SSH, reverse shell, direct) are tested for integrity

That's it. Simple and clean.
