# Project: SigNoz SRE Copilot

## Overview
Autonomous SRE agent using CrewAI + SigNoz MCP for self-healing infrastructure.
Winner-tier submission for Agents of SigNoz hackathon (Track 01).

## Key Files
- agents/orchestrator.py - Main Flask webhook server + CrewAI
- agents/diagnostic_agent.py - SigNoz MCP querying agent
- agents/remediation_agent.py - K8s/Helm remediation actions
- agents/validator_agent.py - Post-fix health verification
- casting.yaml - Foundry deployment configuration

## Quick Commands
- make dev - Start local SigNoz + app stack
- make test - Run integration tests
- make cast - Deploy via Foundry
- make demo - Trigger demo incident

## Environment Variables
- SIGNOZ_MCP_URL - MCP server endpoint
- OPENAI_API_KEY - LLM access
- KUBECONFIG - K8s cluster access
- REMEDIATION_DRY_RUN - Safety switch
- ALLOWED_NAMESPACES - Safe namespace list

## Demo Flow
1. make demo triggers a pod crash in test namespace
2. SigNoz alert fires -> Webhook to agent
3. Diagnostic agent queries traces via MCP
4. Remediation agent restarts deployment
5. Validator agent confirms health via MCP
6. Incident report generated

## SigNoz Features Used
1. Traces - All agent operations traced
2. Metrics - PromQL for health validation
3. Logs - Log search for error analysis
4. Dashboards - Custom SRE Copilot dashboard
5. Alerts - Webhook-triggered response
6. Query Builder - Metric alert thresholds
7. MCP Server - LLM-native data access
