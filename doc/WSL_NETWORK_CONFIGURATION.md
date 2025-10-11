# WSL Network Configuration for Kali Linux Server

This guide explains how to configure WSL networking to allow your host OS to communicate with the Kali Linux MCP server running in WSL.

## Prerequisites

- WSL 2 with Kali Linux installed
- Administrator privileges on Windows

## Configuration Steps

### 1. Configure wsl.conf

Create or edit `/etc/wsl.conf` in your Kali Linux WSL instance:

```bash
sudo nano /etc/wsl.conf
```

Add the following configuration:

```ini
[automount]
enabled = true
root = /
options = "metadata,uid=1000,gid=1000,umask=0022,fmask=11,case=off"
mountFsTab = false
crossDistribution = true

[filesystem]
umask = 0022

[network]
generateHosts = true
generateResolvConf = false

[user]
default = kali_user

[boot]
systemd=true

[interop]
appendWindowsPath = false
```

**Detailed Explanation:**

**[automount] section:**
- `enabled = true`: Enables automatic mounting of Windows drives (default: true)
- `root = /`: Sets the mount point for Windows drives to root instead of `/mnt` (e.g., `/c/` instead of `/mnt/c/`)
- `options`: Mount options for Windows drives:
  - `metadata`: Enables Linux file metadata (permissions, ownership) on Windows drives
  - `uid=1000,gid=1000`: Sets default user/group ownership for mounted files
  - `umask=0022`: Default permissions for new files (755 for directories, 644 for files)
  - `fmask=11`: Specific file permissions mask
  - `case=off`: Disables case sensitivity (Windows default behavior)
- `mountFsTab = false`: Prevents automatic mounting of entries in `/etc/fstab` (default: false)
- `crossDistribution = true`: Allows sharing mounts across different WSL distributions (default: false)

**[filesystem] section:**
- `umask = 0022`: Sets default file creation permissions within WSL filesystem (default: 0022)

**[network] section:**
- `generateHosts = true`: Allows WSL to generate `/etc/hosts` file automatically (default: true)
- `generateResolvConf = false`: **CRITICAL** - Prevents WSL from overwriting `/etc/resolv.conf`, required for proper DNS configuration and tool functionality

**[user] section:**
- `default = kali_user`: Sets the default user when starting WSL (adjust to your username)

**[boot] section:**
- `systemd=true`: Enables systemd init system for proper service management (required for many services)

**[interop] section:**
- `appendWindowsPath = false`: Prevents Windows PATH from being added to WSL PATH
  - **Pros**: Cleaner environment, avoids conflicts between Windows and Linux binaries
  - **Cons**: Cannot directly run Windows executables (e.g., `notepad.exe`, `explorer.exe`) from WSL
  - **Note**: Set to `true` if you need to call Windows applications from WSL

### 2. Configure DNS Resolution

To ensure all Kali Linux tools (especially GUI tools) work properly, configure DNS to use the Windows host:

```bash
# Remove existing resolv.conf if it's a symlink
sudo rm /etc/resolv.conf

# Get Windows host IP and configure DNS
WINDOWS_IP=$(ip route show | grep -i default | awk '{ print $3}')
echo "nameserver $WINDOWS_IP" | sudo tee /etc/resolv.conf
```

**Why this configuration?**
This configuration is essential for proper functioning of all Kali Linux tools, particularly GUI-based tools and network utilities. Using the Windows host as DNS ensures proper name resolution within the WSL environment.

### 3. Create DNS Update Script (Optional but Recommended)

Create a script to automatically update DNS configuration on WSL startup:

```bash
sudo nano /usr/local/bin/update-dns.sh
```

Add the following content:

```bash
#!/bin/bash

# Get Windows host IP
WINDOWS_IP=$(ip route show | grep -i default | awk '{ print $3}')

# Update resolv.conf
echo "nameserver $WINDOWS_IP" | tee /etc/resolv.conf > /dev/null

echo "DNS updated to use Windows host: $WINDOWS_IP"
```

Make it executable:

```bash
sudo chmod +x /usr/local/bin/update-dns.sh
```

