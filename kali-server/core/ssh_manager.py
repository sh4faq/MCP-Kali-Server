#!/usr/bin/env python3
"""SSH Session Manager for Kali Server."""

import os
import time
import subprocess
import pty
import select
import uuid
from typing import Dict, Any
from .config import logger


class SSHSessionManager:
    """Class to manage SSH sessions with interactive capabilities"""
    
    def __init__(self, target: str, username: str, password: str = "", key_file: str = "", port: int = 22, session_id: str = ""):
        self.target = target
        self.username = username
        self.password = password
        self.key_file = key_file
        self.port = port
        self.session_id = session_id
        self.process = None
        self.master_fd = None
        self.slave_fd = None
        self.is_connected = False
        self.last_output = ""
        self.start_time = time.time()
        self.command_count = 0
        
    def start_session(self) -> Dict[str, Any]:
        """Start an interactive SSH session using sshpass or key authentication"""
        try:
            logger.info(f"Starting SSH session to {self.username}@{self.target}:{self.port}")
            
            # NOTE: Skip client-side connectivity test since this runs on Kali server
            # The Kali server has VPN access to HTB targets, but the MCP client (Windows) doesn't
            # We'll rely on SSH's own connection handling and timeout mechanisms
            logger.info(f"Attempting SSH connection (server-side connectivity)")
            
            # Build SSH command
            ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
            
            if self.key_file:
                ssh_cmd.extend(["-i", self.key_file])
            
            ssh_cmd.extend(["-p", str(self.port), f"{self.username}@{self.target}"])
            
            # Allocate pseudo-terminal for interactive session
            master_fd, slave_fd = pty.openpty()
            self.master_fd = master_fd
            self.slave_fd = slave_fd
            
            if self.password and not self.key_file:
                # Use sshpass for password authentication
                full_cmd = ["sshpass", "-p", self.password] + ssh_cmd
            else:
                full_cmd = ssh_cmd
            
            # Start SSH process with PTY
            self.process = subprocess.Popen(
                full_cmd,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                preexec_fn=os.setsid
            )
            
            # Close slave FD in parent
            os.close(slave_fd)
            
            # Wait for connection establishment
            time.sleep(2)
            
            # Test if connection is ready by sending a simple command
            # Note: We need to test the connection directly via the PTY before setting is_connected
            try:
                # Try to read from the PTY to see if SSH connection is established
                ready, _, _ = select.select([master_fd], [], [], 5.0)  
                if ready:
                    # Try to read initial SSH output
                    test_data = os.read(master_fd, 1024)
                    if b"Connection refused" in test_data or b"Connection timed out" in test_data:
                        self.stop()
                        return {
                            "success": False,
                            "error": "SSH connection refused or timed out",
                            "details": test_data.decode(errors='ignore')
                        }
                
                # Now we can set connected flag and test with a command
                self.is_connected = True
                test_result = self.send_command("echo 'SSH_CONNECTION_TEST'", timeout=10)
                
                # If the command executed successfully, SSH connection is working  
                if test_result.get("success") and "SSH_CONNECTION_TEST" in test_result.get("output", ""):
                    logger.info(f"SSH session established successfully to {self.target}")
                    return {
                        "success": True,
                        "message": f"SSH session started to {self.username}@{self.target}:{self.port}",
                        "session_id": self.session_id,
                        "target": self.target,
                        "username": self.username
                    }
            except Exception as test_error:
                logger.error(f"SSH connection test failed: {str(test_error)}")
            
            # If we get here, connection failed
            self.is_connected = False
            self.stop()
            return {
                "success": False,
                "error": "SSH connection failed or not responding",
                "test_result": test_result if 'test_result' in locals() else {"error": "Connection test failed"}
            }
                
        except Exception as e:
            logger.error(f"Error starting SSH session: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Send a command to the SSH session"""
        if not self.is_connected or not self.master_fd:
            return {
                "success": False,
                "error": "No active SSH connection",
                "output": ""
            }
        
        try:
            # Log command but truncate if it's very long (like base64 payloads)
            if len(command) > 100:
                log_command = f"{command[:50]}...{command[-20:]}"
            else:
                log_command = command
            logger.info(f"Executing SSH command: {log_command}")
            self.command_count += 1
            
            # Generate unique end marker
            marker_id = str(uuid.uuid4())[:8]
            end_marker = f"SSH_END_{marker_id}"
            
            # Add debug flag for base64 commands
            is_base64_cmd = "base64" in command.lower()
            if is_base64_cmd:
                logger.info(f"Executing base64 command on {self.target}")
            
            # Send command and marker
            os.write(self.master_fd, (command + "\n").encode())
            time.sleep(0.1)
            os.write(self.master_fd, (f"echo '{end_marker}'\n").encode())
            
            # Collect output until we see the end marker
            start_time = time.time()
            output_lines = []
            buffer = b""
            
            while time.time() - start_time < timeout:
                ready, _, _ = select.select([self.master_fd], [], [], 1.0)
                if self.master_fd in ready:
                    try:
                        data = os.read(self.master_fd, 1024)
                        if not data:
                            break
                        
                        buffer += data
                        
                        # Process complete lines
                        while b"\n" in buffer:
                            line, buffer = buffer.split(b"\n", 1)
                            text = line.decode(errors='ignore').strip()
                            
                            # Check for end marker
                            if end_marker in text:
                                # Before returning, check if there's remaining data in buffer (base64 without newline)
                                if buffer.strip():
                                    remaining_text = buffer.decode(errors='ignore').strip()
                                    if remaining_text and not self._is_ssh_noise(remaining_text):
                                        output_lines.append(remaining_text)
                                
                                output = '\n'.join(output_lines)
                                if is_base64_cmd:
                                    logger.info(f"[SSH] Base64 command completed: {len(output)} chars")
                                return {
                                    "success": True,
                                    "output": output,
                                    "command": command,
                                    "session_id": self.session_id,
                                    "execution_time": time.time() - start_time
                                }
                            
                            # Skip command echo and end marker echo, but be careful with base64 commands
                            should_skip = (
                                text == command or
                                text.startswith("echo '") and end_marker in text or
                                self._is_ssh_noise(text)
                            )
                            
                            if not should_skip:
                                output_lines.append(text)
                                
                    except OSError:
                        break
                        
            # Timeout reached
            output = '\n'.join(output_lines)
            if is_base64_cmd:
                logger.info(f"[SSH] Base64 command timeout: {len(output)} chars")
            return {
                "success": True,
                "output": output,
                "command": command,
                "session_id": self.session_id,
                "execution_time": time.time() - start_time,
                "timeout": True
            }
            
        except Exception as e:
            logger.error(f"Error executing SSH command: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }
    
    def _is_ssh_noise(self, line):
        """Check if a line is SSH noise that should be filtered out"""
        # Don't filter potential base64 content (any line with base64 characters, even short ones)
        stripped = line.strip()
        if stripped and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in stripped):
            return False
        
        # Don't filter lines that look like command output (non-interactive content)
        # But do filter obvious shell prompts and login messages
        noise_patterns = [
            "Last login:",
            "Welcome to",
            "bash-",
        ]
        
        # Filter shell prompts ($ or # at end, or username@hostname patterns)
        if stripped.endswith('$') or stripped.endswith('#') or stripped == '$' or stripped == '#':
            return True
        if stripped.endswith('$ ') or stripped.endswith('# '):
            return True
        
        # Filter username@hostname patterns more specifically
        if '@' in stripped and (stripped.endswith('$') or stripped.endswith('#') or ':' in stripped):
            return True
        
        for pattern in noise_patterns:
            if pattern in line:
                return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the SSH session"""
        return {
            "session_id": self.session_id,
            "target": self.target,
            "username": self.username,
            "port": self.port,
            "is_connected": self.is_connected,
            "process_alive": self.process and self.process.poll() is None,
            "start_time": self.start_time,
            "command_count": self.command_count
        }
    
    def stop(self):
        """Stop the SSH session"""
        try:
            if self.process:
                logger.info(f"Stopping SSH session to {self.target}")
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                self.process = None
                
            if self.master_fd:
                os.close(self.master_fd)
                self.master_fd = None
                
        except Exception as e:
            logger.error(f"Error stopping SSH session: {str(e)}")
        
        self.is_connected = False
        logger.info("SSH session stopped")
