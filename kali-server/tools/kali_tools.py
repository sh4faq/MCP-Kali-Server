#!/usr/bin/env python3
"""Kali Tools module for Kali Server."""

import os
import traceback
import tempfile
from typing import Dict, Any
from flask import request, jsonify
from core.config import logger
from core.command_executor import execute_command


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


def run_gobuster(params: Dict[str, Any], on_output=None) -> Dict[str, Any]:
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
        
        # Use provided callback or default logging callback
        output_callback = on_output
        if not output_callback:
            def handle_gobuster_output(source, line):
                logger.info(f"[GOBUSTER-{source.upper()}] {line}")
            output_callback = handle_gobuster_output
        
        # Execute with streaming support (gobuster will be detected as a streaming tool)
        result = execute_command(command, on_output=output_callback)
        return result
    except Exception as e:
        logger.error(f"Error in gobuster: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Server error: {str(e)}",
            "success": False
        }


def run_dirb(params: Dict[str, Any], on_output=None) -> Dict[str, Any]:
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
        
        # Use provided callback or default logging callback
        output_callback = on_output
        if not output_callback:
            def handle_dirb_output(source, line):
                logger.info(f"[DIRB-{source.upper()}] {line}")
            output_callback = handle_dirb_output
        
        result = execute_command(command, on_output=output_callback)
        return result
    except Exception as e:
        logger.error(f"Error in dirb: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Server error: {str(e)}",
            "success": False
        }


def run_nikto(params: Dict[str, Any], on_output=None) -> Dict[str, Any]:
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
        
        # Use provided callback or default logging callback
        output_callback = on_output
        if not output_callback:
            def handle_nikto_output(source, line):
                logger.info(f"[NIKTO-{source.upper()}] {line}")
            output_callback = handle_nikto_output
        
        result = execute_command(command, on_output=output_callback)
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