Add to your shell profile (e.g., `~/.bashrc` or `~/.zshrc`):

```bash
# Auto-update DNS on shell start
if [ -f /usr/local/bin/update-dns.sh ]; then
    sudo /usr/local/bin/update-dns.sh
fi
```

Or configure it to run at boot by adding to `/etc/wsl.conf`:

```ini
[boot]
command = /usr/local/bin/update-dns.sh
```

### 4. Restart WSL

In PowerShell (as Administrator):

```powershell
wsl --shutdown
```

Then restart your Kali instance.

### 5. Verify DNS Configuration

Test DNS resolution:

```bash
# Check resolv.conf content
cat /etc/resolv.conf

# Test DNS resolution
nslookup google.com
ping -c 3 google.com
```

## Testing Network Communication

After configuration, it's essential to verify that bidirectional communication works between Windows and Kali Linux.

### Understanding WSL 2 Network Behavior (READ THIS FIRST)

**WSL 2 has asymmetric localhost forwarding:**
- ✅ **Windows → Kali**: Use `localhost` (Windows automatically forwards to WSL)
- ❌ **Kali → Windows**: Use Windows host IP via `ip route show | grep -i default | awk '{ print $3}'` (NOT localhost)

This is **normal and expected** WSL 2 behavior.

### Test 1: Windows → Kali Communication (⚠️ CRITICAL for MCP)

**This test verifies that Windows can access services running in Kali via `localhost`. This is MANDATORY for the MCP server to function.**

**In Kali Linux (WSL):**

```bash
# Start a simple HTTP server
python3 -m http.server 9000
```

**In Windows (PowerShell or Browser):**

```powershell
# Test via localhost (should work with WSL 2)
curl http://localhost:9000

# Or with Invoke-WebRequest
Invoke-WebRequest -Uri "http://localhost:9000" -UseBasicParsing

# Or open in browser
start http://localhost:9000
```

**Expected result:** ✅ You should see the directory listing. This confirms Windows can access Kali services via `localhost`.

**If this test fails:** 🚨 STOP - The MCP server cannot function. See troubleshooting section below.

---

### Test 2: Kali → Windows Communication (Required for Callbacks)

**In Windows (PowerShell):**

```powershell
# Start a simple HTTP server (must bind to all interfaces, not just localhost)
python -m http.server 9001

# Or using PowerShell native
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://+:9001/")  # Important: + binds to all interfaces
$listener.Start()
Write-Host "Listening on http://0.0.0.0:9001"
Write-Host "Press Ctrl+C to stop"
while ($listener.IsListening) {
    $context = $listener.GetContext()
    $response = $context.Response
    $buffer = [System.Text.Encoding]::UTF8.GetBytes("Hello from Windows!")
    $response.ContentLength64 = $buffer.Length
    $response.OutputStream.Write($buffer, 0, $buffer.Length)
    $response.Close()
}
```

**In Kali Linux (WSL):**

```bash
# Get Windows host IP (this is the correct way to access Windows from Kali)
WINDOWS_IP=$(ip route show | grep -i default | awk '{ print $3}')
echo "Windows host IP: $WINDOWS_IP"

# Test with curl using Windows IP
curl http://$WINDOWS_IP:9001

# Or with wget
wget -qO- http://$WINDOWS_IP:9001
```

**Expected result:** ✅ You should receive "Hello from Windows!" This confirms Kali can access Windows services using the Windows host IP.

**⚠️ Important:** `localhost` will NOT work from Kali to Windows. You MUST use `$WINDOWS_IP`.

---

### Test 3: Complete MCP Server Verification

**In Kali Linux:**

```bash
# Navigate to your MCP server directory
cd /path/to/MCP-Kali-Server

# Start the MCP server (adjust port if needed)
python3 mcp-server/mcp_server.py

# Or if using the Kali API server
python3 kali-server/kali_server.py
```

**In Windows (PowerShell):**

```powershell
# Access the Kali MCP server via localhost (this is the correct method)
Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing

# Test with curl
curl http://localhost:3000/health

# Open in browser
start http://localhost:3000
```

**In Kali Linux (verify server is accessible from within WSL too):**

