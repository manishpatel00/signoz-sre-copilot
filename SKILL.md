# SigNoz MCP Development Skill

## Context
You are developing the SigNoz SRE Copilot - an autonomous incident response system.
You have access to:
- SigNoz MCP Server at http://localhost:8000
- SigNoz UI at http://localhost:8080
- OTel Collector at http://localhost:4317 (gRPC) / 4318 (HTTP)

## Available MCP Tools (JSON-RPC 2.0)
- query_traces - Query traces with filters
- query_metrics - PromQL queries
- query_logs - Search logs
- get_alerts - Fetch active alerts
- create_alert - Create alert rules
- create_dashboard - Create dashboard panels

## MCP Request Format
```python
payload = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "query_traces",
        "arguments": {"service": "my-service", "time_range": "1h"}
    },
    "id": 1
}
headers = {"Content-Type": "application/json", "SIGNOZ-API-KEY": key}
response = requests.post("http://localhost:8000/mcp", json=payload, headers=headers)
```

## Patterns
### Pattern 1: Observability-First Development
Always instrument before implementing business logic.

### Pattern 2: Trace-Driven Debugging
When debugging, start with trace_id correlation.

### Pattern 3: MCP-Native Queries
Prefer MCP tools over direct SigNoz API calls.

### Pattern 4: Safety-First Remediation
Always check DRY_RUN and ALLOWED_NAMESPACES before executing K8s commands.

## Environment Variables
- SIGNOZ_MCP_URL: MCP server endpoint
- SIGNOZ_API_KEY: Authentication key
- OTEL_EXPORTER_OTLP_ENDPOINT: OTel collector endpoint
- REMEDIATION_DRY_RUN: true/false safety switch
- ALLOWED_NAMESPACES: Comma-separated safe namespaces
- OPENAI_API_KEY: For CrewAI LLM
