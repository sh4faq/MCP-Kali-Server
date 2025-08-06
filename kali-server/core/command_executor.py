#!/usr/bin/env python3
"""Command Executor Manager for Kali Server."""

import subprocess
import threading
from typing import Dict, Any, Callable
from .config import logger, COMMAND_TIMEOUT


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
    
    def _read_stdout_with_streaming(self, on_output):
        """Thread function to continuously read stdout with streaming callback"""
        for line in iter(self.process.stdout.readline, ''):
            self.stdout_data += line
            if on_output and line.strip():
                try:
                    on_output("stdout", line.strip())
                except Exception as e:
                    logger.error(f"Error in streaming callback: {e}")
    
    def _read_stderr_with_streaming(self, on_output):
        """Thread function to continuously read stderr with streaming callback"""
        for line in iter(self.process.stderr.readline, ''):
            self.stderr_data += line
            if on_output and line.strip():
                try:
                    on_output("stderr", line.strip())
                except Exception as e:
                    logger.error(f"Error in streaming callback: {e}")
    
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

    def execute_with_streaming(self, on_output: Callable[[str, str], None]) -> Dict[str, Any]:
        """Execute the command with streaming output via callback"""
        logger.info(f"Executing command with streaming: {self.command}")
        
        try:
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Start threads to read output continuously with streaming
            self.stdout_thread = threading.Thread(target=self._read_stdout_with_streaming, args=(on_output,))
            self.stderr_thread = threading.Thread(target=self._read_stderr_with_streaming, args=(on_output,))
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
                "partial_results": self.timed_out and (self.stdout_data or self.stderr_data),
                "streaming_enabled": True
            }
        
        except Exception as e:
            logger.error(f"Error executing command with streaming: {str(e)}")
            return {
                "stdout": self.stdout_data,
                "stderr": f"Error executing command: {str(e)}\n{self.stderr_data}",
                "return_code": -1,
                "success": False,
                "timed_out": False,
                "partial_results": bool(self.stdout_data or self.stderr_data),
                "streaming_enabled": True
            }


def execute_command(command: str, on_output: Callable[[str, str], None] = None, timeout: int = None) -> Dict[str, Any]:
    """
    Execute a shell command with optional streaming and tool-specific behavior.
    
    Args:
        command: The command to execute
        on_output: Optional callback function for streaming output (source, line)
        timeout: Optional timeout override (uses tool-specific timeout if not provided)
        
    Returns:
        A dictionary containing the stdout, stderr, and return code
    """
    from .tool_config import is_streaming_tool, is_blocked_tool, get_tool_timeout
    
    # Parse the command to detect the tool
    command_parts = command.strip().split()
    if not command_parts:
        return {
            "success": False,
            "error": "Empty command provided",
            "stdout": "",
            "stderr": "",
            "return_code": -1
        }
    
    tool_name = command_parts[0]
    
    # Check if the tool is blocked
    if is_blocked_tool(tool_name):
        logger.warning(f"Command '{tool_name}' is not allowed. Use the appropriate manager.")
        return {
            "success": False,
            "error": f"The command '{tool_name}' is not allowed. Please use the appropriate manager (e.g., SSH Manager for ssh commands).",
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "blocked": True
        }
    
    # Get tool-specific timeout if not provided
    if timeout is None:
        timeout = get_tool_timeout(tool_name)
    
    # Check if the tool requires streaming
    requires_streaming = is_streaming_tool(tool_name)
    
    # Create executor with appropriate timeout
    executor = CommandExecutor(command, timeout=timeout)
    
    # If streaming callback is provided or tool requires streaming, enable streaming
    if on_output or requires_streaming:
        return executor.execute_with_streaming(on_output)
    else:
        return executor.execute()
