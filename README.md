# MCP Kali Server

A comprehensive Model Context Protocol (MCP) server for penetration testing and cybersecurity operations, providing seamless integration between Kali Linux tools and MCP-compatible clients.

## 🚀 Overview

This project provides a powerful MCP server that enables secure, programmatic access to Kali Linux penetration testing tools through a standardized interface. It includes advanced features like reverse shell management, SSH session handling, and comprehensive file operations with integrity verification.

## 🏗️ Architecture

This project is designed to work across different environments:

### 1. Kali Server (`kali-server/`)
**Runs on Kali Linux only** - The core server application that provides the actual penetration testing capabilities.

```
kali-server/
├── api/           # REST API routes and endpoints
├── core/          # Core functionality (SSH, reverse shells, config, Docker)
├── tools/         # Penetration testing tools integration
└── utils/         # Utility functions and file operations
```

**Features:**
- Docker test mode (`--test` option) - automatically manages test containers
- All penetration testing tools (nmap, gobuster, etc.)
- SSH and reverse shell session management
- File operations with integrity verification

### 2. MCP Server (`mcp-server/`)
**Can run on any system** - The Model Context Protocol server that provides a standardized interface for MCP clients.

```
mcp-server/
└── mcp_server.py  # MCP protocol implementation
```

**Note:** The MCP server communicates with the Kali server via HTTP, so they can be on different systems.

### Deployment Architecture

```
┌─────────────────┐    HTTP     ┌──────────────────┐    HTTP     ┌──────────────────┐
│   MCP Client    │ ◄─────────► │   MCP Server     │ ◄─────────► │   Kali Server    │
│  (Any system)   │             │  (Any system)    │             │  (Kali Linux)    │
└─────────────────┘             └──────────────────┘             │                  │
                                                                  │ ┌──────────────┐ │
                                                                  │ │   Docker     │ │
                                                                  │ │ (test mode)  │ │
                                                                  │ └──────────────┘ │
                                                                  └──────────────────┘
```

## ✨ Key Features

### 🔧 Penetration Testing Tools
- **Nmap**: Network discovery and security auditing
- **Gobuster**: Directory/file enumeration
- **Dirb**: Web content scanner
- **Nikto**: Web server scanner
- **Hydra**: Network logon cracker
- **SQLmap**: SQL injection testing
- **WPScan**: WordPress security scanner
- **John the Ripper**: Password cracking
- **Enum4linux**: SMB enumeration
- **Metasploit**: Exploitation framework

### 🐚 Advanced Session Management
- **SSH Session Manager**: Complete SSH session lifecycle management
  - `start_ssh_session`: Establish secure SSH connections
  - `execute_ssh_command`: Run commands in SSH sessions
  - `get_ssh_status`: Monitor SSH session status
  - `stop_ssh_session`: Cleanly terminate SSH sessions
  - `list_ssh_sessions`: View all active SSH sessions
- **Reverse Shell Manager**: Multi-session reverse shell handling
  - `start_reverse_shell_listener`: Start listening for reverse shells
  - `execute_shell_command`: Execute commands in reverse shells
  - `trigger_reverse_shell_action`: Non-blocking trigger execution for payloads
  - `get_shell_status`: Monitor reverse shell session status
  - `stop_reverse_shell`: Terminate reverse shell sessions
  - `list_reverse_shell_sessions`: View all active reverse shell sessions

### 📁 Comprehensive File Operations
- **Kali Server File Management**:
  - `upload_to_kali`: Upload files directly to Kali server
  - `download_from_kali`: Download files from Kali server
- **SSH File Transfer** (optimized for large files):
  - `ssh_upload_content`: Upload content via SSH with auto-optimization
  - `ssh_download_content`: Download content via SSH with chunking
  - `ssh_estimate_transfer_time`: Estimate transfer times and get recommendations
- **Reverse Shell File Transfer**:
  - `reverse_shell_upload_file`: Upload files via reverse shell
  - `reverse_shell_upload_content`: Upload content via reverse shell
  - `reverse_shell_download_file`: Download files via reverse shell
  - `reverse_shell_download_content`: Download content via reverse shell

### 🛠️ System Integration
- **Command Execution**: Direct command execution on Kali server
- **Health Monitoring**: Server health checks and status monitoring
- **Session Persistence**: Maintain multiple concurrent sessions

### 🔒 Security Features
- **Data Integrity**: SHA256 checksum verification for all file transfers
- **Secure Communications**: Encrypted SSH connections
- **Session Isolation**: Independent session management
- **Error Handling**: Comprehensive error detection and reporting

### 📊 Performance Optimization
- **Chunked Transfers**: Optimized for large file operations
- **Automatic Method Selection**: Smart selection based on file size
- **Background Processing**: Non-blocking operations for long-running tasks
- **Resource Management**: Efficient memory and CPU usage

