# Architecture and Environments

## Overview

This MCP Kali Server project is designed to operate in separate environments:

### 🖥️ **Kali Server (kali-server/)**
- **Environment**: Kali Linux only
- **Role**: Executes pentesting tools and manages Docker
- **Features**:
  - `--test` option with automatic Docker management
  - All penetration testing tools (nmap, gobuster, etc.)
  - SSH and reverse shell sessions
  - Docker test container

### 🌐 **MCP Server (mcp-server/)**
- **Environment**: Any system (Windows, Linux, macOS)
- **Role**: MCP interface for clients
- **Communication**: Connects to Kali server via HTTP

## Typical Usage

```
┌─────────────────┐         HTTP          ┌──────────────────┐
│   MCP Client    │ ◄────────────────────► │   MCP Server     │
│  (anywhere)     │                        │  (anywhere)      │
└─────────────────┘                        └──────────────────┘
                                                      │
                                             HTTP     │
                                                      ▼
                                           ┌──────────────────┐
                                           │   Kali Server    │
                                           │  (Kali Linux)    │
                                           │                  │
                                           │ ┌──────────────┐ │
                                           │ │   Docker     │ │
                                           │ │ (test mode)  │ │
                                           │ └──────────────┘ │
                                           └──────────────────┘
```

## Startup Commands

### On Kali Linux
```bash
# In the project directory on Kali
cd kali-server
python kali_server.py --test    # With automatic Docker
# or
python kali_server.py           # Without Docker
```

### On client system (Windows/Linux/macOS)
```bash
# In the project directory
cd mcp-server
python mcp_server.py
```

## Important Notes

- **Docker**: Only managed on the Kali Linux system
- **Test Mode**: The `--test` option only works on Kali Linux
- **Diagnostic Scripts**: Should be executed on Kali Linux only
- **Docker Setup**: Configuration should be done on Kali Linux

## Troubleshooting

### If Docker doesn't work
1. Verify you are on Kali Linux
2. Check Docker installation and permissions
3. Use the integrated `--test` mode for automatic Docker management

### If connection fails
1. Verify that the Kali server is accessible from the MCP server
2. Check ports and IP address in the configuration
3. Test network connectivity between systems
