# MCP Kali Server

A comprehensive Model Context Protocol (MCP) server for penetration testing and cybersecurity operations, providing seamless integration between Kali Linux tools and MCP-compatible clients.

## 🚀 Overview

This project provides a powerful MCP server that enables secure, programmatic access to Kali Linux penetration testing tools through a standardized interface. It includes advanced features like reverse shell management, SSH session handling, and comprehensive file operations with integrity verification.

## 🏗️ Architecture

The project is organized into two main components:

### 1. Kali Server (`kali-server/`)
The core server application that runs on Kali Linux and provides the actual penetration testing capabilities.

```
kali-server/
├── api/           # REST API routes and endpoints
├── core/          # Core functionality (SSH, reverse shells, config)
├── tools/         # Penetration testing tools integration
└── utils/         # Utility functions and file operations
```

### 2. MCP Server (`mcp-server/`)
The Model Context Protocol server that provides a standardized interface for MCP clients.

```
mcp-server/
└── mcp_server.py  # MCP protocol implementation
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
- Kali Linux (recommended) or any Linux distribution
- Python 3.8+
- Docker and Docker Compose (for testing)
- Required system tools (nmap, gobuster, etc.)

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

3. **Set up Docker for testing** (required)
   ```bash
   # Install Docker if not already installed
   sudo apt update && sudo apt install docker.io docker-compose
   
   # Start Docker service
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

4. **Start the Kali Server**
   ```bash
   cd kali-server
   python kali_server.py --host 0.0.0.0 --port 5000
   ```

5. **Start the MCP Server** (in another terminal)
   ```bash
   cd mcp-server
   python mcp_server.py
   ```

## 📖 Usage

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

### Debug Mode
Enable debug logging:
```python
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