## 🛠️ Installation

### Prerequisites
- Kali Linux (required for the Kali server)
- Python 3.8+
- Docker (for test mode on Kali Linux)
- Required penetration testing tools (nmap, gobuster, etc.)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/TriV3/MCP-Kali-Server.git
   cd MCP-Kali-Server
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Docker for testing** (on Kali Linux only)
   ```bash
   # Run these commands on your Kali Linux system
   sudo apt update && sudo apt install docker.io
   
   # Start Docker service
   sudo systemctl start docker
   sudo systemctl enable docker
   
   # Add user to docker group (then logout/login)
   sudo usermod -aG docker $USER
   ```

4. **Start the Kali Server** (on Kali Linux)
   ```bash
   cd kali-server
   python kali_server.py --test
   ```

5. **Start the MCP Server** (can be on any system)
   ```bash
   cd mcp-server
   python mcp_server.py
   ```

## ⚠️ Security Warning

**IMPORTANT**: Be extremely cautious when running the Kali server with `sudo` privileges:

```bash
# ⚠️ DANGEROUS - Avoid if possible
sudo python kali_server.py
```

**Why this is risky:**
- The entire server runs with root privileges
- All API endpoints and commands execute with full system access
- Any compromise of the server grants complete root access to the system
- No privilege separation or access control

**Safer alternatives:**
- Run the server as a regular user (many tools work without root)
- Use specific sudo permissions only for commands that require them
- Consider containerization or virtualization for isolation
- Implement privilege escalation only when absolutely necessary

**For production environments**: Please see `TODO.md` for planned security enhancements including granular privilege management and access controls.

## 📖 Usage

### Starting the Kali Server

The Kali server supports several command-line options:

```bash
# Basic usage
python kali_server.py

# Enable debug mode
python kali_server.py --debug

# Enable test mode (automatically manages Docker container)
python kali_server.py --test

# Custom port
python kali_server.py --port 8080

# Combined options
python kali_server.py --test --debug --port 8080
```

### Working Directory

The Kali server automatically creates and uses a `tmp/` directory as its working directory to keep the project clean:

- **Automatic Creation**: The `tmp/` directory is created automatically on startup if it doesn't exist
- **Permission Handling**: If permission is denied in the project directory, falls back to `~/.mcp-kali-server/tmp/`
- **Default Location**: All file operations (nmap output files, downloads, etc.) use this directory by default
- **Git Ignored**: The entire `tmp/` directory is ignored by git, keeping the repository clean
- **Absolute Paths**: You can still use absolute paths to save files anywhere on the system

**Directory Priority:**
1. `<project>/tmp/` (preferred)
2. `~/.mcp-kali-server/tmp/` (fallback if permissions denied)

**Examples:**
```bash
# These commands save files in the working directory:
nmap -oN scan_results.txt 192.168.1.1
wget http://example.com/file.txt

# These commands use absolute paths:
nmap -oN /home/user/scans/results.txt 192.168.1.1
```

**Benefits:**
- Keeps the git repository clean from operational artifacts
- Provides a dedicated space for scan results and temporary files
- Handles permission issues gracefully with automatic fallback
- Makes cleanup easier after testing sessions

#### Test Mode Features

When using the `--test` option, the server will:
- Automatically check if Docker is available
- Build the test Docker image if needed
- Start a test container with SSH and testing services
- Provide a test environment with:
  - SSH access on `localhost:2222` (testuser:testpass)
  - Reverse shell listeners on ports 4444, 4445
  - Sample test files for file transfer operations
- Automatically stop and clean up the Docker container when the server is shut down (Ctrl+C)

This is perfect for development, testing, and demonstration purposes without needing a separate Kali Linux environment.

### MCP Client Integration

The server provides MCP tools that can be used by any MCP-compatible client:

```python
# Example: Running an Nmap scan
result = await mcp_client.call_tool("mcp_kali_mcp_nmap_scan", {
    "target": "192.168.1.1",
    "scan_type": "-sV",
    "ports": "22,80,443"
})
```

### Direct API Usage

You can also interact directly with the Kali Server REST API:

```bash
# Start SSH session
curl -X POST http://localhost:5000/api/ssh/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "target": "192.168.1.100",
    "username": "user",
    "password": "password",
    "port": 22
  }'

# Execute command
curl -X POST http://localhost:5000/api/ssh/session/test_session/command \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la"}'
```

## 🧪 Testing

The project includes comprehensive test suites using Docker containers for isolated testing environments.

### Run All Tests
```bash
cd tests
./run_all.bat  # Windows
# or
chmod +x run_all.sh && ./run_all.sh  # Linux
```

### Docker Testing Environment
```bash
cd tests/docker
docker-compose up -d --build
python test_config_docker.py
```

### SSH Manager Tests
```bash
cd tests/kali
python -m pytest test_ssh_manager.py -v
```

