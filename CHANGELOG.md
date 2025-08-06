# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- (No changes yet)

### Changed
- (No changes yet)

### Fixed
- (No changes yet)

## [0.2.0] - 2025-08-06

### Added
- **Real-time Streaming Support**: Added streaming capabilities for long-running penetration testing tools
  - Gobuster, Dirb, and Nikto now support real-time output streaming
  - Server-Sent Events (SSE) implementation with `streaming=true` parameter
  - Thread-based execution prevents endpoint blocking
  - Queue-based output collection for thread-safe streaming
  - Comprehensive error handling and connection recovery
  - Backward compatibility maintained for existing clients
- **Enhanced Tool Functions**: Updated tool functions to accept optional `on_output` callbacks
  - `run_gobuster()`, `run_dirb()`, and `run_nikto()` now support streaming callbacks
  - Default logging callbacks provided for non-streaming usage
  - Consistent output formatting across all tools
- **Automatic Working Directory Management**: Server now automatically manages a clean working directory
  - Creates `tmp/` directory on startup if it doesn't exist in project root
  - Graceful fallback to `~/.mcp-kali-server/tmp/` if permissions denied
  - Sets working directory to prevent polluting the project repository
  - Directory is completely ignored by git for clean repository management
  - All file operations default to this directory unless absolute paths are used
- **Comprehensive Documentation**: Added extensive documentation and examples
  - `doc/STREAMING.md`: Complete streaming API documentation with client examples
  - `examples/streaming_example.py`: Interactive demonstration script with menu system
  - JavaScript and Python client implementation examples
  - Troubleshooting guide and best practices
  - Updated README with working directory and streaming information
- **Enhanced Testing**: Added comprehensive unit tests for streaming functionality
  - `tests/test_streaming.py`: Complete streaming test suite
  - Mock-based testing for callback verification
  - Command construction validation
  - Backward compatibility testing

### Changed
- **API Endpoints**: Enhanced tool endpoints to support streaming
  - Modified `/api/tools/gobuster`, `/api/tools/dirb`, and `/api/tools/nikto` endpoints
  - Added required imports (`queue`, `threading`) for streaming support
  - Consistent streaming response format across all endpoints
  - Improved error handling with appropriate HTTP status codes
- **Tool Configuration**: Refined automatic streaming behavior
  - Removed nmap from automatic streaming tools list (streams only when explicitly requested)
  - Maintains automatic streaming for directory enumeration tools (gobuster, dirb, etc.)
  - Better balance between automation and user control
- **Repository Management**: Improved git repository cleanliness
  - Updated `.gitignore` to completely ignore temporary directories
  - Automatic creation ensures directories are available when needed
  - Supports both project-local and user-home fallback locations

### Technical Improvements
- **Streaming Protocol**: Robust Server-Sent Events implementation
  - Event types: output, heartbeat, result, error, complete
  - Real-time output delivery with connection keep-alive
  - Automatic fallback to standard JSON for non-streaming requests
- **Performance Optimizations**: Memory-efficient streaming
  - No output buffering for real-time performance
  - Thread-safe queue implementation
  - Configurable timeout and heartbeat intervals
- **Error Handling**: Enhanced error recovery and user feedback
  - Permission-aware directory creation with automatic fallback
  - Comprehensive logging for debugging and monitoring
  - Graceful degradation when streaming is not available

### Security
- **Working Directory Isolation**: Enhanced security through directory management
  - Prevents accidental pollution of project files
  - Isolates operational artifacts from source code
  - Maintains clean separation between temporary and permanent files

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
