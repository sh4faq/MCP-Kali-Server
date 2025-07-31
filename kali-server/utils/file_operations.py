#!/usr/bin/env python3
"""File Operations module for Kali Server."""

import os
import base64
from typing import Dict, Any
from flask import Flask
from core.config import logger


def upload_content_to_kali(content: str, remote_path: str) -> Dict[str, Any]:
    """
    Upload content directly to the Kali server filesystem using robust base64 chunking.
    
    Args:
        content: Base64 encoded content to upload
        remote_path: Destination path on the Kali server
        
    Returns:
        Dict with success status and message
    """
    try:
        # Decode base64 encoded content
        file_content = base64.b64decode(content)
        
        logger.info(f"Upload request: {len(content)} base64 chars -> {len(file_content)} bytes to {remote_path}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(remote_path), exist_ok=True)
        
        # Write file to disk
        with open(remote_path, "wb") as f:
            f.write(file_content)
        
        # Verify file was written correctly
        if os.path.exists(remote_path):
            written_size = os.path.getsize(remote_path)
            logger.info(f"File written successfully: {written_size} bytes")
            return {
                "success": True,
                "message": f"File uploaded successfully to {remote_path}",
                "size": written_size
            }
        else:
            logger.error("File was not created on disk")
            return {
                "error": "File was not created on disk",
                "success": False
            }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


def download_content_from_kali(remote_file: str) -> Dict[str, Any]:
    """
    Download content from the Kali server filesystem.
    
    Args:
        remote_file: Path to the file on the Kali server
        
    Returns:
        Dict with file content and metadata or error
    """
    try:
        logger.info(f"Download request for file: {remote_file}")
        
        if not remote_file:
            logger.error("No remote_file parameter provided")
            return {
                "error": "remote_file parameter is required",
                "success": False
            }
            
        if not os.path.exists(remote_file):
            logger.error(f"File not found: {remote_file}")
            return {
                "error": f"File not found: {remote_file}",
                "success": False
            }
        
        # Get file size before reading
        file_size = os.path.getsize(remote_file)
        logger.info(f"Original file size on disk: {file_size} bytes")
        
        # Read file in binary mode
        with open(remote_file, "rb") as f:
            file_content = f.read()
        
        # Log the size of file content read
        logger.info(f"File content read: {len(file_content)} bytes")
        
        # Verify content is not empty
        if len(file_content) == 0:
            logger.warning("File content is empty")
            return {
                "error": "File is empty",
                "success": False
            }
        
        # Encode content to base64 for safe transport
        encoded_content = base64.b64encode(file_content).decode('ascii')
        logger.info(f"Base64 encoded content: {len(encoded_content)} chars")
        
        return {
            "success": True,
            "content": encoded_content,
            "filename": os.path.basename(remote_file),
            "path": remote_file,
            "size": len(file_content),
            "encoded_size": len(encoded_content)
        }
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


def upload_file_to_target(session_manager, local_file: str, remote_file: str, method: str = "base64") -> Dict[str, Any]:
    """
    Upload a file from the Kali server to a target via reverse shell.
    
    Args:
        session_manager: ReverseShellManager instance
        local_file: Path to the local file on the Kali server
        remote_file: Path where to save the file on the target
        method: Upload method (currently only "base64" is supported)
        
    Returns:
        Dict with success status and transfer statistics
    """
    try:
        logger.info(f"Starting file upload: {local_file} -> {remote_file}")
        
        if not os.path.exists(local_file):
            logger.error(f"Local file not found: {local_file}")
            return {
                "error": f"Local file not found: {local_file}",
                "success": False
            }
        
        # Read local file
        with open(local_file, "rb") as f:
            file_content = f.read()
        
        # Use the session manager's upload method
        result = session_manager.upload_content(file_content, remote_file, method="auto")
        
        if result.get("success"):
            logger.info(f"File upload completed successfully: {len(file_content)} bytes")
            result.update({
                "local_file": local_file,
                "remote_file": remote_file,
                "size": len(file_content)
            })
        
        return result
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


def upload_content_to_target(session_manager, content: str, remote_file: str, method: str = "base64", encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Upload content directly to the target via reverse shell.
    
    Args:
        session_manager: ReverseShellManager instance
        content: Base64 encoded content to upload
        remote_file: Path where to save the file on the target
        method: Upload method (currently only "base64" is supported)
        encoding: Content encoding (utf-8 or binary)
        
    Returns:
        Dict with success status and transfer statistics
    """
    try:
        logger.info(f"Starting content upload: {len(content)} chars -> {remote_file}")
        
        # Decode base64 content
        if encoding == "binary" or method == "base64":
            file_content = base64.b64decode(content)
        else:
            file_content = content.encode(encoding)
        
        # Use the session manager's upload method
        result = session_manager.upload_content(file_content, remote_file, method="auto")
        
        if result.get("success"):
            logger.info(f"Content upload completed successfully: {len(file_content)} bytes")
            result.update({
                "remote_file": remote_file,
                "size": len(file_content),
                "original_content_size": len(content)
            })
        
        return result
    except Exception as e:
        logger.error(f"Content upload error: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


def download_file_from_target(session_manager, remote_file: str, local_file: str, method: str = "base64") -> Dict[str, Any]:
    """
    Download a file from the target to the Kali server via reverse shell.
    
    Args:
        session_manager: ReverseShellManager instance
        remote_file: Path to the file on the target
        local_file: Path where to save the file on the Kali server
        method: Download method (currently only "base64" is supported)
        
    Returns:
        Dict with success status and file information
    """
    try:
        logger.info(f"Starting file download: {remote_file} -> {local_file}")
        
        if method == "base64":
            # Use base64 encoding to download the file
            command = f"base64 -w 0 {remote_file}"
            result = session_manager.send_command(command, timeout=120)
            
            if not result.get("success"):
                logger.error(f"Failed to execute download command: {result.get('error', 'Unknown error')}")
                return {
                    "error": f"Failed to execute download command: {result.get('error', 'Unknown error')}",
                    "success": False
                }
            
            # Get the base64 output
            output = result.get("output", "").strip()
            if not output:
                logger.error("No output received from download command")
                return {
                    "error": "No output received from download command",
                    "success": False
                }
            
            try:
                # Decode base64 content
                file_content = base64.b64decode(output)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(local_file), exist_ok=True)
                
                # Write file to disk
                with open(local_file, "wb") as f:
                    f.write(file_content)
                
                # Verify file was written correctly
                if os.path.exists(local_file):
                    written_size = os.path.getsize(local_file)
                    logger.info(f"File downloaded successfully: {written_size} bytes")
                    return {
                        "success": True,
                        "message": f"File downloaded successfully to {local_file}",
                        "remote_file": remote_file,
                        "local_file": local_file,
                        "size": written_size,
                        "method": method
                    }
                else:
                    logger.error("File was not created on disk")
                    return {
                        "error": "File was not created on disk",
                        "success": False
                    }
                    
            except Exception as decode_error:
                logger.error(f"Failed to decode base64 content: {str(decode_error)}")
                return {
                    "error": f"Failed to decode base64 content: {str(decode_error)}",
                    "success": False
                }
        else:
            logger.error(f"Unsupported download method: {method}")
            return {
                "error": f"Unsupported download method: {method}",
                "success": False
            }
            
    except Exception as e:
        logger.error(f"File download error: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


def download_content_from_target(session_manager, remote_file: str, method: str = "base64") -> Dict[str, Any]:
    """
    Download content from the target via reverse shell and return as base64.
    
    Args:
        session_manager: ReverseShellManager instance
        remote_file: Path to the file on the target
        method: Download method (currently only "base64" is supported)
        
    Returns:
        Dict with success status and base64 encoded content
    """
    try:
        logger.info(f"Starting content download: {remote_file}")
        
        if method == "base64":
            # Use base64 encoding to download the file
            command = f"base64 -w 0 {remote_file}"
            result = session_manager.send_command(command, timeout=120)
            
            if not result.get("success"):
                logger.error(f"Failed to execute download command: {result.get('error', 'Unknown error')}")
                return {
                    "error": f"Failed to execute download command: {result.get('error', 'Unknown error')}",
                    "success": False
                }
            
            # Get the base64 output
            output = result.get("output", "").strip()
            if not output:
                logger.error("No output received from download command")
                return {
                    "error": "No output received from download command",
                    "success": False
                }
            
            try:
                # Verify it's valid base64
                file_content = base64.b64decode(output)
                
                logger.info(f"Content downloaded successfully: {len(file_content)} bytes")
                return {
                    "success": True,
                    "content": output,  # Return raw base64 string
                    "filename": os.path.basename(remote_file),
                    "remote_file": remote_file,
                    "size": len(file_content),
                    "method": method
                }
                    
            except Exception as decode_error:
                logger.error(f"Failed to decode base64 content: {str(decode_error)}")
                return {
                    "error": f"Failed to decode base64 content: {str(decode_error)}",
                    "success": False
                }
        elif method == "cat":
            # Simple cat method for text files
            command = f"cat {remote_file}"
            result = session_manager.send_command(command, timeout=60)
            
            if not result.get("success"):
                logger.error(f"Failed to execute cat command: {result.get('error', 'Unknown error')}")
                return {
                    "error": f"Failed to execute cat command: {result.get('error', 'Unknown error')}",
                    "success": False
                }
            
            # Get the output and encode to base64
            output = result.get("output", "")
            content_b64 = base64.b64encode(output.encode('utf-8')).decode('ascii')
            
            logger.info(f"Content downloaded successfully: {len(output)} chars")
            return {
                "success": True,
                "content": content_b64,
                "filename": os.path.basename(remote_file),
                "remote_file": remote_file,
                "size": len(output),
                "method": method
            }
        else:
            logger.error(f"Unsupported download method: {method}")
            return {
                "error": f"Unsupported download method: {method}",
                "success": False
            }
            
    except Exception as e:
        logger.error(f"Content download error: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }
