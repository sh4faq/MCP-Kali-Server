# MCP TOOLS COMPREHENSIVE TEST PLAN
# Generated: October 20, 2025
# Purpose: Full validation of all MCP tool integrations

## TEST ENVIRONMENT
- Kali Server: 192.168.216.128:5000
- Windows MCP Client: C:\Users\hamze\Desktop\MCP-Kali-Server\mcp-server\mcp_server.py
- Kali API Server: /home/kali/MCP-Kali-Server/kali-server/

## TOOLS TO TEST (28 Total)

### TIER 1: Core System Tools (10)
1. ✓ tools_nmap - Port scanning
2. ✓ tools_gobuster - Directory bruteforcing
3. ✓ tools_dirb - Web content scanner
4. ✓ tools_nikto - Web server scanner
5. ✓ tools_sqlmap - SQL injection scanner
6. ✓ tools_metasploit - Exploitation framework
7. ✓ tools_hydra - Password cracking
8. ✓ tools_john - Password hash cracking
9. ✓ tools_wpscan - WordPress scanner
10. ✓ tools_enum4linux - Windows/Samba enumeration

### TIER 2: Go Tools (8)
11. ✓ tools_subfinder - Subdomain enumeration
12. ✓ tools_httpx - HTTP probing (Project Discovery)
13. ✓ tools_nuclei - Vulnerability scanner
14. ✓ tools_arjun - Parameter discovery
15. ✓ tools_assetfinder - Asset discovery
16. ✓ tools_subzy - Subdomain takeover detection
17. ✓ tools_ffuf - Web fuzzer
18. ⚠ tools_waybackurls - Wayback Machine URL fetcher [NEWLY ADDED]

### TIER 3: Specialized Tools (2)
19. ✓ tools_bypass_403 - 403 Forbidden bypass
20. ✓ tools_searchsploit - Exploit database search

### TIER 4: Session Management (10)
21. ✓ ssh_session_start - Start SSH session
22. ✓ ssh_session_command - Execute SSH commands
23. ✓ ssh_session_status - Check SSH session status
24. ✓ ssh_session_stop - Stop SSH session
25. ✓ ssh_sessions - List all SSH sessions
26. ✓ reverse_shell_listener_start - Start reverse shell listener
27. ✓ reverse_shell_command - Execute reverse shell commands
28. ✓ reverse_shell_status - Check reverse shell status
29. ✓ reverse_shell_stop - Stop reverse shell
30. ✓ reverse_shell_sessions - List reverse shells

### TIER 5: Utility Tools (5)
31. ✓ health - Server health check
32. ✓ command - Execute arbitrary commands
33. ✓ system_network_info - Network information
34. ✓ kali_upload - Upload files to Kali
35. ✓ kali_download - Download files from Kali

## TEST METHODOLOGY

### Phase 1: Connection Tests
- [ ] Verify Kali API server is running
- [ ] Test Windows MCP client can connect
- [ ] Validate health endpoint
- [ ] Check network connectivity

### Phase 2: Simple Tool Tests (Quick validation)
Test each tool with minimal parameters to verify:
- [ ] Tool is accessible via MCP
- [ ] API endpoint responds
- [ ] Basic command execution works
- [ ] Return format is correct

### Phase 3: Complex Tool Tests (Full validation)
- [ ] Test with various parameters
- [ ] Test error handling
- [ ] Test timeout scenarios
- [ ] Verify output parsing

### Phase 4: Integration Tests
- [ ] Test tool chaining (e.g., subfinder → httpx → nuclei)
- [ ] Test file upload/download
- [ ] Test session management
- [ ] Test concurrent operations

### Phase 5: Performance Tests
- [ ] Measure response times
- [ ] Test with large outputs
- [ ] Identify slow tools
- [ ] Check for memory leaks

## TEST RESULTS TEMPLATE

Tool: [name]
Status: [PASS/FAIL/SLOW/ERROR]
Response Time: [ms]
Notes: [observations]
Reproducible Steps: [if failed]

## EXPECTED ISSUES TO WATCH FOR

1. **Tool Not Found**
   - Binary missing on Kali
   - Not in PATH
   - Wrong binary name

2. **API Endpoint Missing**
   - Route not defined in routes.py
   - Function not imported
   - MCP tool not defined in mcp_server.py

3. **Timeout Issues**
   - Tool takes too long
   - Network latency
   - Large output buffers

4. **Permission Issues**
   - Root access required
   - File permissions
   - Network restrictions

5. **Output Parsing Errors**
   - Unexpected format
   - Encoding issues
   - Binary output

## PRIORITIZATION

**Critical (must work):**
- nmap, gobuster, nikto, sqlmap, health, command

**High Priority:**
- subfinder, httpx, nuclei, ffuf, waybackurls

**Medium Priority:**
- All other reconnaissance tools

**Low Priority:**
- Session management (advanced features)

## NEXT STEPS AFTER TESTING

1. Document all failures with reproducible steps
2. Identify root causes (Kali vs Windows vs API)
3. Propose fixes for each issue
4. Re-test after fixes
5. Generate final report

---
End of Test Plan
