#!/usr/bin/env python3
"""Docker management module for test container lifecycle."""

import subprocess
import time
import logging
import os
import sys
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DockerManager:
    """Manages Docker test container lifecycle."""
    
    def __init__(self, container_name: str = "kali-test-ssh", image_name: str = "kali-test-ssh:latest"):
        """Initialize Docker manager.
        
        Args:
            container_name: Name of the Docker container
            image_name: Name of the Docker image
        """
        self.container_name = container_name
        self.image_name = image_name
        self.is_running = False
        self.docker_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests", "docker")
        
    def _run_command(self, command: list, capture_output: bool = True, timeout: int = 30) -> Dict[str, Any]:
        """Run a command and return the result.
        
        Args:
            command: Command to run as a list
            capture_output: Whether to capture stdout/stderr
            timeout: Command timeout in seconds
            
        Returns:
            Dictionary with command result information
        """
        try:
            # Ensure we have a proper environment with PATH
            env = os.environ.copy()
            
            # Common Docker paths on Linux systems
            docker_paths = [
                "/usr/bin/docker",
                "/usr/local/bin/docker",
                "/bin/docker",
                "/snap/bin/docker"
            ]
            
            # If command starts with 'docker', try to find the full path
            if command and command[0] == "docker":
                docker_cmd = None
                # First try to use the command as-is (it might be in PATH)
                try:
                    test_result = subprocess.run(
                        ["which", "docker"], 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    if test_result.returncode == 0 and test_result.stdout.strip():
                        docker_cmd = test_result.stdout.strip()
                except:
                    # If 'which' fails, try common paths
                    for path in docker_paths:
                        if os.path.exists(path):
                            docker_cmd = path
                            break
                
                if docker_cmd:
                    command[0] = docker_cmd
                    logger.debug(f"Using Docker at: {docker_cmd}")
            
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=self.docker_dir,
                env=env
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "command": " ".join(command)
            }
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {' '.join(command)}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "command": " ".join(command)
            }
        except FileNotFoundError as e:
            logger.error(f"Command not found: {' '.join(command)}. Error: {e}")
            logger.error("Please ensure Docker is installed and available in PATH.")
            # Try to provide more specific error information
            if command and command[0] in ["docker", "/usr/bin/docker", "/usr/local/bin/docker"]:
                logger.error("Docker installation suggestions:")
                logger.error("  - sudo apt update && sudo apt install docker.io")
                logger.error("  - sudo systemctl start docker")
                logger.error("  - sudo usermod -aG docker $USER (then logout/login)")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command not found: {command[0]}",
                "command": " ".join(command)
            }
        except Exception as e:
            logger.error(f"Error running command {' '.join(command)}: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": " ".join(command)
            }
    
    def check_docker_available(self) -> bool:
        """Check if Docker is available and running.
        
        Returns:
            True if Docker is available, False otherwise
        """
        logger.info("Checking Docker availability...")
        
        # First, try to find Docker executable
        docker_paths = [
            "docker",  # Try PATH first
            "/usr/bin/docker",
            "/usr/local/bin/docker", 
            "/bin/docker",
            "/snap/bin/docker"
        ]
        
        docker_found = False
        docker_path = None
        
        for path in docker_paths:
            try:
                if path == "docker":
                    # Try using 'which' to find docker in PATH
                    which_result = subprocess.run(
                        ["which", "docker"], 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    if which_result.returncode == 0 and which_result.stdout.strip():
                        docker_path = which_result.stdout.strip()
                        docker_found = True
                        break
                else:
                    # Check if file exists at specific path
                    if os.path.exists(path):
                        docker_path = path
                        docker_found = True
                        break
            except Exception as e:
                logger.debug(f"Error checking Docker path {path}: {e}")
                continue
        
        if not docker_found:
            logger.error("Docker executable not found in common locations.")
            logger.error("Please install Docker: sudo apt update && sudo apt install docker.io")
            logger.error("Or install Docker CE: https://docs.docker.com/engine/install/")
            return False
        
        logger.info(f"Docker found at: {docker_path}")
        
        # Test Docker version
        result = self._run_command([docker_path, "--version"])
        if not result["success"]:
            logger.error("Docker version check failed")
            logger.error(f"Error: {result['stderr']}")
            return False
            
        logger.info(f"Docker version: {result['stdout'].strip()}")
        
        # Check if Docker daemon is running
        daemon_result = self._run_command([docker_path, "info"])
        if not daemon_result["success"]:
            logger.error("Docker daemon is not running or not accessible")
            logger.error("Try:")
            logger.error("  sudo systemctl start docker")
            logger.error("  sudo usermod -aG docker $USER (then logout/login)")
            logger.error("  sudo docker info (to test with sudo)")
            logger.error(f"Error details: {daemon_result['stderr']}")
            return False
            
        logger.info("✅ Docker daemon is running and accessible")
        return True
    
    def is_container_running(self) -> bool:
        """Check if the test container is currently running.
        
        Returns:
            True if container is running, False otherwise
        """
        result = self._run_command(["docker", "ps", "-q", "-f", f"name={self.container_name}"])
        return result["success"] and bool(result["stdout"].strip())
    
    def is_image_available(self) -> bool:
        """Check if the Docker image is available locally.
        
        Returns:
            True if image exists, False otherwise
        """
        result = self._run_command(["docker", "images", "-q", self.image_name])
        return result["success"] and bool(result["stdout"].strip())
    
    def build_image(self) -> bool:
        """Build the Docker image if it doesn't exist.
        
        Returns:
            True if build successful, False otherwise
        """
        if self.is_image_available():
            logger.info(f"Docker image {self.image_name} already exists")
            return True
            
        logger.info(f"Building Docker image {self.image_name}...")
        
        result = self._run_command(["docker", "build", "-t", self.image_name, "."], timeout=300)
        
        if result["success"]:
            logger.info("Docker image built successfully")
            return True
        else:
            logger.error(f"Failed to build Docker image: {result['stderr']}")
            return False
    
    def start_container(self) -> bool:
        """Start the Docker test container.
        
        Returns:
            True if container started successfully, False otherwise
        """
        if self.is_container_running():
            logger.info(f"Container {self.container_name} is already running")
            self.is_running = True
            return True
        
        # Build image if necessary
        if not self.build_image():
            return False
        
        # Remove existing container if it exists
        logger.info("Removing any existing container...")
        self._run_command(["docker", "rm", "-f", self.container_name])
        
        # Start new container
        logger.info(f"Starting Docker container {self.container_name}...")
        result = self._run_command([
            "docker", "run", "-d",
            "--name", self.container_name,
            "-p", "2222:22",
            "-p", "4444:4444", 
            "-p", "4445:4445",
            "-p", "8080:8080",
            self.image_name
        ])
        
        if not result["success"]:
            logger.error(f"Failed to start container: {result['stderr']}")
            return False
        
        # Wait for services to start
        logger.info("Waiting for container services to start...")
        time.sleep(8)
        
        # Verify container is running
        if self.is_container_running():
            logger.info("✅ Docker container started successfully")
            logger.info("📋 SSH available at: localhost:2222 (testuser:testpass)")
            logger.info("📋 Reverse shell ports: 4444, 4445")
            self.is_running = True
            return True
        else:
            logger.error("Container failed to start properly")
            return False
    
    def stop_container(self) -> bool:
        """Stop and remove the Docker test container.
        
        Returns:
            True if container stopped successfully, False otherwise
        """
        if not self.is_container_running():
            logger.info(f"Container {self.container_name} is not running")
            self.is_running = False
            return True
        
        logger.info(f"Stopping Docker container {self.container_name}...")
        result = self._run_command(["docker", "stop", self.container_name])
        
        if result["success"]:
            # Remove the container
            self._run_command(["docker", "rm", self.container_name])
            logger.info("✅ Docker container stopped and removed")
            self.is_running = False
            return True
        else:
            logger.error(f"Failed to stop container: {result['stderr']}")
            return False
    
    def get_container_status(self) -> Dict[str, Any]:
        """Get detailed status information about the container.
        
        Returns:
            Dictionary with container status information
        """
        running = self.is_container_running()
        image_available = self.is_image_available()
        
        status = {
            "container_name": self.container_name,
            "image_name": self.image_name,
            "is_running": running,
            "image_available": image_available,
            "docker_available": self.check_docker_available()
        }
        
        if running:
            # Get container details
            result = self._run_command(["docker", "inspect", self.container_name])
            if result["success"]:
                status["container_details"] = "Container inspection successful"
            else:
                status["container_details"] = "Failed to inspect container"
        
        return status


# Global Docker manager instance
docker_manager = DockerManager()
