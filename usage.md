# Usage Guide

## Starting the Kali Server

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

## Working Directory

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

### Test Mode Features

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

## MCP Client Integration

The server provides MCP tools that can be used by any MCP-compatible client:

```python
# Example: Running an Nmap scan
result = await mcp_client.call_tool("mcp_kali_mcp_nmap_scan", {
    "target": "192.168.1.1",
    "scan_type": "-sV",
    "ports": "22,80,443"
})
```

## Direct API Usage

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
