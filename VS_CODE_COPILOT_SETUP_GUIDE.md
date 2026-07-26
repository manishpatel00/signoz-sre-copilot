# VS Code + GitHub Copilot Setup Guide
## Build SigNoz SRE Copilot Step-by-Step

---

## Step 0: Prerequisites Check

Before starting, ensure you have:

| Tool | Version | Check Command |
|------|---------|---------------|
| VS Code | Latest | `code --version` |
| Python | 3.11+ | `python3 --version` |
| Docker | Latest | `docker --version` |
| Git | Latest | `git --version` |
| GitHub Account | Active | github.com |

**Install VS Code:** https://code.visualstudio.com/download

---

## Step 1: Install VS Code Extensions (5 minutes)

### Method A: Via VS Code UI
1. Open VS Code
2. Press `Ctrl+Shift+X` (Windows/Linux) or `Cmd+Shift+X` (Mac)
3. Search and install each extension:

```
Extension Name                    Publisher           Purpose
─────────────────────────────────────────────────────────────────────
Python                            Microsoft           Python support
Pylance                           Microsoft           Type checking
YAML                              Red Hat             YAML validation
GitHub Copilot                    GitHub              AI code completion
GitHub Copilot Chat               GitHub              AI chat interface
Docker                            Microsoft           Container support
Thunder Client                    Rangav              API testing
```

### Method B: Via Command Line (Faster)
```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension redhat.vscode-yaml
code --install-extension github.copilot
code --install-extension github.copilot-chat
code --install-extension ms-azuretools.vscode-docker
code --install-extension rangav.vscode-thunder-client
```

### Verify Extensions
Press `Ctrl+Shift+P` -> Type `Extensions: Show Installed Extensions`
You should see 7 extensions installed.

---

## Step 2: Configure GitHub Copilot (3 minutes)

### 2.1 Sign In
1. Press `Ctrl+Shift+P`
2. Type `GitHub Copilot: Sign In`
3. Click 'Sign in to GitHub.com'
4. Browser opens -> Authorize VS Code
5. Return to VS Code -> 'Signed in as [your-username]'

### 2.2 Enable Copilot Chat
1. Look for the chat icon (speech bubble) in the left sidebar
2. Or press `Ctrl+Shift+I` to open Copilot Chat
3. You should see 'GitHub Copilot' at the top

### 2.3 Configure Copilot Settings
Press `Ctrl+,` (comma) to open Settings, search for:

```
copilot setting                          recommended value
─────────────────────────────────────────────────────────────
github.copilot.enable                    true
github.copilot.inlineSuggest.enable      true
github.copilot.chat.locale               English
github.copilot.chat.codeGeneration.instructions  -> Add custom instructions
```

**Add Custom Instructions:**
In Settings, find `github.copilot.chat.codeGeneration.instructions`
Click 'Edit in settings.json' and add:

```json
{
  "github.copilot.chat.codeGeneration.instructions": [
    {
      "text": "You are building the SigNoz SRE Copilot - an autonomous incident response system using CrewAI and SigNoz MCP Server. All code must be OpenTelemetry-native, use the SigNoz MCP Server for observability queries, and include safety checks for remediation actions."
    }
  ]
}
```

---

## Step 3: Set Up Project in VS Code (5 minutes)

### 3.1 Create Project Directory
```bash
# Open terminal in VS Code: Ctrl+`
mkdir -p ~/projects/signoz-sre-copilot
cd ~/projects/signoz-sre-copilot

# Initialize git
git init

# Create virtual environment
python3 -m venv venv

# Activate (choose your OS)
source venv/bin/activate        # Mac/Linux
# OR
venv\Scripts\activate         # Windows

# Install dependencies
pip install crewai langchain langchain-openai flask requests \
  opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp \
  opentelemetry-instrumentation opentelemetry-instrumentation-flask \
  kubernetes pytest python-dotenv
