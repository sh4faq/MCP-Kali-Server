# Streaming Support for Kali Tools

## Overview

The MCP Kali Server now supports real-time streaming for penetration testing tools, allowing clients to receive output as it's generated rather than waiting for the complete scan to finish.

## Supported Tools

The following tools support streaming output:

```mermaid
flowchart TD
    subgraph "Streaming Tools Classification"
        subgraph "Dedicated Endpoints"
            GOB[Gobuster<br/>/api/tools/gobuster]
            DIRB[Dirb<br/>/api/tools/dirb]
            NIK[Nikto<br/>/api/tools/nikto]
        end
        
        subgraph "Auto-Streaming Tools via /api/command"
            FFUF[ffuf<br/>Web fuzzer]
            FEROX[feroxbuster<br/>Directory enumeration]
            WFUZZ[wfuzz<br/>Web application fuzzer]
            DIRS[dirsearch<br/>Web path scanner]
            PING[ping<br/>Network testing]
            BASH[bash<br/>General commands]
        end
    end
    
    subgraph "Configuration"
        CONFIG[STREAMING_TOOLS<br/>in tool_config.py]
    end
    
    subgraph "Streaming Methods"
        MANUAL[Manual: streaming=true]
        AUTO[Automatic Detection]
    end
    
    GOB --> MANUAL
    DIRB --> MANUAL
    NIK --> MANUAL
    
    FFUF --> AUTO
    FEROX --> AUTO
    WFUZZ --> AUTO
    DIRS --> AUTO
    PING --> AUTO
    BASH --> AUTO
    
    CONFIG --> AUTO
    
    style AUTO fill:#e8f5e8
    style MANUAL fill:#fff3e0
    style CONFIG fill:#f3e5f5
```

### Tools with Dedicated Endpoints
- **Gobuster** (`/api/tools/gobuster`)
- **Dirb** (`/api/tools/dirb`) 
- **Nikto** (`/api/tools/nikto`)

### Tools via Command Execution Endpoint
These tools automatically enable streaming when executed via `/api/command`:

- **ffuf** - Web fuzzer
- **feroxbuster** - Fast directory/file enumeration tool
- **wfuzz** - Web application fuzzer
- **dirsearch** - Web path scanner
- **ping** - Network connectivity testing
- **bash** - General bash commands (useful for testing)

All tools listed above will automatically stream their output in real-time when executed through either their dedicated endpoints or the general command execution endpoint.

## How to Enable Streaming

### For Tools with Dedicated Endpoints

To enable streaming for tools with dedicated endpoints (Gobuster, Dirb, Nikto), add the `streaming: true` parameter to your request:

```json
{
    "url": "http://example.com",
    "mode": "dir",
    "wordlist": "/usr/share/wordlists/dirb/common.txt",
    "streaming": true
}
```

### For Tools via Command Execution

For tools in the STREAMING_TOOLS list, streaming is **automatically enabled** when using the `/api/command` endpoint. No additional parameter is needed:

```json
{
    "command": "ffuf -u http://example.com/FUZZ -w /usr/share/wordlists/dirb/common.txt"
}
```

```json
{
    "command": "feroxbuster -u http://example.com -w /usr/share/wordlists/dirb/common.txt"
}
```

The system automatically detects these tools and enables streaming based on the tool configuration in `STREAMING_TOOLS`.

## Streaming Response Format

When streaming is enabled, the endpoint returns a Server-Sent Events (SSE) stream instead of a JSON response. The response has the following format:

### Content Type
```
Content-Type: text/plain; charset=utf-8
Cache-Control: no-cache
Connection: keep-alive
```

### Event Types Flow

```mermaid
stateDiagram-v2
    [*] --> StreamStart : Client connects
    StreamStart --> OutputEvents : Tool execution begins
    OutputEvents --> OutputEvents : Real-time output
    OutputEvents --> HeartbeatEvents : Keep connection alive
    HeartbeatEvents --> OutputEvents : Continue streaming
    OutputEvents --> ResultEvents : Tool completes
    ResultEvents --> CompleteEvents : Stream finalization
    CompleteEvents --> [*] : Connection closed
    
    OutputEvents --> ErrorEvents : Error occurs
    ErrorEvents --> CompleteEvents : Stream terminated
    
    note right of OutputEvents
        stdout/stderr lines
        as they are generated
    end note
    
    note right of HeartbeatEvents
        Periodic keep-alive
        prevents timeouts
    end note
    
    note right of ResultEvents
        Final execution status
        return code, success
    end note
```

### Event Types

1. **Output Events** - Real-time command output
   ```
   data: {"type": "output", "source": "stdout", "line": "Found: /admin"}
   ```

