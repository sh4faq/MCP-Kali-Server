# Quick Reference: Enhanced Security Tools

## 🔧 Installed Tools

| Tool | Version | Purpose | Location |
|------|---------|---------|----------|
| **Subzy** | v1.2.0 | Subdomain takeover detection | `/home/kali/go/bin/subzy` |
| **403bypasser** | Latest | Bypass 403 Forbidden | `/usr/local/bin/403bypasser` |
| **Nuclei** | v3.4.10 | Vulnerability scanner | `/usr/bin/nuclei` |
| **HTTPx** | v1.7.1 | HTTP toolkit | `/home/kali/go/bin/httpx` |
| **Assetfinder** | Latest | Subdomain discovery | `/home/kali/go/bin/assetfinder` |
| **Waybackurls** | Latest | Historical URL finder | `/home/kali/go/bin/waybackurls` |
| **Shodan** | v1.31.0 | Device search engine | `/usr/bin/shodan` |

---

## 🚀 Quick Start Commands

### Subzy - Check subdomain takeovers
```bash
# Single domain
subzy -t example.com

# From file
subzy -t domains.txt

# HTTPS only
subzy -t example.com --https
```

### 403bypasser - Bypass access restrictions
```bash
# Single URL
python3 /usr/local/bin/403bypasser -u https://example.com/admin

# Multiple URLs from file
python3 /usr/local/bin/403bypasser -urllist urls.txt

# Specific directory
python3 /usr/local/bin/403bypasser -u https://example.com -directory /admin
```

### Nuclei - Scan for vulnerabilities
```bash
# Update templates first (ONE TIME)
nuclei -update-templates

# Scan single target
nuclei -u https://example.com -tags cve

# Scan with severity filter
nuclei -u https://example.com -severity critical,high

# Scan from list
nuclei -l targets.txt -tags misconfig,exposed-panels

# Extended timeout for slow targets
nuclei -u https://example.com -timeout 20 -rate-limit 50
```

### HTTPx - HTTP probing
```bash
# Basic probe
echo "example.com" | httpx

# With status codes and titles
echo "example.com" | httpx -status-code -title

# Full reconnaissance
cat domains.txt | httpx -status-code -title -tech-detect -follow-redirects -silent

# Fast mode (for large lists)
cat domains.txt | httpx -threads 100 -rate-limit 150 -timeout 10 -silent
```

### Assetfinder - Find subdomains
```bash
# Find subdomains
assetfinder --subs-only example.com

# Save to file
assetfinder --subs-only example.com > subdomains.txt

# Multiple domains
cat domains.txt | xargs -I {} assetfinder --subs-only {}
```

### Waybackurls - Historical URLs
```bash
# Get all archived URLs
echo "example.com" | waybackurls

# With timestamps
echo "example.com" | waybackurls -dates

# Multiple domains
cat domains.txt | waybackurls > all_urls.txt
```

### Shodan - Internet device search
```bash
# Initialize (REQUIRED FIRST TIME)
shodan init YOUR_API_KEY

# Search for devices
shodan search "apache"

# Get info about specific IP
shodan host 8.8.8.8

# Count results
shodan count "nginx"

# Your API info
shodan info
```

---

## 🔗 Chaining Tools (Workflows)

### Workflow 1: Complete Subdomain Recon
```bash
#!/bin/bash
DOMAIN="example.com"

# Step 1: Find subdomains
echo "[+] Finding subdomains..."
assetfinder --subs-only $DOMAIN > subs.txt

# Step 2: Check which are live
echo "[+] Checking live hosts..."
cat subs.txt | httpx -status-code -title -silent > live_hosts.txt

# Step 3: Check for takeovers
echo "[+] Checking for subdomain takeovers..."
subzy -t subs.txt --https > takeover_check.txt

# Step 4: Get historical URLs
echo "[+] Getting historical URLs..."
cat live_hosts.txt | awk '{print $1}' | waybackurls > historical_urls.txt

echo "[+] Recon complete! Check output files."
```

### Workflow 2: Vulnerability Assessment
```bash
#!/bin/bash
TARGET="$1"

# Step 1: HTTP probe
echo "[+] Probing target..."
echo $TARGET | httpx -status-code -title -tech-detect > probe_result.txt

# Step 2: Run Nuclei scans
echo "[+] Running vulnerability scans..."
nuclei -u $TARGET -tags cve,misconfig -severity high,critical -o nuclei_results.txt

# Step 3: Check for 403 bypasses
echo "[+] Checking for access control bypasses..."
python3 /usr/local/bin/403bypasser -u $TARGET > bypass_results.txt

echo "[+] Assessment complete!"
```

### Workflow 3: Historical Analysis
```bash
#!/bin/bash
DOMAIN="$1"

# Get all historical URLs
echo "[+] Fetching historical data..."
echo $DOMAIN | waybackurls > all_urls.txt

# Extract interesting paths
echo "[+] Filtering interesting URLs..."
cat all_urls.txt | grep -E "\.php|\.asp|\.jsp|admin|login|config" > interesting_urls.txt

# Probe which still exist
echo "[+] Checking which URLs still exist..."
cat interesting_urls.txt | httpx -status-code -silent > live_historical.txt

echo "[+] Analysis complete!"
```

---

## ⚙️ Configuration Tips

### For Large Scans
- **HTTPx**: Use `-threads 100 -rate-limit 150`
- **Nuclei**: Use `-rate-limit 100 -timeout 20`
- **Assetfinder**: Process in batches of 10-20 domains

### For Stealth
- **HTTPx**: Use `-random-agent -rate-limit 10`
- **Nuclei**: Use `-rate-limit 10 -timeout 30`
- Add delays between tool runs

### For Accuracy
- **Nuclei**: Always update templates first
- **HTTPx**: Use `-retries 2 -timeout 15`
- **Subzy**: Use `--https --verify_ssl`

---

## 📚 Additional Resources

### Documentation
- Nuclei templates: https://github.com/projectdiscovery/nuclei-templates
- ProjectDiscovery docs: https://docs.projectdiscovery.io/
- Shodan API: https://developer.shodan.io/

### Tool Repositories
- Subzy: https://github.com/PentestPad/subzy
- 403bypasser: https://github.com/yunemse48/403bypasser
- HTTPx: https://github.com/projectdiscovery/httpx
- Assetfinder: https://github.com/tomnomnom/assetfinder
- Waybackurls: https://github.com/tomnomnom/waybackurls

---

## 🆘 Troubleshooting

### Tool not found
```bash
# Check if in PATH
echo $PATH | grep go/bin

# Reload bashrc
source ~/.bashrc

# Verify installation
which <toolname>
```

### Shodan not working
```bash
# Initialize with API key
shodan init YOUR_API_KEY

# Verify
shodan info
```

### Nuclei no results
```bash
# Update templates
nuclei -update-templates

# Verify templates exist
nuclei -tl
```

### Permission denied
```bash
# For 403bypasser
sudo chmod +x /usr/local/bin/403bypasser

# For wrapper
chmod +x /home/kali/MCP-Kali-Server/enhanced_tools_wrapper.sh
```

---

**Last Updated:** October 20, 2025  
**For full audit report:** See `ENHANCED_TOOLS_AUDIT_REPORT.md`