```

### 3.2 Open Project in VS Code
```bash
code .
```

### 3.3 Configure Python Interpreter
1. Press `Ctrl+Shift+P`
2. Type `Python: Select Interpreter`
3. Choose `./venv/bin/python` (or `venv\Scripts\python.exe` on Windows)

### 3.4 Create Project Structure
In VS Code terminal (`Ctrl+`):
```bash
mkdir -p agents runbooks instrumentation/collector-config dashboards alerts tests/chaos docs .vscode
```

---

## Step 4: Configure MCP Server in VS Code (3 minutes)

### 4.1 Create MCP Config File
Create `.vscode/mcp.json`:

```json
{
  "servers": {
    "signoz": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### 4.2 Create VS Code Settings
Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "editor.formatOnSave": true,
  "editor.rulers": [80, 120],
  "files.associations": {
    "casting.yaml": "yaml",
    "*.yml": "yaml"
  },
  "github.copilot.chat.codeGeneration.instructions": [
    {
      "text": "Build SigNoz SRE Copilot using CrewAI. All telemetry must be OpenTelemetry-native. Use SigNoz MCP Server (JSON-RPC over HTTP at localhost:8000) for observability queries. Include safety checks: dry-run mode and namespace allowlisting for all K8s remediation actions."
    }
  ]
}
```

### 4.3 Create .cursorrules File
Create `.cursorrules` in project root:

```
# SigNoz SRE Copilot - Development Rules

## Architecture
1. All telemetry MUST be OpenTelemetry-native
2. All SigNoz interactions go through MCP Server (JSON-RPC over HTTP)
3. All deployments reproducible via Foundry (casting.yaml)
4. All agents emit their own traces (meta-observability)
5. All remediation actions have dry-run mode

## Code Style
- Python: PEP 8, type hints, docstrings
- YAML: 2-space indent
- All functions >10 lines MUST have OTel spans

## Safety
- Remediation defaults to DRY_RUN=true
- Only act on ALLOWED_NAMESPACES
- Never delete data
- Prefer rolling restart

## MCP Endpoints
- Health: GET /livez
- Tools: POST /mcp (JSON-RPC 2.0)
- Headers: SIGNOZ-API-KEY
```

---

## Step 5: Use Copilot to Generate Code (The Build Phase)

### 5.1 Open Copilot Chat
- Press `Ctrl+Shift+I` or click the chat icon
- Select 'Edit with Copilot' mode

### 5.2 Generate diagnostic_agent.py

**Prompt Copilot Chat:**
```
Create a CrewAI diagnostic agent that queries SigNoz via MCP Server.
The agent should have these tools:
1. query_traces - Query traces via MCP JSON-RPC
2. query_metrics - PromQL queries via MCP
3. query_logs - Log search via MCP
4. get_active_alerts - Fetch firing alerts

Use OpenTelemetry for meta-observability. Include proper error handling.
Save as agents/diagnostic_agent.py
```

**Copilot will generate code. Review it, then save.**

### 5.3 Generate remediation_agent.py

**Prompt:**
```
Create a CrewAI remediation agent with these tools:
1. restart_deployment - Rolling restart of K8s deployment
2. scale_deployment - Scale replicas
3. get_pod_status - Check pod status

Must include safety: DRY_RUN env var check, ALLOWED_NAMESPACES check.
Use subprocess for kubectl. Include OTel tracing.
Save as agents/remediation_agent.py
```

### 5.4 Generate validator_agent.py

**Prompt:**
```
Create a CrewAI validator agent that:
1. Checks service health via MCP metrics query
2. Checks if alerts are still firing via MCP
3. Retries validation with configurable intervals

Save as agents/validator_agent.py
```

### 5.5 Generate orchestrator.py

**Prompt:**
```
Create a Flask orchestrator that:
1. Receives webhooks at POST /webhook/alert
2. Uses CrewAI with sequential process
3. Chains Diagnostic -> Remediation -> Validator agents
4. Returns incident report with trace correlation
5. Has health endpoint at GET /health

Include OTel tracing for the orchestrator itself.
Save as agents/orchestrator.py
```

### 5.6 Generate casting.yaml

**Prompt:**
```
Create a SigNoz Foundry casting.yaml with:
- SigNoz platform (docker compose mode)
- MCP Server enabled on port 8000
- OTel Collector with custom config path
- Ports 4317, 4318, 8889 exposed

Use v1alpha1 API version.
Save as casting.yaml
```

### 5.7 Generate OTel Collector Config

**Prompt:**
```
Create OpenTelemetry Collector config with:
- OTLP receiver (gRPC 4317, HTTP 4318)
- Prometheus receiver for scraping
- Isolation Forest processor (forest_size: 100, contamination_rate: 0.05)
- Resource processor adding deployment.environment
- OTLP exporter to signoz-otel-collector:4317
- Pipelines for traces, metrics, logs

Save as instrumentation/collector-config/otel-collector-config.yaml
```

---

## Step 6: Copilot Inline Suggestions (While Coding)

### How to Trigger Suggestions
1. Start typing a function signature
2. Copilot shows gray ghost text
3. Press `Tab` to accept
4. Press `Esc` to dismiss
5. Press `Alt+]` (or `Option+]` on Mac) for next suggestion

### Example Inline Workflow

**You type:**
```python
def query_sig
```

**Copilot suggests (gray text):**
```python
def query_signoz_traces(service: str, time_range: str = '1h') -> dict:
    # Query SigNoz traces via MCP Server.
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        ...
```

**Press Tab to accept, then modify as needed.**

---

## Step 7: Test with Copilot

### 7.1 Generate Tests

**Prompt Copilot Chat:**
```
Create pytest tests for:
1. MCP connectivity (test_mcp_integration.py)
2. Remediation safety - dry run and namespace blocking (test_remediation.py)
3. Anomaly detection span tagging (test_anomaly_detection.py)

