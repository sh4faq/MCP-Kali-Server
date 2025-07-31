#!/usr/bin/env python3
"""API Routes module for Kali Server."""

import traceback
from flask import Flask, request, jsonify
from core.config import logger, active_sessions, active_ssh_sessions
from core.ssh_manager import SSHSessionManager
from core.reverse_shell_manager import ReverseShellManager, execute_command
from tools.kali_tools import (
    run_nmap, run_gobuster, run_dirb, run_nikto, run_sqlmap,
    run_metasploit, run_hydra, run_john, run_wpscan, run_enum4linux
)
from utils.file_operations import (
    upload_content_to_kali, download_content_from_kali,
    upload_file_to_target, upload_content_to_target, download_file_from_target, download_content_from_target
)


def setup_routes(app: Flask):
    """Setup all API routes for the Flask application."""
    
    # Health check
    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "message": "Kali Linux Tools API Server is running"
        })

    # Command execution
    @app.route("/api/command", methods=["POST"])
    def command():
        """Execute an arbitrary command on the Kali server."""
        try:
            params = request.json
            if not params or "command" not in params:
                return jsonify({
                    "error": "Command parameter is required"
                }), 400
            
            command = params["command"]
            result = execute_command(command)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in command endpoint: {str(e)}")
            return jsonify({
                "error": f"Server error: {str(e)}"
            }), 500

    # Tool endpoints
    @app.route("/api/tools/nmap", methods=["POST"])
    def nmap():
        try:
            params = request.json or {}
            result = run_nmap(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in nmap endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/gobuster", methods=["POST"])
    def gobuster():
        try:
            params = request.json or {}
            result = run_gobuster(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in gobuster endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/dirb", methods=["POST"])
    def dirb():
        try:
            params = request.json or {}
            result = run_dirb(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in dirb endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/nikto", methods=["POST"])
    def nikto():
        try:
            params = request.json or {}
            result = run_nikto(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in nikto endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/sqlmap", methods=["POST"])
    def sqlmap():
        try:
            params = request.json or {}
            result = run_sqlmap(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in sqlmap endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/metasploit", methods=["POST"])
    def metasploit():
        try:
            params = request.json or {}
            result = run_metasploit(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in metasploit endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/hydra", methods=["POST"])
    def hydra():
        try:
            params = request.json or {}
            result = run_hydra(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in hydra endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/john", methods=["POST"])
    def john():
        try:
            params = request.json or {}
            result = run_john(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in john endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/wpscan", methods=["POST"])
    def wpscan():
        try:
            params = request.json or {}
            result = run_wpscan(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in wpscan endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/enum4linux", methods=["POST"])
    def enum4linux():
        try:
            params = request.json or {}
            result = run_enum4linux(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in enum4linux endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    # SSH session management
    @app.route("/api/ssh/session/start", methods=["POST"])
    def start_ssh_session():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            target = params.get("target")
            username = params.get("username")
            password = params.get("password", "")
            key_file = params.get("key_file", "")
            port = params.get("port", 22)
            session_id = params.get("session_id", f"ssh_{target}_{username}")
            
            if not target or not username:
                return jsonify({"error": "Target and username are required"}), 400
            
            if session_id in active_ssh_sessions:
                return jsonify({"error": f"SSH session {session_id} already exists"}), 400
            
            ssh_manager = SSHSessionManager(target, username, password, key_file, port, session_id)
            result = ssh_manager.start_session()
            
            if result.get("success"):
                active_ssh_sessions[session_id] = ssh_manager
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error starting SSH session: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/session/<session_id>/command", methods=["POST"])
    def execute_ssh_command(session_id):
        try:
            if session_id not in active_ssh_sessions:
                return jsonify({"error": f"SSH session {session_id} not found"}), 404
            
            params = request.json
            if not params or "command" not in params:
                return jsonify({"error": "Command parameter is required"}), 400
            
            command = params["command"]
            timeout = params.get("timeout", 30)
            
            ssh_manager = active_ssh_sessions[session_id]
            result = ssh_manager.send_command(command, timeout)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error executing SSH command: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/session/<session_id>/status", methods=["GET"])
    def get_ssh_session_status(session_id):
        try:
            if session_id not in active_ssh_sessions:
                return jsonify({"error": f"SSH session {session_id} not found"}), 404
            
            ssh_manager = active_ssh_sessions[session_id]
            status = ssh_manager.get_status()
            return jsonify(status)
        except Exception as e:
            logger.error(f"Error getting SSH session status: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/session/<session_id>/stop", methods=["POST"])
    def stop_ssh_session(session_id):
        try:
            if session_id not in active_ssh_sessions:
                return jsonify({"error": f"SSH session {session_id} not found"}), 404
            
            ssh_manager = active_ssh_sessions[session_id]
            ssh_manager.stop()
            del active_ssh_sessions[session_id]
            
            return jsonify({
                "success": True,
                "message": f"SSH session {session_id} stopped successfully"
            })
        except Exception as e:
            logger.error(f"Error stopping SSH session: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/sessions", methods=["GET"])
    def list_ssh_sessions():
        try:
            sessions = {}
            for session_id, ssh_manager in active_ssh_sessions.items():
                sessions[session_id] = ssh_manager.get_status()
            return jsonify({"sessions": sessions})
        except Exception as e:
            logger.error(f"Error listing SSH sessions: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/session/<session_id>/upload_content", methods=["POST"])
    def upload_content_to_ssh_session(session_id):
        """Upload content to target via SSH session with optimized handling for large files"""
        try:
            if session_id not in active_ssh_sessions:
                return jsonify({"error": f"SSH session {session_id} not found"}), 404
            
            params = request.json or {}
            content = params.get("content", "")
            remote_file = params.get("remote_file", "")
            encoding = params.get("encoding", "utf-8")
            method = params.get("method", "auto")
            
            if not content or not remote_file:
                return jsonify({
                    "error": "content and remote_file parameters are required"
                }), 400
            
            ssh_manager = active_ssh_sessions[session_id]
            
            # Decode content first to determine size
            if encoding == "base64":
                import base64
                try:
                    decoded_content = base64.b64decode(content).decode('utf-8')
                except:
                    decoded_content = base64.b64decode(content)
            else:
                decoded_content = content
            
            # Determine file size and optimal method
            if isinstance(decoded_content, bytes):
                file_size = len(decoded_content)
                content_for_upload = base64.b64encode(decoded_content).decode('ascii')
            else:
                file_size = len(decoded_content.encode('utf-8'))
                content_for_upload = base64.b64encode(decoded_content.encode('utf-8')).decode('ascii')
            
            logger.info(f"SSH upload: {file_size} bytes to {remote_file}")
            
            # Auto-select method based on file size
            if method == "auto":
                if file_size < 50 * 1024:
                    method = "single_command"
                elif file_size < 500 * 1024:
                    method = "streaming"
                else:
                    method = "chunked"
            
            import time
            start_time = time.time()
            
            if method == "single_command":
                upload_cmd = f"echo '{content_for_upload}' | base64 -d > {remote_file}"
                result = ssh_manager.send_command(upload_cmd, timeout=60)
            elif method == "streaming":
                heredoc_command = f"""cat << 'EOF_B64' | base64 -d > {remote_file}
{content_for_upload}
EOF_B64"""
                result = ssh_manager.send_command(heredoc_command, timeout=120)
            elif method == "chunked":
                chunk_size = 8192
                chunks = [content_for_upload[i:i+chunk_size] for i in range(0, len(content_for_upload), chunk_size)]
                temp_b64_file = f"{remote_file}.b64temp"
                
                ssh_manager.send_command(f"rm -f {temp_b64_file}", timeout=10)
                
                for i, chunk in enumerate(chunks):
                    append_cmd = f"echo '{chunk}' >> {temp_b64_file}"
                    chunk_result = ssh_manager.send_command(append_cmd, timeout=30)
                    if not chunk_result.get('success'):
                        return jsonify({
                            "success": False,
                            "error": f"Failed to upload chunk {i+1}/{len(chunks)}"
                        }), 500
                
                decode_cmd = f"base64 -d {temp_b64_file} > {remote_file} && rm {temp_b64_file}"
                result = ssh_manager.send_command(decode_cmd, timeout=60)
            else:
                return jsonify({"error": f"Unsupported upload method: {method}"}), 400
            
            upload_time = time.time() - start_time
            
            if result.get('success'):
                verify_result = ssh_manager.send_command(f"ls -la {remote_file}", timeout=10)
                return jsonify({
                    "success": True,
                    "message": f"Content uploaded successfully via SSH using {method} method",
                    "remote_file": remote_file,
                    "file_size": file_size,
                    "method": method,
                    "upload_time_seconds": round(upload_time, 2),
                    "verification": verify_result.get('output', '').strip()
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"Upload failed using {method} method"
                }), 500
                
        except Exception as e:
            logger.error(f"Error in SSH upload endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/session/<session_id>/download_content", methods=["POST"])
    def download_content_from_ssh_session(session_id):
        """Download content from target via SSH session with optimized handling for large files"""
        try:
            if session_id not in active_ssh_sessions:
                return jsonify({"error": f"SSH session {session_id} not found"}), 404
            
            params = request.json or {}
            remote_file = params.get("remote_file", "")
            method = params.get("method", "auto")
            max_size_mb = params.get("max_size_mb", 100)
            
            if not remote_file:
                return jsonify({
                    "error": "remote_file parameter is required"
                }), 400
            
            ssh_manager = active_ssh_sessions[session_id]
            
            # Check if file exists and get size
            stat_result = ssh_manager.send_command(f"stat -c %s {remote_file} 2>/dev/null || echo 'FILE_NOT_FOUND'", timeout=10)
            
            if not stat_result.get('success') or 'FILE_NOT_FOUND' in stat_result.get('output', ''):
                return jsonify({
                    "success": False,
                    "error": f"File {remote_file} not found on target"
                }), 404
            
            try:
                file_size_str = stat_result.get('output', '0').strip()
                
                # Clean ANSI escape sequences and control characters
                import re
                # Remove ANSI escape sequences
                ansi_escape = re.compile(r'\x1b\[[0-9;]*[mGKHlh]|\x1b\[[?0-9;]*[lh]')
                clean_output = ansi_escape.sub('', file_size_str)
                # Remove only non-digit control characters (preserve 0-9)
                clean_output = re.sub(r'[\r\n\x00-\x08\x0b-\x1f\x7f-\x9f]', '', clean_output).strip()
                # Remove SSH_END_xxxxx markers
                clean_output = re.sub(r'SSH_END_[a-f0-9]+', '', clean_output).strip()
                # Extract only digits
                clean_output = re.sub(r'[^0-9]', '', clean_output)
                
                file_size = int(clean_output)
                file_size_mb = file_size / (1024 * 1024)
            except ValueError as e:
                logger.error(f"Failed to parse file size from stat output: {e}")
                return jsonify({
                    "success": False,
                    "error": f"Failed to get file size: invalid stat output"
                }), 500
                
            if file_size_mb > max_size_mb:
                return jsonify({
                    "success": False,
                    "error": f"File too large: {file_size_mb:.1f}MB (max: {max_size_mb}MB)"
                }), 400
            
            logger.info(f"SSH download: {file_size} bytes from {remote_file}")
            
            # Auto-select method based on file size
            if method == "auto":
                method = "direct" if file_size < 1024 * 1024 else "chunked"
            
            import time
            start_time = time.time()
            
            if method == "direct":
                # Use a command that ensures proper output separation
                download_cmd = f"base64 -w 0 {remote_file} && echo"
                result = ssh_manager.send_command(download_cmd, timeout=120)
                
                if result.get('success'):
                    content_b64_raw = result.get('output', '').strip()
                    
                    # Clean base64 output from SSH markers and control characters
                    import re
                    # Remove ANSI escape sequences
                    ansi_escape = re.compile(r'\x1b\[[0-9;]*[mGKHlh]|\x1b\[[?0-9;]*[lh]')
                    content_b64_clean = ansi_escape.sub('', content_b64_raw)
                    # Remove SSH_END_xxxxx markers
                    content_b64_clean = re.sub(r'SSH_END_[a-f0-9]+', '', content_b64_clean)
                    # Keep only valid base64 characters (A-Z, a-z, 0-9, +, /, =)
                    content_b64_clean = re.sub(r'[^A-Za-z0-9+/=]', '', content_b64_clean)
                    
                    logger.info(f"SSH download: {len(content_b64_clean)} base64 chars from {remote_file}")
                    
                    download_time = time.time() - start_time
                    return jsonify({
                        "success": True,
                        "content": content_b64_clean,
                        "remote_file": remote_file,
                        "file_size": file_size,
                        "method": method,
                        "download_time_seconds": round(download_time, 2)
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Failed to download file content"
                    }), 500
                
            elif method == "chunked":
                chunk_size = 8192
                total_chunks = (file_size + chunk_size - 1) // chunk_size
                temp_b64_file = f"{remote_file}.b64temp"
                
                encode_cmd = f"base64 -w 0 {remote_file} > {temp_b64_file}"
                encode_result = ssh_manager.send_command(encode_cmd, timeout=120)
                
                if not encode_result.get('success'):
                    return jsonify({
                        "success": False,
                        "error": "Failed to encode file for chunked download"
                    }), 500
                
                content_parts = []
                chunk_b64_size = (chunk_size * 4) // 3
                
                for i in range(total_chunks):
                    start_pos = i * chunk_b64_size
                    chunk_cmd = f"dd if={temp_b64_file} bs=1 skip={start_pos} count={chunk_b64_size} 2>/dev/null"
                    chunk_result = ssh_manager.send_command(chunk_cmd, timeout=30)
                    
                    if chunk_result.get('success'):
                        content_parts.append(chunk_result.get('output', ''))
                    else:
                        ssh_manager.send_command(f"rm -f {temp_b64_file}", timeout=10)
                        return jsonify({
                            "success": False,
                            "error": f"Failed to download chunk {i+1}/{total_chunks}"
                        }), 500
                
                ssh_manager.send_command(f"rm -f {temp_b64_file}", timeout=10)
                content_b64 = ''.join(content_parts)
                download_time = time.time() - start_time
                
                return jsonify({
                    "success": True,
                    "content": content_b64,
                    "remote_file": remote_file,
                    "file_size": file_size,
                    "method": method,
                    "chunks": total_chunks,
                    "download_time_seconds": round(download_time, 2)
                })
            
            else:
                return jsonify({"error": f"Unsupported download method: {method}"}), 400
                    
        except Exception as e:
            logger.error(f"Error in SSH download endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/estimate_transfer", methods=["POST"])
    def estimate_ssh_transfer():
        """Estimate SSH transfer performance and provide recommendations"""
        try:
            params = request.json or {}
            file_size_bytes = params.get("file_size_bytes", 0)
            operation = params.get("operation", "upload")
            
            if file_size_bytes <= 0:
                return jsonify({
                    "error": "file_size_bytes parameter must be greater than 0"
                }), 400
            
            file_size_kb = file_size_bytes / 1024
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            base_throughput_kbps = 1000
            overhead_factor = 1.2
            
            if file_size_bytes < 50 * 1024:
                recommended_method = "single_command"
                estimated_time = (file_size_kb * overhead_factor) / base_throughput_kbps + 1
            elif file_size_bytes < 500 * 1024:
                recommended_method = "streaming"
                estimated_time = (file_size_kb * overhead_factor) / base_throughput_kbps + 2
            else:
                recommended_method = "chunked"
                estimated_time = (file_size_kb * overhead_factor) / base_throughput_kbps + 3
            
            return jsonify({
                "success": True,
                "file_size_bytes": file_size_bytes,
                "file_size_kb": round(file_size_kb, 2),
                "file_size_mb": round(file_size_mb, 2),
                "operation": operation,
                "recommended_method": recommended_method,
                "estimated_time_seconds": round(estimated_time, 2),
                "estimated_throughput_kbps": base_throughput_kbps,
                "recommendations": [
                    "Compress files before transfer",
                    "Consider splitting large files",
                    "Use direct Kali upload for files on local network"
                ] if file_size_mb > 10 else []
            })
            
        except Exception as e:
            logger.error(f"Error in SSH estimate endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    # Reverse shell management
    @app.route("/api/shell/listener/start", methods=["POST"])
    def start_reverse_shell_listener():
        try:
            params = request.json or {}
            port = params.get("port", 4444)
            session_id = params.get("session_id", f"shell_{port}")
            listener_type = params.get("listener_type", "pwncat")
            
            if session_id in active_sessions:
                return jsonify({"error": f"Session {session_id} already exists"}), 400
            
            shell_manager = ReverseShellManager(port, session_id, listener_type)
            result = shell_manager.start_listener()
            
            if result.get("success"):
                active_sessions[session_id] = shell_manager
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error starting reverse shell listener: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/shell/session/<session_id>/command", methods=["POST"])
    def execute_shell_command(session_id):
        try:
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            params = request.json
            if not params or "command" not in params:
                return jsonify({"error": "Command parameter is required"}), 400
            
            command = params["command"]
            timeout = params.get("timeout", 60)
            
            shell_manager = active_sessions[session_id]
            result = shell_manager.send_command(command, timeout)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error executing shell command: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/shell/session/<session_id>/status", methods=["GET"])
    def get_shell_session_status(session_id):
        try:
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            shell_manager = active_sessions[session_id]
            status = shell_manager.get_status()
            return jsonify(status)
        except Exception as e:
            logger.error(f"Error getting shell session status: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/shell/session/<session_id>/stop", methods=["POST"])
    def stop_shell_session(session_id):
        try:
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            shell_manager = active_sessions[session_id]
            shell_manager.stop()
            del active_sessions[session_id]
            
            return jsonify({
                "success": True,
                "message": f"Shell session {session_id} stopped successfully"
            })
        except Exception as e:
            logger.error(f"Error stopping shell session: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/shell/sessions", methods=["GET"])
    def list_shell_sessions():
        try:
            sessions = {}
            for session_id, shell_manager in active_sessions.items():
                sessions[session_id] = shell_manager.get_status()
            return jsonify(sessions)
        except Exception as e:
            logger.error(f"Error listing shell sessions: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    # File operations
    @app.route("/api/kali/upload", methods=["POST"])
    def upload_to_kali():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            content = params.get("content")
            remote_path = params.get("remote_path")
            
            if not content or not remote_path:
                return jsonify({"error": "Content and remote_path are required"}), 400
            
            result = upload_content_to_kali(content, remote_path)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in upload to Kali: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/kali/download", methods=["POST"])
    def download_from_kali():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            remote_file = params.get("remote_file")
            
            if not remote_file:
                return jsonify({"error": "remote_file parameter is required"}), 400
            
            result = download_content_from_kali(remote_file)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in download from Kali: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/target/upload_file", methods=["POST"])
    def upload_file_to_target_endpoint():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            session_id = params.get("session_id")
            local_file = params.get("local_file")
            remote_file = params.get("remote_file")
            method = params.get("method", "base64")
            
            if not all([session_id, local_file, remote_file]):
                return jsonify({"error": "session_id, local_file, and remote_file are required"}), 400
            
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            shell_manager = active_sessions[session_id]
            result = upload_file_to_target(shell_manager, local_file, remote_file, method)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in upload file to target: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/target/upload_content", methods=["POST"])
    def upload_content_to_target_endpoint():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            session_id = params.get("session_id")
            content = params.get("content")
            remote_file = params.get("remote_file")
            method = params.get("method", "base64")
            encoding = params.get("encoding", "utf-8")
            
            if not all([session_id, content, remote_file]):
                return jsonify({"error": "session_id, content, and remote_file are required"}), 400
            
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            shell_manager = active_sessions[session_id]
            result = upload_content_to_target(shell_manager, content, remote_file, method, encoding)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in upload content to target: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/target/download_file", methods=["POST"])
    def download_file_from_target_endpoint():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            session_id = params.get("session_id")
            remote_file = params.get("remote_file")
            local_file = params.get("local_file")
            method = params.get("method", "base64")
            
            if not all([session_id, remote_file, local_file]):
                return jsonify({"error": "session_id, remote_file, and local_file are required"}), 400
            
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            shell_manager = active_sessions[session_id]
            result = download_file_from_target(shell_manager, remote_file, local_file, method)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in download file from target: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/target/download_content", methods=["POST"])
    def download_content_from_target_endpoint():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            session_id = params.get("session_id")
            remote_file = params.get("remote_file")
            method = params.get("method", "base64")
            
            if not all([session_id, remote_file]):
                return jsonify({"error": "session_id and remote_file are required"}), 400
            
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            shell_manager = active_sessions[session_id]
            result = download_content_from_target(shell_manager, remote_file, method)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in download content from target: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    return app