```bash
# Test from within Kali (localhost works within same system)
curl http://localhost:5000/health

# Test with the WSL IP (also works)
WSL_IP=$(hostname -I | awk '{print $1}')
curl http://$WSL_IP:5000/health
```

**Expected results:**
- ✅ `http://localhost:5000` should work from Windows (THIS IS CRITICAL)
- ✅ `http://$WSL_IP:5000` should work from Kali (accessing its own server)

---

### Summary of Network Communication Rules

**From Windows to Kali:**
```powershell
# Always use localhost
curl http://localhost:3000
```

**From Kali to Windows:**
```bash
# Always use Windows host IP
WINDOWS_IP=$(ip route show | grep -i default | awk '{ print $3}')
curl http://$WINDOWS_IP:8080
```

**From Kali to Kali:**
```bash
# Use localhost
curl http://localhost:3000
```

**Critical Requirements for MCP:**
- 🔴 Test 1 (Windows → Kali via localhost) MUST pass - This is mandatory
- ✅ Test 2 (Kali → Windows via host IP) should pass if Kali needs to callback to Windows
- 🚫 Do NOT proceed if Test 1 fails

---

## Troubleshooting Network Tests

### Problem: Windows → Kali (localhost) doesn't work

🚨 **CRITICAL BLOCKER** - This will prevent the entire MCP system from functioning.

1. Verify you're using WSL 2 (not WSL 1):
```powershell
# In PowerShell
wsl -l -v
# Should show "VERSION 2" for your Kali distribution
```

2. If using WSL 1, upgrade to WSL 2:
```powershell
wsl --set-version kali-linux 2
```

3. Check if the Kali server is binding correctly:
```bash
# In Kali - server should bind to 0.0.0.0 or :: (all interfaces)
sudo netstat -tulpn | grep 5000
# Should show 0.0.0.0:<port> or :::<port>, not 127.0.0.1:<port>
```

4. Restart WSL completely:
```powershell
wsl --shutdown
# Wait a few seconds, then restart Kali
wsl
```

---

### Problem: Kali → Windows (using Windows host IP) doesn't work

This is needed if your Kali tools need to callback to Windows services.

1. Verify Windows server is binding to all interfaces (not just localhost):
```powershell
# In PowerShell - check listening ports
netstat -an | findstr :<port>
# Should show 0.0.0.0:<port> or [::]:<port>, not 127.0.0.1:<port>
```

2. Get Windows host IP and verify connectivity:
```bash
# In Kali
WINDOWS_IP=$(ip route show | grep -i default | awk '{ print $3}')
echo "Windows IP: $WINDOWS_IP"

# Test TCP connectivity (this should work)
curl http://$WINDOWS_IP:9001

# Test ICMP (ping may fail - this is normal)
ping -c 4 $WINDOWS_IP
# ⚠️ If ping fails but curl works, this is NORMAL - Windows Firewall blocks ICMP by default
```

1. Check Windows Firewall:
```powershell
# Temporarily disable to test (run as Administrator)
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
# Test connection from Kali
# Re-enable firewall
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

# If it works, add proper firewall rule:
New-NetFirewallRule -DisplayName "WSL Kali Access" -Direction Inbound -Protocol TCP -LocalPort <port> -Action Allow
```

---

### Important Notes

**Localhost Asymmetry (This is Normal):**
- ✅ Windows → Kali via `localhost` works by default in WSL 2
- ❌ Kali → Windows via `localhost` does NOT work - always use Windows host IP
- 💡 This is expected WSL 2 behavior, not a bug

**If ping doesn't work but HTTP does:**
- This is normal - ICMP may be blocked by Windows Firewall
- Focus on TCP connectivity tests (curl, wget, etc.)

## Accessing the MCP Server from Windows

**⚠️ PREREQUISITE**: Before using any of these methods, ensure Test 5 (Localhost Communication) has passed successfully. Without bidirectional localhost access, the MCP system cannot function.

### Method 1: Using Localhost (Recommended - Required for MCP)

**This is the primary method for MCP operation.**

Once the Kali server is running, connect from Windows using:

```
http://localhost:3000
```

