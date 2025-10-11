
# Installation Guide

## Example: Claude Desktop MCP Integration

To integrate the MCP Kali Server with Claude Desktop or similar clients, you can use a configuration file like the following:

```json
{
   "mcpServers": {
      "kali-mcp-server": {
         "command": "/absolute/path/to/python",
         "args": ["/absolute/path/to/mcp-server/mcp_server.py"],
         "env": {}
      }
   }
}
```

Replace `/absolute/path/to/python` with the path to your Python executable, and `/absolute/path/to/mcp-server/mcp_server.py` with the path to your MCP server script. You can add environment variables as needed in the `env` section.



## Prerequisites
- Kali Linux (required for the Kali server)
- Python 3.8+
- Docker (for test mode on Kali Linux)
- Required penetration testing tools (nmap, gobuster, etc.)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/TriV3/MCP-Kali-Server.git
   cd MCP-Kali-Server
   ```

2. **Install Python dependencies (split environments)**
   On the Kali machine (API server):
   ```bash
   pip install -r requirements.kali.txt
   ```
   On the machine hosting the MCP server (can be Kali or another OS):
   ```bash
   pip install -r requirements.mcp.txt
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
