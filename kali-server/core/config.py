#!/usr/bin/env python3
"""Configuration module for Kali Server."""

import os
import logging
import sys

# Version information
VERSION = "0.2.0"

# Configuration
API_PORT = int(os.environ.get("API_PORT", 5000))
DEBUG_MODE = os.environ.get("DEBUG_MODE", "0").lower() in ("1", "true", "yes", "y")
TEST_MODE = os.environ.get("TEST_MODE", "0").lower() in ("1", "true", "yes", "y")
COMMAND_TIMEOUT = 300  # 5 minutes default timeout

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for troubleshooting
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global dictionaries for active sessions
active_sessions = {}
active_ssh_sessions = {}

def get_network_interfaces_info():
    """Get network interfaces information for display at startup."""
    try:
        from utils.network_utils import get_network_info
        network_info = get_network_info()
        
        if not network_info.get("success", False):
            logger.warning("Could not retrieve network information")
            return {"pentest_suitable": [], "test_only_suitable": [], "all_interfaces": []}
        
        interfaces = network_info.get("interfaces", [])
        pentest_ips = [iface for iface in interfaces if iface.get("is_pentest_suitable", False)]
        test_only_ips = [iface for iface in interfaces if iface.get("is_test_suitable", False) and not iface.get("is_pentest_suitable", False)]
        
        return {
            "pentest_suitable": pentest_ips,
            "test_only_suitable": test_only_ips,
            "all_interfaces": interfaces
        }
    except Exception as e:
        logger.error(f"Error getting network interfaces info: {e}")
        return {"pentest_suitable": [], "test_only_suitable": [], "all_interfaces": []}

def display_network_interfaces(test_mode=False):
    """Display available network interfaces at startup."""
    interfaces_info = get_network_interfaces_info()
    
    # Always display pentest suitable IPs
    pentest_ips = interfaces_info.get("pentest_suitable", [])
    if pentest_ips:
        logger.info("🌐 Available IP addresses for pentesting:")
        for interface in pentest_ips:
            interface_type = []
            if interface.get("is_vpn_tunnel"):
                interface_type.append("VPN")
            if interface.get("is_docker_bridge"):
                interface_type.append("Docker")
            
            type_info = f" ({', '.join(interface_type)})" if interface_type else ""
            logger.info(f"   📡 {interface['interface']}: {interface['ip']}{type_info}")
    
    # Display test-only IPs only in test mode
    if test_mode:
        test_only_ips = interfaces_info.get("test_only_suitable", [])
        if test_only_ips:
            logger.info("🧪 Additional IP addresses for local testing:")
            for interface in test_only_ips:
                interface_type = []
                if interface.get("is_vpn_tunnel"):
                    interface_type.append("VPN")
                if interface.get("is_docker_bridge"):
                    interface_type.append("Docker Bridge")
                
                type_info = f" ({', '.join(interface_type)})" if interface_type else ""
                logger.info(f"   🔧 {interface['interface']}: {interface['ip']}{type_info}")
    
    if not pentest_ips and (not test_mode or not interfaces_info.get("test_only_suitable", [])):
        logger.warning("⚠️  No suitable IP addresses found for reverse shell operations")
        logger.info("💡 Make sure you have at least one non-loopback network interface UP")