Save in tests/ directory.
```

### 7.2 Generate Dashboard JSON

**Prompt:**
```
Create a SigNoz dashboard JSON with panels for:
1. Active Incidents (value panel)
2. Incidents Resolved 24h (value panel)
3. MTTR (value panel in seconds)
4. Anomaly Score Distribution (graph)
5. MCP Query Latency (graph)

Save as dashboards/sre-copilot-overview.json
```

### 7.3 Generate Alert Rules

**Prompt:**
```
Create SigNoz alert rules YAML with:
1. High Error Rate alert (>5%) with webhook to copilot
2. Anomaly Detection alert (isolation forest score >0.7)
Both should POST to http://sre-copilot:8080/webhook/alert

Save as alerts/high-error-rate.yml
```

---

## Step 8: Deploy and Test

### 8.1 Create .env file
```bash
cp .env.example .env
# Edit with your keys
```

### 8.2 Deploy with Foundry
In VS Code terminal:
```bash
# Install foundryctl if not already
curl -fsSL https://signoz.io/foundry.sh | bash

# Deploy
foundryctl cast -f casting.yaml
```

### 8.3 Test with Thunder Client (VS Code Extension)
1. Open Thunder Client (icon in left sidebar)
2. Create new request:
   - Method: POST
   - URL: http://localhost:8080/webhook/alert
   - Body (JSON):
```json
{
  "alert_name": "test-incident",
  "labels": {
    "service_name": "demo-app",
    "namespace": "default",
    "severity": "warning"
  }
}
```
3. Click Send
4. Check response and logs

---

## Step 9: GitHub Copilot Tips for This Project

### Tip 1: Use @workspace for Context
In Copilot Chat, type:
```
@workspace Explain how the diagnostic agent uses MCP Server
```
This references your entire codebase.

### Tip 2: Generate Docstrings
Select a function, then in Copilot Chat:
```
Generate Google-style docstring for this function
```

### Tip 3: Fix Errors
When you see a red squiggly error:
1. Hover over it
2. Click 'Quick Fix'
3. Select Copilot suggestion

### Tip 4: Generate Commit Messages
After `git add .`, in terminal:
```bash
git copilot suggest  # If available
```
Or use Copilot Chat:
```
Generate a conventional commit message for these changes
```

### Tip 5: Explain Complex Code
Select the orchestrator.py CrewAI setup, then:
```
Explain how the sequential process works in this code
```

---

## Step 10: Final Checklist Before Submission

```bash
# Run all tests
pytest tests/ -v

# Check formatting
black agents/ tests/

# Verify files exist
ls casting.yaml casting.yaml.lock

# Check git status
git status
git add .
git commit -m 'feat: initial SigNoz SRE Copilot implementation'
git push origin main
```

---

## Quick Reference: Copilot Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Tab` | Accept inline suggestion |
| `Esc` | Dismiss suggestion |
| `Alt+]` | Next suggestion |
| `Alt+[` | Previous suggestion |
| `Ctrl+Shift+I` | Open Copilot Chat |
| `Ctrl+Shift+P` | Command palette |
| `Ctrl+K Ctrl+I` | Inline chat |

---

## Troubleshooting

### Copilot not working?
1. Check you are signed in: `Ctrl+Shift+P` -> `GitHub Copilot: Sign In`
2. Check status bar (bottom right) for Copilot icon
3. Reload window: `Ctrl+Shift+P` -> `Developer: Reload Window`

### MCP Server not connecting?
1. Check SigNoz is running: `curl http://localhost:8080/api/v1/health`
2. Check MCP: `curl http://localhost:8000/livez`
3. Verify `.vscode/mcp.json` has correct URL

### Python import errors?
1. Check interpreter: `Ctrl+Shift+P` -> `Python: Select Interpreter`
2. Ensure venv is activated
3. Reinstall: `pip install -r requirements.txt`

---

*Now you are ready to build. Start with Step 1 and work through sequentially.*