# Setup Guide

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- kubectl (optional)
- 8GB RAM minimum

## Step 1: Install Foundry

```bash
curl -fsSL https://signoz.io/foundry.sh | bash
```

## Step 2: Clone and Configure

```bash
git clone https://github.com/manish-kumar/signoz-sre-copilot.git
cd signoz-sre-copilot
cp .env.example .env
# Edit .env with your API keys
```

## Step 3: Deploy SigNoz

```bash
foundryctl cast -f casting.yaml
```

## Step 4: Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 5: Start the Copilot

```bash
python agents/orchestrator.py
```

## Step 6: Trigger Demo Incident

```bash
curl -X POST http://localhost:8080/webhook/alert \
  -H "Content-Type: application/json" \
  -d '{
    "alert_name": "demo-incident",
    "labels": {
      "service_name": "demo-app",
      "namespace": "default",
      "severity": "warning"
    }
  }'
```

## Verification

```bash
# Check SigNoz UI
open http://localhost:8080

# Check MCP Server
curl http://localhost:8000/livez

# Check Copilot Health
curl http://localhost:8080/health
```