### Test Configuration
Tests use Docker containers for consistent and isolated testing environments. The configuration is automatically set up in:
- `tests/kali/test_config.py` - Main test configuration (Docker-based)
- `tests/docker/test_config_docker.py` - Docker-specific test configuration

## 🔧 Configuration

### Kali Server Configuration
The server can be configured through environment variables or command-line arguments:

```python
# Default configuration
KALI_SERVER_CONFIG = {
    "host": "localhost",
    "port": 5000,
    "timeout": 30,
    "max_sessions": 10
}
```

### SSH Targets
Configure your SSH targets for testing in the configuration files:

```python
# Docker-based SSH targets (automatically configured)
SSH_TARGETS = {
    "default_target": {
        "host": "localhost",
        "port": 2222,
        "username": "testuser",
        "password": "testpass",
        "description": "Docker container for SSH tests"
    }
}
```

## 📋 Available MCP Tools

The MCP server provides the following tools:

| Tool | Description |
|------|-------------|
| `mcp_kali_mcp_nmap_scan` | Network scanning and enumeration |
| `mcp_kali_mcp_gobuster_scan` | Directory and file enumeration |
| `mcp_kali_mcp_hydra_attack` | Password brute forcing |
| `mcp_kali_mcp_start_ssh_session` | SSH session management |
| `mcp_kali_mcp_execute_ssh_command` | SSH command execution |
| `mcp_kali_mcp_ssh_upload_content` | File upload via SSH |
| `mcp_kali_mcp_ssh_download_content` | File download via SSH |
| `mcp_kali_mcp_start_reverse_shell_listener` | Reverse shell management |
| `mcp_kali_mcp_generate_reverse_shell_payload` | Payload generation |

## 🔍 File Operations

### Upload with Integrity Verification
```python
# The system automatically verifies file integrity using SHA256 checksums
upload_result = {
    "success": True,
    "source_checksum": "abc123...",
    "remote_checksum": "abc123...",
    "checksum_verified": True,
    "integrity_check": "PASSED"
}
```

### Download with Integrity Verification
```python
# All downloads include automatic integrity verification
download_result = {
    "success": True,
    "remote_checksum": "def456...",
    "local_checksum": "def456...",
    "checksum_verified": True,
    "integrity_check": "PASSED"
}
```

## 🚨 Security Considerations

- **Testing Environment**: All tests use isolated Docker containers for security
- **Network Security**: Ensure proper firewall configuration
- **Authentication**: Use strong passwords and key-based authentication
- **Session Management**: Regularly clean up unused sessions
- **File Permissions**: Set appropriate file permissions on uploaded files
- **Logging**: Monitor all activities through comprehensive logging

## 🐛 Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if server is running
   curl http://localhost:5000/health
   ```

2. **SSH Connection Failed**
   ```bash
   # Verify SSH connectivity
   ssh user@target-host
   ```

3. **Tool Not Found**
   ```bash
   # Install missing tools
   sudo apt update && sudo apt install nmap gobuster
   ```

4. **Docker Test Mode Issues**
   
   If you encounter Docker-related errors when using `--test` mode **on Kali Linux**:
   
   **Common Docker fixes on Kali Linux:**
   ```bash
   # Install Docker
   sudo apt update && sudo apt install docker.io
   
   # Start Docker service
   sudo systemctl start docker
   sudo systemctl enable docker
   
   # Add user to docker group (then logout/login)
   sudo usermod -aG docker $USER
   
   # Test Docker access
   docker --version
   docker ps
   ```
   
   **If Docker commands work manually but fail in test mode:**
   - The issue might be PATH-related in the Python environment
   - Try running with sudo: `sudo python kali_server.py --test`
   - Check Docker socket permissions: `ls -la /var/run/docker.sock`
   - Ensure you're running this on Kali Linux, not Windows

### Debug Mode
Enable debug logging:
```bash
# For the server
python kali_server.py --test --debug

# For Python logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the coding standards (English comments, proper naming)
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

### Coding Standards
- All code, variables, and functions must be in English
- All comments and documentation must be in clear English
- Follow standard naming conventions
- Add tests for new features or bug fixes
- Update README and documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Original Project**: This project is initially a fork of [MCP-Kali-Server](https://github.com/Wh0am123/MCP-Kali-Server) but has been completely rewritten and restructured
- [Kali Linux](https://www.kali.org/) for the comprehensive penetration testing platform
- [Model Context Protocol](https://modelcontextprotocol.io/) for the standardized interface
- The cybersecurity community for continuous tool development

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/TriV3/MCP-Kali-Server/issues)
- **Documentation**: [Wiki](https://github.com/TriV3/MCP-Kali-Server/wiki)

---

**⚠️ Disclaimer**: This tool is designed for authorized penetration testing and security research only. Users are responsible for complying with applicable laws and regulations.