def run_subfinder(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Subfinder for subdomain enumeration."""
    target = params.get('target')
    additional_args = params.get('additional_args', '')
    
    if not target:
        return {'success': False, 'error': 'target parameter is required'}
    
    command = f"subfinder -d {target} -silent"
    if additional_args:
        command += f" {additional_args}"
    
    return execute_command(command, timeout=300)


def run_httpx(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute httpx for HTTP probing."""
    target = params.get('target')
    additional_args = params.get('additional_args', '')
    
    if not target:
        return {'success': False, 'error': 'target parameter is required'}
    
    # httpx uses stdin or -l for file
    if target.startswith('http'):
        # Single URL via stdin
        command = f"echo '{target}' | /home/kali/go/bin/httpx -silent"
    else:
        # File path
        command = f"/home/kali/go/bin/httpx -l {target} -silent"
    
    if additional_args:
        command += f" {additional_args}"
    
    return execute_command(command, timeout=300)


def run_searchsploit(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute searchsploit for exploit database search."""
    query = params.get('query')
    additional_args = params.get('additional_args', '')
    
    if not query:
        return {'success': False, 'error': 'query parameter is required'}
    
    command = f"searchsploit {query}"
    if additional_args:
        command += f" {additional_args}"
    
    return execute_command(command, timeout=60)


def run_nuclei(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Nuclei vulnerability scanner."""
    target = params.get('target')
    templates = params.get('templates', '')
    severity = params.get('severity', '')
    additional_args = params.get('additional_args', '')
    
    if not target:
        return {'success': False, 'error': 'target parameter is required'}
    
    command = f"nuclei -u {target} -silent"
    
    if templates:
        command += f" -t {templates}"
    
    if severity:
        command += f" -severity {severity}"
    
    if additional_args:
        command += f" {additional_args}"
    
    return execute_command(command, timeout=600)


def run_arjun(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Arjun parameter discovery tool."""
    url = params.get('url')
    method = params.get('method', 'GET')
    wordlist = params.get('wordlist', '')
    additional_args = params.get('additional_args', '')
    
    if not url:
        return {'success': False, 'error': 'url parameter is required'}
    
    command = f"arjun -u {url}"
    
    if method:
        command += f" -m {method}"
    
    if wordlist:
        command += f" -w {wordlist}"
    
    if additional_args:
        command += f" {additional_args}"
    
    return execute_command(command, timeout=300)


def run_subzy(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Subzy for subdomain takeover detection."""
    target = params.get('target')
    targets_file = params.get('targets_file')
    additional_args = params.get('additional_args', '')
    
    if not target and not targets_file:
        return {'success': False, 'error': 'Either target or targets_file parameter is required'}
    
    subzy_path = "/home/kali/go/bin/subzy"
    
    if target:
        # Create temp file with target
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(target)
            temp_file = f.name
        command = f"{subzy_path} run --targets {temp_file}"
    else:
        command = f"{subzy_path} run --targets {targets_file}"
    
    if additional_args:
        command += f" {additional_args}"
    
    result = execute_command(command, timeout=300)
    
    # Cleanup temp file if created
    if target:
        try:
            os.unlink(temp_file)
        except:
            pass
    
    return result


def run_assetfinder(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Assetfinder for subdomain discovery."""
    domain = params.get('domain')
    subs_only = params.get('subs_only', True)
    additional_args = params.get('additional_args', '')
    
    if not domain:
        return {'success': False, 'error': 'domain parameter is required'}
    
    assetfinder_path = "/home/kali/go/bin/assetfinder"
    command = assetfinder_path
    
    if subs_only:
        command += " --subs-only"
    
    command += f" {domain}"
    
    if additional_args:
        command += f" {additional_args}"
    
    return execute_command(command, timeout=120)


def run_ffuf(params: Dict[str, Any], on_output=None) -> Dict[str, Any]:
    """Execute ffuf web fuzzer with the provided parameters."""
    try:
        url = params.get("url", "")
        wordlist = params.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        additional_args = params.get("additional_args", "")
        method = params.get("method", "GET")
        headers = params.get("headers", "")
        data = params.get("data", "")
        
        if not url:
            logger.warning("ffuf called without URL parameter")
            return {
                "error": "URL parameter is required and must contain FUZZ keyword",
                "success": False
            }
        
        if "FUZZ" not in url and not data:
            logger.warning("ffuf called without FUZZ keyword in URL or data")
            return {
                "error": "URL or data must contain FUZZ keyword for fuzzing position",
                "success": False
            }
        
        command = f"ffuf -u {url} -w {wordlist}"
        
        if method and method != "GET":
            command += f" -X {method}"
        
        if headers:
            # Support multiple headers separated by semicolon
            for header in headers.split(";"):
                if header.strip():
                    command += f" -H '{header.strip()}'"
        
        if data:
            command += f" -d '{data}'"
        
        if additional_args:
            command += f" {additional_args}"
        
        # Use provided callback or default logging callback
        output_callback = on_output
        if not output_callback:
            def handle_ffuf_output(source, line):
                logger.info(f"[FFUF-{source.upper()}] {line}")
            output_callback = handle_ffuf_output
        
        # Execute with streaming support
        result = execute_command(command, on_output=output_callback, timeout=300)
        return result
    except Exception as e:
        logger.error(f"Error in ffuf: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Server error: {str(e)}",
            "success": False
        }


def run_waybackurls(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute waybackurls for archived URL discovery."""
    target = params.get('target')
    additional_args = params.get('additional_args', '')
    
    if not target:
        return {'success': False, 'error': 'target parameter is required'}
    
    command = f"/home/kali/go/bin/waybackurls {target}"
    if additional_args:
        command += f" {additional_args}"
    
    return execute_command(command, timeout=300)


def run_byp4xx(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute byp4xx 403 bypass tool."""
    url = params.get('url')
    additional_args = params.get('additional_args', '')
    
    if not url:
        return {'success': False, 'error': 'url parameter is required'}
    
    command = f"/home/kali/byp4xx/byp4xx {url}"
    if additional_args:
        command += f" {additional_args}"
    
    return execute_command(command, timeout=120)
