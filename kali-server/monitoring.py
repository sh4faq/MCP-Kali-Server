"""
Comprehensive monitoring for MCP-Kali-Server
Tracks system resources, API usage, and tool execution
"""

import psutil
import json
import time
import threading
from datetime import datetime
from collections import deque
from pathlib import Path

class SystemMonitor:
    """Monitor system resources and tool execution"""
    
    def __init__(self, log_dir="/var/log/mcp-kali"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        
        # Metrics storage (last 1000 measurements)
        self.metrics = deque(maxlen=1000)
        self.active_processes = {}
        
        # Start monitoring thread
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'percent': psutil.virtual_memory().percent,
                    'available_mb': psutil.virtual_memory().available / 1024 / 1024
                },
                'disk': {
                    'percent': psutil.disk_usage('/').percent,
                    'free_gb': psutil.disk_usage('/').free / 1024 / 1024 / 1024
                },
                'network': {
                    'connections': len(psutil.net_connections()),
                },
                'processes': len(self.active_processes)
            }
            
            self.metrics.append(metrics)
            
            # Write to log file every minute
            if len(self.metrics) % 60 == 0:
                self._write_metrics_log()
            
            time.sleep(1)
    
    def _write_metrics_log(self):
        """Write metrics to daily log file"""
        log_file = self.log_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        with open(log_file, 'a') as f:
            for metric in list(self.metrics)[-60:]:  # Last minute of metrics
                f.write(json.dumps(metric) + '\n')
    
    def track_tool_execution(self, tool_name, command, start_time=None):
        """Track tool execution"""
        if start_time is None:
            # Starting execution
            process_id = f"{tool_name}_{time.time()}"
            self.active_processes[process_id] = {
                'tool': tool_name,
                'command': command,
                'start_time': datetime.now().isoformat(),
                'pid': None
            }
            return process_id
        else:
            # Execution completed
            if start_time in self.active_processes:
                execution_time = time.time() - float(start_time.split('_')[1])
                log_entry = {
                    'tool': tool_name,
                    'command': command,
                    'execution_time': execution_time,
                    'completed': datetime.now().isoformat()
                }
                
                # Log to file
                log_file = self.log_dir / f"tools_{datetime.now().strftime('%Y%m%d')}.jsonl"
                with open(log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
                
                # Remove from active processes
                del self.active_processes[start_time]
    
    def get_system_health(self):
        """Get current system health status"""
        current_metrics = self.metrics[-1] if self.metrics else {}
        
        health = {
            'status': 'healthy',
            'issues': [],
            'metrics': current_metrics
        }
        
        # Check for issues
        if current_metrics:
            if current_metrics.get('cpu_percent', 0) > 90:
                health['issues'].append('High CPU usage')
                health['status'] = 'degraded'
            
            if current_metrics.get('memory', {}).get('percent', 0) > 90:
                health['issues'].append('High memory usage')
                health['status'] = 'degraded'
            
            if current_metrics.get('disk', {}).get('percent', 0) > 90:
                health['issues'].append('Low disk space')
                health['status'] = 'warning'
        
        return health
    
    def get_recent_metrics(self, minutes=5):
        """Get recent metrics for analysis"""
        return list(self.metrics)[-minutes * 60:]

class APILogger:
    """Structured logging for API requests"""
    
    def __init__(self, log_file="/var/log/mcp-kali/api.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True, parents=True)
    
    def log_request(self, request, response, execution_time):
        """Log API request and response"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'endpoint': request.path,
            'client_ip': request.remote_addr,
            'parameters': request.json if request.method == 'POST' else dict(request.args),
            'response_status': response.status_code if hasattr(response, 'status_code') else 200,
            'execution_time': execution_time,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        # Sanitize sensitive data
        if 'password' in log_entry['parameters']:
            log_entry['parameters']['password'] = '***REDACTED***'
        
        # Write to log file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        return log_entry
    
    def get_recent_requests(self, count=100):
        """Get recent API requests for analysis"""
        if not self.log_file.exists():
            return []
        
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
            recent = []
            for line in lines[-count:]:
                try:
                    recent.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            return recent

# Initialize global monitors
system_monitor = SystemMonitor()
api_logger = APILogger()

def get_monitoring_dashboard():
    """Get a dashboard view of system status"""
    health = system_monitor.get_system_health()
    recent_requests = api_logger.get_recent_requests(10)
    active_tools = system_monitor.active_processes
    
    dashboard = {
        'system_health': health,
        'active_tools': list(active_tools.values()),
        'recent_api_calls': recent_requests,
        'uptime_seconds': time.time()  # Would need process start time in production
    }
    
    return dashboard
