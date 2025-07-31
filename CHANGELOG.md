# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-07-31

### Added
- **Docker Test Mode**: New `--test` command-line option for automatic Docker container management
  - Automatically starts and manages Docker test container when `--test` flag is used on Kali Linux
  - Provides isolated test environment with SSH and reverse shell capabilities
  - Automatic cleanup on server shutdown (Ctrl+C or SIGTERM)
  - Test environment includes:
    - SSH access on `localhost:2222` (testuser:testpass)
    - Reverse shell listeners on ports 4444, 4445
    - Sample test files for file transfer operations
    - Ubuntu-based container with penetration testing tools

### New Components
- `core/docker_manager.py`: Complete Docker lifecycle management (Kali Linux only)
  - Container build, start, stop, and status monitoring
  - Automatic image building with dependency management
  - Health checks and error handling
  - Performance optimization for large container operations
- `ARCHITECTURE.md`: Clear documentation of system architecture and environments

### Enhanced Configuration
- Added `TEST_MODE` configuration option
- Updated command-line argument parsing to support `--test` flag
- Enhanced signal handling for graceful Docker container cleanup

### Documentation Updates
- Updated README.md with clear architecture explanation
- Clarified that Docker test mode only works on Kali Linux
- Added ARCHITECTURE.md for environment separation
- Removed Windows-specific scripts that were inappropriate
- Updated TOOLS_SUMMARY.md with Docker test mode information

### Testing
- Enhanced Docker diagnostics for Kali Linux environment
- Simplified testing approach for appropriate environments

### Important Notes
- **Docker test mode (`--test`) only works on Kali Linux**
- The Kali server must run on Kali Linux for full functionality
- MCP server can run on any system and connects via HTTP
- All Docker-related features are designed for Linux environments only

### Files Modified
- `kali-server/kali_server.py`: Added Docker integration and test mode
- `kali-server/core/config.py`: Added TEST_MODE configuration
- `README.md`: Added comprehensive test mode documentation
- `doc/TOOLS_SUMMARY.md`: Updated with Docker test mode features

### Files Added
- `kali-server/core/docker_manager.py`: Docker management module
- `tests/docker/start_services.sh`: Container startup script
- `ARCHITECTURE.md`: Clear documentation of system architecture and environments
- `CHANGELOG.md`: This changelog file

### Files Removed
- Removed inappropriate Windows-specific scripts and diagnostics
- Simplified Docker setup by removing diagnostic scripts (Docker works correctly)

### Usage
```bash
# Start server in test mode (automatically manages Docker container)
python kali_server.py --test

# Test mode with debug logging
python kali_server.py --test --debug

# Test mode on custom port
python kali_server.py --test --port 8080
```

---

## [Previous Releases] - Initial Development

### Added
- Complete MCP server implementation with 31 tools
- SSH session management (7 tools)
- Reverse shell management (5 tools)
- File operations (6 tools)
- Enhanced Kali tools integration (12 tools)
- Comprehensive API coverage
- Advanced session management
- File integrity verification
- Performance optimizations
