# Demo Script

## Pre-Demo Setup

1. Start SigNoz: `make cast`
2. Start Copilot: `python agents/orchestrator.py`
3. Open 3 terminal windows

## Demo Flow (7 minutes)

### Scene 1: The Problem (0:00-0:30)
- Show SigNoz dashboard
- Explain: "AI agents need observable infrastructure"
- Show custom SRE Copilot dashboard

### Scene 2: The Setup (0:30-1:00)
- Run `make cast`
- Show Foundry deploying everything
- Show `make health` output

### Scene 3: The Incident (1:00-1:30)
- Run `make demo`
- Show alert firing in SigNoz
- Show webhook received

### Scene 4: The Diagnosis (1:30-2:30)
- Show Diagnostic Agent logs
- Show MCP queries executed
- Show trace analysis in SigNoz

### Scene 5: The Fix (2:30-3:30)
- Show Remediation Agent logs
- Show deployment restart
- Show pod status changing

### Scene 6: The Validation (3:30-4:00)
- Show Validator Agent confirming health
- Show alert clearing
- Show metrics normal

### Scene 7: The Impact (4:00-5:00)
- Show MTTR improvement
- Show anomaly detection scores
- Show incident timeline

### Scene 8: Architecture Deep Dive (5:00-6:00)
- Show 3-agent system
- Show MCP Server integration
- Show Isolation Forest config

### Scene 9: Conclusion (6:00-7:00)
- Recap innovations
- Show GitHub repo
- Call to action
