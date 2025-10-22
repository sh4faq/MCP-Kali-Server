# MCP-Kali-Master
*The Ultimate Guide to Building AI-Powered Security Automation with Kali Linux*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)](https://www.python.org/)
[![Kali Linux](https://img.shields.io/badge/Kali-Linux-red.svg)](https://www.kali.org/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-green.svg)](https://github.com/anthropics/mcp)

## 🌟 What This Repository Contains

This repository is the result of an intensive debugging and optimization session that transformed a broken MCP-Kali-Server into a production-ready security automation platform. It contains:

- **Complete working implementation** of MCP-Kali-Server with 18+ security tools
- **Battle-tested debugging scripts** that saved hours of troubleshooting
- **Security hardening configurations** for production deployment
- **Performance monitoring systems** with real-time metrics
- **Automated backup and recovery tools**
- **Comprehensive documentation** of architecture and lessons learned

## 📚 Repository Structure

```
MCP-Kali-Master/
├── README.md                   # This file
├── ARTICLE.md                  # Complete implementation guide
├── LICENSE                     # MIT License
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
│
├── kali-server/               # Kali Linux server components
│   ├── kali_server.py         # Main Flask application
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # API route definitions
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration settings
│   │   ├── command_executor.py # Command execution logic
│   │   └── security_config.py  # Security hardening
│   ├── tools/
│   │   ├── __init__.py
│   │   └── kali_tools.py      # Tool implementations
│   └── utils/
│       ├── __init__.py
│       └── monitoring.py       # Monitoring system
│
├── mcp-server/                # Windows MCP client
│   └── mcp_server.py          # MCP protocol interface
│
├── scripts/                   # Management scripts
│   ├── verify-mcp-tool.sh    # Tool verification script
│   ├── debug-mcp.sh          # Debugging toolkit
│   ├── mcp-backup-manager.sh # Backup management
│   ├── sync-mcp-to-windows.sh # Sync helper
│   └── setup.sh              # Initial setup script
│
├── configs/                   # Configuration templates
│   ├── nginx.conf            # Reverse proxy config
│   ├── systemd.service       # Systemd service file
│   └── firewall.rules        # UFW firewall rules
│
├── docs/                      # Additional documentation
│   ├── ARCHITECTURE.md       # System architecture
│   ├── SECURITY.md          # Security guide
│   ├── PERFORMANCE.md       # Performance tuning
│   └── TROUBLESHOOTING.md   # Common issues
│
└── tests/                    # Test suites
    ├── test_tools.py         # Tool function tests
    ├── test_api.py          # API endpoint tests
    └── test_security.py     # Security tests
```

## 🚀 Quick Start

### Prerequisites

- **Kali Linux** (2023.3 or later) - Physical or VM
- **Python 3.8+** on both Kali and Windows
- **Network connectivity** between Windows and Kali
- **Claude Desktop** or compatible MCP client

### Installation

1. **Clone on Kali Linux:**
```bash
cd /home/kali
git clone https://github.com/yourusername/MCP-Kali-Master.git
cd MCP-Kali-Master
```

2. **Run the setup script:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

3. **Configure your IP address:**
```bash
# Edit kali-server/core/config.py
nano kali-server/core/config.py
# Set your Kali IP address
```

4. **Start the Kali server:**
```bash
source env/bin/activate
python kali-server/kali_server.py
```

5. **On Windows, clone and configure:**
```powershell
git clone https://github.com/yourusername/MCP-Kali-Master.git
cd MCP-Kali-Master
# Edit mcp-server/mcp_server.py with your Kali IP
python mcp-server/mcp_server.py
```

## 🛠️ Available Tools

The server currently supports these Kali Linux tools:

| Tool | Purpose | Status |
|------|---------|--------|
| **nmap** | Network discovery and security auditing | ✅ Tested |
| **gobuster** | Directory/file brute-forcer | ✅ Tested |
| **dirb** | Web content scanner | ✅ Tested |
| **nikto** | Web server scanner | ✅ Tested |
| **sqlmap** | SQL injection tool | ✅ Tested |
| **metasploit** | Penetration testing framework | ✅ Tested |
| **hydra** | Password cracking tool | ✅ Tested |
| **john** | Password cracker | ✅ Tested |
| **wpscan** | WordPress vulnerability scanner | ✅ Tested |
| **enum4linux** | SMB enumeration | ✅ Tested |
| **fierce** | DNS enumeration | ✅ Tested |
| **httpx** | HTTP toolkit | ✅ Tested |
| **subfinder** | Subdomain discovery | ✅ Tested |
| **nuclei** | Vulnerability scanner | ✅ Tested |
| **searchsploit** | Exploit database search | ✅ Tested |
| **arjun** | HTTP parameter discovery | ✅ Tested |
| **subzy** | Subdomain takeover detection | ✅ Tested |
| **assetfinder** | Asset discovery | ✅ Tested |

## 🔍 Key Scripts Explained

### verify-mcp-tool.sh
Verifies that a tool is properly configured across all system layers. This script checks:
- System binary installation
- Python function implementation
- API route registration
- Import statements

**Usage:** `./scripts/verify-mcp-tool.sh httpx`

### debug-mcp.sh
Comprehensive debugging toolkit that systematically tests each component:
- Network connectivity
- API endpoints
- Tool execution
- Error logs

**Usage:** `./scripts/debug-mcp.sh full httpx`

### mcp-backup-manager.sh
Automated backup and recovery system:
- Creates timestamped backups
- Maintains backup rotation
- Enables quick restoration

**Usage:** `./scripts/mcp-backup-manager.sh backup`

## 🔒 Security Features

This implementation includes multiple security layers:

1. **IP Whitelisting** - Only authorized IPs can connect
2. **Rate Limiting** - Prevents API abuse
3. **Input Sanitization** - Prevents command injection
4. **Audit Logging** - Complete activity tracking
5. **Least Privilege** - Minimal permissions for operations

See [docs/SECURITY.md](docs/SECURITY.md) for detailed security configuration.

## 📊 Monitoring & Performance

Built-in monitoring tracks:
- System resources (CPU, memory, disk, network)
- Tool execution metrics
- API request patterns
- Error rates and types

Access monitoring dashboard:
```bash
curl http://localhost:5000/api/monitoring/dashboard
```

## 🐛 Troubleshooting

### Common Issues and Solutions

**Tool not found by Claude:**
```bash
./scripts/verify-mcp-tool.sh <tool_name>
./scripts/debug-mcp.sh tool <tool_name>
```

**API connection refused:**
```bash
# Check if server is running
sudo netstat -tlnp | grep 5000
# Check firewall rules
sudo ufw status
```

**Tool execution timeout:**
Edit timeout in `kali_tools.py`:
```python
result = execute_command(command, timeout=600)  # 10 minutes
```

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for comprehensive troubleshooting guide.

## 📖 The Story Behind This Repository

This repository emerged from an intensive debugging session where we transformed a partially broken MCP-Kali-Server into a production-ready system. The journey involved:

1. **Discovering architectural misunderstandings** - The fierce tool was added to the wrong file
2. **Understanding the complete data flow** - From Claude through MCP to Linux commands
3. **Building debugging tools** - Scripts that now save hours of troubleshooting
4. **Implementing security hardening** - Multiple layers of protection
5. **Creating monitoring systems** - Visibility into system behavior
6. **Establishing best practices** - Patterns that ensure maintainability

Read the full story in [ARTICLE.md](ARTICLE.md).

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/NewTool`)
3. Follow the existing code patterns
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

### Adding a New Tool

To add a new tool, follow the workflow in [ARTICLE.md#adding-tools](ARTICLE.md#adding-tools):

1. Implement in `kali-server/tools/kali_tools.py`
2. Register route in `kali-server/api/routes.py`
3. Define interface in `mcp-server/mcp_server.py`
4. Verify with `./scripts/verify-mcp-tool.sh <tool>`

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for **authorized security testing only**. Users must:
- Have explicit permission to test target systems
- Comply with all applicable laws and regulations
- Use responsibly and ethically

The authors assume no liability for misuse or damage caused by this software.

## 🙏 Acknowledgments

- **Claude (Anthropic)** - For the AI assistance that makes this possible
- **Kali Linux Team** - For the amazing security tools
- **MCP Protocol** - For enabling AI-tool integration
- **The Security Community** - For continuous learning and sharing

## 📬 Contact

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and community support
- **Security Issues**: Please report privately to [security contact]

## 🌟 Star History

If this repository helped you, please consider giving it a star ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/MCP-Kali-Master&type=Date)](https://star-history.com/#yourusername/MCP-Kali-Master&Date)

---

**Remember:** *With great power comes great responsibility. Use these tools ethically and legally.*