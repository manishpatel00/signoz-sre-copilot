# Architecture Documentation

## System Overview

SigNoz SRE Copilot is a multi-agent autonomous incident response system.

## Components

### 1. SigNoz Platform
- Self-hosted via SigNoz Foundry
- Ingests traces, metrics, logs
- Provides MCP Server for LLM-native querying

### 2. OpenTelemetry Collector
- Receives OTLP data
- Runs Isolation Forest for anomaly detection
- Forwards enriched data to SigNoz

### 3. SRE Copilot (Agent System)
- **Orchestrator**: Flask webhook server + CrewAI
- **Diagnostic Agent**: Queries SigNoz via MCP
- **Remediation Agent**: Executes safe K8s actions
- **Validator Agent**: Confirms fixes via MCP

### 4. Demo Application
- Generates synthetic traffic and errors
- Instrumented with OpenTelemetry

## Data Flow

```
Demo App -> OTel Collector -> SigNoz
                              |
                         Alert Manager
                              |
                         Webhook -> Copilot
                              |
                    +---------+---------+
                    |                   |
            Diagnostic          Remediation
            (MCP queries)       (K8s actions)
                    |                   |
                    +---------+---------+
                              |
                        Validator (MCP verify)
                              |
                        Resolved
```

## Security

- MCP Server requires SIGNOZ-API-KEY
- Namespace allowlists for remediation
- Dry-run mode prevents accidents
- All actions traced for audit
