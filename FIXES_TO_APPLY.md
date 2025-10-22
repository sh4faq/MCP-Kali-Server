# MCP Kali Server - Comprehensive Fixes

## Issues Fixed:

### 1. Missing Tool Routes (9 tools)
- subfinder, httpx, searchsploit, nuclei, arjun, subzy, assetfinder, waybackurls, byp4xx

### 2. SSE Streaming Headers
- Changed from `text/plain` to `text/event-stream` for proper SSE support

### 3. Command Execution Safety  
- Added `execute_command_argv` function for safer execution without shell=True

### 4. Tool Path Resolution
- Added `_which_or_go` helper to find tools in PATH or ~/go/bin

## Files Modified:
1. kali-server/api/routes.py - Added 9 missing tool endpoints
2. kali-server/tools/kali_tools.py - Added path resolution helper
3. kali-server/core/command_executor.py - Added execute_command_argv

---

# Apply these fixes to your Kali VM at /home/kali/MCP-Kali-Server/
