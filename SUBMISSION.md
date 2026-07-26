# Agents of SigNoz - Submission Form Answers
# Copy-paste these into the Google Form

---

## Email
manishpatel953249@gmail.com

## Team name
Manish Kumar (Solo)

## Name of the person submitting the form
Manish Kumar

## Track you are submitting for
Track 1: AI & Agent Observability

## Project description
SigNoz SRE Copilot is an autonomous self-healing infrastructure system built on SigNoz MCP Server and CrewAI. When a SigNoz alert fires, a multi-agent CrewAI system autonomously diagnoses the incident using SigNoz traces, metrics, and logs via the MCP Server, executes safe Kubernetes remediation actions (restart, scale, rollback), and validates the fix before closing the incident - all without human intervention.

Key innovations:
1. FIRST open-source SRE agent built specifically on SigNoz MCP Server
2. Inline anomaly detection using OpenTelemetry Collector Isolation Forest processor
3. Meta-observability: the copilot traces its own decisions in SigNoz
4. One-command deployment via SigNoz Foundry (casting.yaml)
5. Safety-first remediation with dry-run mode and namespace allowlisting

The system addresses the core hackathon theme: "If you can't observe your AI agents, you don't own them" - by making the infrastructure that runs AI agents fully observable and self-healing.

## GitHub link to project
https://github.com/manish-kumar/signoz-sre-copilot

## Deployed link to project
http://localhost:8080 (self-hosted via Foundry)
SigNoz UI: http://localhost:8080

## YouTube video demo link
[3-minute demo video URL here]

Video covers:
- 0:00-0:30: Project overview and problem statement
- 0:30-1:00: Tech stack and architecture (CrewAI + SigNoz MCP + Isolation Forest)
- 1:00-2:30: Live demo - trigger incident, autonomous diagnosis, remediation, validation
- 2:30-3:00: Learning, growth, and future roadmap

## Describe how you have used SigNoz in your project
I used ALL 7 SigNoz features deeply:

1. TRACES: Every agent operation (diagnostic, remediation, validation) emits OpenTelemetry traces to SigNoz. The Diagnostic Agent queries traces via the SigNoz MCP Server to find root causes.

2. METRICS: The Remediation Agent queries PromQL metrics via MCP to check error rates and latency. The OTel Collector Isolation Forest processor adds anomaly scores to metrics in-flight.

3. LOGS: The Diagnostic Agent searches logs via MCP to find error messages and stack traces during incident investigation.

4. DASHBOARDS: Created a custom "SRE Copilot Overview" dashboard in SigNoz showing active incidents, MTTR, anomaly scores, and MCP query latency.

5. ALERTS: Configured alert rules with webhook endpoints that trigger the autonomous incident response. Alerts include auto_remediate labels.

6. QUERY BUILDER: Used SigNoz Query Builder in alert rules for error rate and latency thresholds.

7. MCP SERVER: This is the core innovation. The entire system is built around the SigNoz MCP Server - agents query SigNoz natively via JSON-RPC, making the LLM an integral part of the observability workflow.

## Project blog link
[Blog post URL on Dev.to/Medium/Substack]

Blog title: "Building an Autonomous SRE Copilot with SigNoz MCP and CrewAI"
Covers:
- Why autonomous incident response matters for AI infrastructure
- Deep dive into SigNoz MCP Server integration
- How CrewAI agents use observability data to make decisions
- Setting up Isolation Forest anomaly detection in OTel Collector
- Lessons learned and future improvements

## How was your hackathon experience?
This hackathon pushed me to explore the cutting edge of agent-native observability. Building on SigNoz MCP Server was eye-opening - the ability for an LLM to natively query traces, metrics, and logs opens entirely new paradigms for autonomous operations. The Foundry deployment system made self-hosting SigNoz incredibly smooth. The biggest challenge was ensuring remediation safety - implementing dry-run mode and namespace allowlisting was critical. I am excited to continue developing this into a production-ready open-source tool.