**Why localhost is mandatory:**
- The MCP client on Windows expects to connect via `localhost`
- This eliminates IP address changes after WSL restarts
- This is how the MCP architecture is designed to work

### Method 2: Using Direct IP (Alternative for Testing)

Find your WSL IP address in Kali Linux:

```bash
ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1
```

Connect from Windows using the WSL IP:
```
http://<WSL_IP>:3000
```

**Note:** This method works but is not recommended for production use as the IP changes on WSL restart.

### Method 3: Port Forwarding (For Complex Network Scenarios)

If the WSL IP changes frequently, use Windows port forwarding for a stable connection.

In PowerShell (as Administrator):

```powershell
# Get WSL IP
$WSL_IP = wsl hostname -I

# Add port forwarding rule
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$WSL_IP
```

Then connect to `http://localhost:3000` from Windows.

To remove the rule later:

```powershell
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0
```

To view all forwarding rules:

```powershell
netsh interface portproxy show all
```

## Firewall Configuration

Ensure Windows Firewall allows the connection:

```powershell
# In PowerShell as Administrator
New-NetFirewallRule -DisplayName "WSL MCP Server" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
```

## Server Configuration

Ensure your MCP server binds to `0.0.0.0` (all interfaces) instead of `127.0.0.1` (localhost only) to be accessible from Windows:

```python
# In your server configuration
app.run(host='0.0.0.0', port=3000)
```

## Troubleshooting

### DNS Resolution Issues

```bash
# Verify resolv.conf is correctly configured
cat /etc/resolv.conf

# Should show: nameserver <Windows_Host_IP>

# Test DNS resolution
nslookup google.com
dig google.com

# If failing, manually update DNS
WINDOWS_IP=$(ip route show | grep -i default | awk '{ print $3}')
echo "nameserver $WINDOWS_IP" | sudo tee /etc/resolv.conf
```

### Cannot Connect from Windows

```bash
# Verify server is running and listening
sudo netstat -tulpn | grep 3000

# Check if binding to 0.0.0.0 (not 127.0.0.1)
sudo ss -tlnp | grep 3000
```

### Port Already in Use

```bash
# Find process using port 3000
sudo lsof -i :3000

# Kill the process if needed
sudo kill -9 <PID>
```

### WSL IP Changes After Restart

This is normal behavior. Solutions:
1. Use the port forwarding method (Method 2) for a stable `localhost` connection
2. Create a script to automatically update port forwarding on WSL start
3. Use a dynamic DNS update script

### GUI Tools Not Working Properly

If Kali Linux GUI tools still don't work properly after DNS configuration:

```bash
# Verify X11 forwarding (if using GUI tools)
echo $DISPLAY

# Install X server on Windows (e.g., VcXsrv, X410, or WSLg)

# Test with a simple GUI tool
xcalc
```

## Additional Network Optimization

For better network performance in WSL:

### Disable IPv6 (if causing issues)

```bash
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
```

Make permanent by adding to `/etc/sysctl.conf`:

```bash
echo "net.ipv6.conf.all.disable_ipv6 = 1" | sudo tee -a /etc/sysctl.conf
echo "net.ipv6.conf.default.disable_ipv6 = 1" | sudo tee -a /etc/sysctl.conf
```

### Increase Network Buffer Sizes

```bash
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.wmem_max=134217728
```

## References

- [WSL Configuration Documentation](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)
- [WSL Networking Documentation](https://learn.microsoft.com/en-us/windows/wsl/networking)
- [Kali Linux in WSL](https://www.kali.org/docs/wsl/wsl-preparations/)

## Summary

Key configuration files:

1. `/etc/wsl.conf` - WSL configuration
2. `/etc/resolv.conf` - DNS configuration (must use Windows host IP)
3. `/usr/local/bin/update-dns.sh` - DNS auto-update script (optional)

Essential commands:

```bash
# Update DNS
WINDOWS_IP=$(ip route show | grep -i default | awk '{ print $3}')
echo "nameserver $WINDOWS_IP" | sudo tee /etc/resolv.conf

# Get WSL IP
ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1

# Restart WSL (from PowerShell)
wsl --shutdown
```
