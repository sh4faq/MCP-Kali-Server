#!/usr/bin/env python3
"""Kali Tools module for Kali Server."""

import os
import traceback
from typing import Dict, Any
from flask import request, jsonify
from core.config import logger
from core.reverse_shell_manager import execute_command


def run_nmap(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute nmap scan with the provided parameters."""
    try:
        target = params.get("target", "")
        scan_type = params.get("scan_type", "-sCV")
        ports = params.get("ports", "")
        additional_args = params.get("additional_args", "-T4 -Pn")
        
        if not target:
            logger.warning("Nmap called without target parameter")
            return {
                "error": "Target parameter is required",
                "success": False
            }
        
        command = f"nmap {scan_type}"
        
        if ports:
            command += f" -p {ports}"
        
        if additional_args:
            command += f" {additional_args}"
        
        command += f" {target}"
        
        result = execute_command(command)
        return result
    except Exception as e:
        logger.error(f"Error in nmap: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Server error: {str(e)}",
            "success": False
        }


def run_gobuster(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute gobuster with the provided parameters."""
    try:
        url = params.get("url", "")
        mode = params.get("mode", "dir")
        wordlist = params.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        additional_args = params.get("additional_args", "")
        
        if not url:
            logger.warning("Gobuster called without URL parameter")
            return {
                "error": "URL parameter is required",
                "success": False
            }
        
        # Validate mode
        if mode not in ["dir", "dns", "fuzz", "vhost"]:
            logger.warning(f"Invalid gobuster mode: {mode}")
            return {
                "error": f"Invalid mode: {mode}. Must be one of: dir, dns, fuzz, vhost",
                "success": False
            }
        
        command = f"gobuster {mode} -u {url} -w {wordlist}"
        
        if additional_args:
            command += f" {additional_args}"
        
        result = execute_command(command)
        return result
    except Exception as e:
        logger.error(f"Error in gobuster: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Server error: {str(e)}",
            "success": False
        }


def run_dirb(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute dirb with the provided parameters."""
    try:
        url = params.get("url", "")
        wordlist = params.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        additional_args = params.get("additional_args", "")
        
        if not url:
            logger.warning("Dirb called without URL parameter")
            return {
                "error": "URL parameter is required",
                "success": False
            }
        
        command = f"dirb {url} {wordlist}"
        
        if additional_args:
            command += f" {additional_args}"
        
        result = execute_command(command)
        return result
    except Exception as e:
        logger.error(f"Error in dirb: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Server error: {str(e)}",
            "success": False
        }


def run_nikto(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute nikto with the provided parameters."""
    try:
        target = params.get("target", "")
        additional_args = params.get("additional_args", "")
        
        if not target:
            logger.warning("Nikto called without target parameter")
            return {
                "error": "Target parameter is required",
                "success": False
            }
        
        command = f"nikto -h {target}"
        
        if additional_args:
            command += f" {additional_args}"
        
        result = execute_command(command)
        return result
    except Exception as e:
        logger.error(f"Error in nikto: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Server error: {str(e)}",
            "success": False
        }


def run_sqlmap(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute sqlmap with the provided parameters."""
    try:
        url = params.get("url", "")
        data = params.get("data", "")
        additional_args = params.get("additional_args", "")
        
        if not url:
            logger.warning("SQLmap called without URL parameter")
            return {
                "error": "URL parameter is required",
                "success": False
            }
        
        command = f"sqlmap -u '{url}'"
        
        if data:
            command += f" --data '{data}'"
        
        # Add common safe arguments
        command += " --batch --threads=5 --random-agent"
        
        if additional_args:
            command += f" {additional_args}"
        
        result = execute_command(command)
        return result
    except Exception as e:
        logger.error(f"Error in sqlmap: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Server error: {str(e)}",
            "success": False
        }


def run_metasploit(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute metasploit module with the provided parameters."""
    try:
        module = params.get("module", "")
        options = params.get("options", {})
        
        if not module:
            logger.warning("Metasploit called without module parameter")
            return {
                "error": "Module parameter is required",
                "success": False
            }
        
        # Build msfconsole command
        command = f"msfconsole -x 'use {module};"
        
        # Add options
        for key, value in options.items():
            command += f" set {key} {value};"
        
        command += " run; exit'"
        
        result = execute_command(command)
        return result
    except Exception as e:
        logger.error(f"Error in metasploit: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Server error: {str(e)}",
            "success": False
        }


def run_hydra(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute hydra with the provided parameters."""
    try:
        target = params.get("target", "")
        service = params.get("service", "")
        username = params.get("username", "")
        username_file = params.get("username_file", "")
        password = params.get("password", "")
        password_file = params.get("password_file", "")
        additional_args = params.get("additional_args", "")
        
        if not target or not service:
            logger.warning("Hydra called without target or service parameter")
            return {
                "error": "Target and service parameters are required",
                "success": False
            }
        
        command = f"hydra"
        
        # Add username options
        if username:
            command += f" -l {username}"
        elif username_file:
            command += f" -L {username_file}"
        else:
            command += " -l admin"  # Default username
        
        # Add password options
        if password:
            command += f" -p {password}"
        elif password_file:
            command += f" -P {password_file}"
        else:
            command += " -P /usr/share/wordlists/rockyou.txt"  # Default wordlist
        
        if additional_args:
            command += f" {additional_args}"
        
        command += f" {target} {service}"
        
        result = execute_command(command)
        return result
    except Exception as e:
        logger.error(f"Error in hydra: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Server error: {str(e)}",
            "success": False
        }


def run_john(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute john the ripper with the provided parameters."""
    try:
        hash_file = params.get("hash_file", "")
        wordlist = params.get("wordlist", "")
        format_type = params.get("format_type", "")
        additional_args = params.get("additional_args", "")
        
        if not hash_file:
            logger.warning("John called without hash_file parameter")
            return {
                "error": "Hash file parameter is required",
                "success": False
            }
        
        command = f"john {hash_file}"
        
        if wordlist:
            command += f" --wordlist={wordlist}"
        
        if format_type:
            command += f" --format={format_type}"
        
        if additional_args:
            command += f" {additional_args}"
        
        result = execute_command(command)
        return result
    except Exception as e:
        logger.error(f"Error in john: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Server error: {str(e)}",
            "success": False
        }


def run_wpscan(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute wpscan with the provided parameters."""
    try:
        url = params.get("url", "")
        additional_args = params.get("additional_args", "")
        
        if not url:
            logger.warning("WPScan called without URL parameter")
            return {
                "error": "URL parameter is required",
                "success": False
            }
        
        command = f"wpscan --url {url}"
        
        # Add common safe arguments
        command += " --random-user-agent --disable-tls-checks"
        
        if additional_args:
            command += f" {additional_args}"
        
        result = execute_command(command)
        return result
    except Exception as e:
        logger.error(f"Error in wpscan: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Server error: {str(e)}",
            "success": False
        }


def run_enum4linux(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute enum4linux with the provided parameters."""
    try:
        target = params.get("target", "")
        additional_args = params.get("additional_args", "-a")
        
        if not target:
            logger.warning("Enum4linux called without target parameter")
            return {
                "error": "Target parameter is required",
                "success": False
            }
        
        command = f"enum4linux {additional_args} {target}"
        
        result = execute_command(command)
        return result
    except Exception as e:
        logger.error(f"Error in enum4linux: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Server error: {str(e)}",
            "success": False
        }
