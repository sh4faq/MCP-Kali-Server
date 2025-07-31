"""
Core modules for Kali Server.
Contains configuration, session managers and core functionality.
"""

from .config import API_PORT, DEBUG_MODE, COMMAND_TIMEOUT, VERSION, logger, active_sessions, active_ssh_sessions
from .ssh_manager import SSHSessionManager
from .reverse_shell_manager import ReverseShellManager, CommandExecutor, execute_command

__all__ = [
    'API_PORT', 'DEBUG_MODE', 'COMMAND_TIMEOUT', 'VERSION', 'logger', 
    'active_sessions', 'active_ssh_sessions',
    'SSHSessionManager', 'ReverseShellManager', 'CommandExecutor', 'execute_command'
]