2. **Heartbeat Events** - Keep connection alive
   ```
   data: {"type": "heartbeat"}
   ```

3. **Result Events** - Final execution result
   ```
   data: {"type": "result", "success": true, "return_code": 0}
   ```

4. **Error Events** - Error information
   ```
   data: {"type": "error", "message": "Server error: Connection refused"}
   ```

5. **Complete Events** - Indicates stream end
   ```
   data: {"type": "complete"}
   ```

## Streaming Architecture

```mermaid
flowchart TB
    subgraph "Client Layer"
        CLIENT[Client Application]
    end
    
    subgraph "API Layer"
        DEDICATED[Dedicated Tool Endpoints<br/>/api/tools/*]
        COMMAND[Command Execution<br/>/api/command]
    end
    
    subgraph "Processing Layer"
        DETECT[Tool Detection<br/>STREAMING_TOOLS]
        THREAD[Background Thread<br/>Non-blocking execution]
        QUEUE[Output Queue<br/>Thread-safe communication]
    end
    
    subgraph "Response Layer"
        SSE[Server-Sent Events<br/>Real-time streaming]
        JSON[Standard JSON<br/>Non-streaming response]
    end
    
    CLIENT -->|POST with streaming=true| DEDICATED
    CLIENT -->|POST command| COMMAND
    
    DEDICATED -->|Check streaming flag| THREAD
    COMMAND -->|Auto-detect tool| DETECT
    DETECT -->|Tool in STREAMING_TOOLS| THREAD
    DETECT -->|Tool not in list| JSON
    
    THREAD -->|Real-time output| QUEUE
    QUEUE -->|Stream events| SSE
    SSE -->|data: events| CLIENT
    
    style DETECT fill:#e8f5e8
    style SSE fill:#e1f5fe
    style THREAD fill:#fff3e0
```

## Streaming Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Detector
    participant Thread
    participant Tool
    participant Queue
    
    Client->>+API: POST request
    API->>+Detector: Check tool type
    
    alt Dedicated endpoint with streaming=true
        Detector-->>API: Enable streaming
    else Auto-streaming tool via /api/command
        Detector-->>API: Enable streaming (auto)
    else Non-streaming tool
        Detector-->>API: Standard response
        API-->>Client: JSON response
    end
    
    API->>+Thread: Start background execution
    Thread-->>-API: Thread started
    API-->>-Client: Start SSE stream
    
    par Background Execution
        Thread->>+Tool: Execute command
        Tool-->>Queue: stdout/stderr output
        Tool-->>Queue: completion status
        Tool-->>-Thread: Process finished
    end
    
    par Stream Events
        Queue-->>Client: data: {"type":"output",...}
        Queue-->>Client: data: {"type":"heartbeat"}
        Queue-->>Client: data: {"type":"result",...}
        Queue-->>Client: data: {"type":"complete"}
    end
```

## Benefits

1. **Real-time feedback** - See results as they're discovered
2. **Long-running scans** - No timeout issues for lengthy operations
3. **Progressive results** - Start analyzing results before scan completion
4. **Resource efficiency** - Lower memory usage compared to buffering all output

## Compatibility

- **Non-streaming mode** remains available by omitting the `streaming` parameter or setting it to `false`
- **Backward compatibility** - Existing clients continue to work without changes
- **Fallback behavior** - If streaming fails, the endpoint falls back to standard JSON response

## Implementation Details

The streaming implementation uses:
- **Threading** - Commands run in separate threads to prevent blocking
- **Queue-based communication** - Thread-safe output collection
- **Flask streaming** - Server-Sent Events via `stream_with_context`
- **Error handling** - Comprehensive error recovery and reporting
- **Auto-detection** - Tools in `STREAMING_TOOLS` list automatically enable streaming
- **Tool configuration** - Centralized configuration in `tool_config.py` manages streaming behavior

### Streaming Tool Detection

The system automatically detects streaming tools based on the `STREAMING_TOOLS` configuration:

```python
# From tool_config.py
STREAMING_TOOLS = [
    "ffuf",
    "gobuster", 
    "feroxbuster",
    "wfuzz",
    "dirsearch",
    "dirb",
    "nikto",
    "ping",
    "bash"
]
```

When any of these tools are executed via `/api/command`, streaming is automatically enabled regardless of any streaming parameter.

## Troubleshooting

### Common Issues

1. **Connection drops** - Check network stability and firewall settings
2. **Missing heartbeats** - Verify client timeout configurations
3. **Incomplete streams** - Ensure proper error handling in client code

### Debug Mode

Enable debug logging in the Kali server configuration to see detailed streaming operations:

```python
LOGGING_LEVEL = "DEBUG"
```

This will show:
- Stream setup and teardown
- Thread lifecycle management
- Queue operations
- Error conditions
