"""SigNoz SRE Copilot - Main Orchestrator."""
import os
import json
import logging
import datetime
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from crewai import Crew, Process, Task
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize global OpenTelemetry tracer provider
if not isinstance(trace.get_tracer_provider(), TracerProvider):
    resource = Resource.create({
        "service.name": "sre-copilot-orchestrator",
        "service.version": "1.0.0",
        "deployment.environment": "hackathon"
    })
    provider = TracerProvider(resource=resource)
    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
            insecure=True
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    except Exception:
        pass
    trace.set_tracer_provider(provider)

tracer = trace.get_tracer("orchestrator")

# Fallback imports to support both absolute and relative execution
try:
    from .diagnostic_agent import diagnostic_agent, _query_traces, _query_logs, _get_active_alerts
    from .remediation_agent import remediation_agent, _restart_deployment
    from .validator_agent import validator_agent, _check_service_health, _wait_and_validate
except ImportError:
    from diagnostic_agent import diagnostic_agent, _query_traces, _query_logs, _get_active_alerts
    from remediation_agent import remediation_agent, _restart_deployment
    from validator_agent import validator_agent, _check_service_health, _wait_and_validate

class IncidentManager:
    def __init__(self):
        self.crew = Crew(
            agents=[diagnostic_agent, remediation_agent, validator_agent],
            tasks=[],
            process=Process.sequential,
            verbose=True,
            memory=False,
        )

    @tracer.start_as_current_span("incident.handle")
    def handle_incident(self, alert_data: dict) -> dict:
        service = alert_data.get("service", "unknown")
        namespace = alert_data.get("namespace", "default")
        alert_name = alert_data.get("alert_name", "unknown")
        severity = alert_data.get("severity", "warning")

        span = trace.get_current_span()
        span.set_attribute("incident.service", service)
        span.set_attribute("incident.alert", alert_name)
        span.set_attribute("incident.severity", severity)

        logger.info(f"Handling incident: {alert_name} for {service}/{namespace}")

        diagnosis_task = Task(
            description=f"""
            Investigate incident for service {service} in namespace {namespace}.
            Alert: {alert_name} (severity: {severity})
            Steps:
            1. Get all active alerts
            2. Query traces for {service} in last 30 minutes
            3. Query error logs for {service} in last 30 minutes
            4. Query key metrics (error rate, p95 latency)
            5. Correlate findings and identify root cause
            Provide detailed root cause analysis with evidence.
            """,
            agent=diagnostic_agent,
            expected_output="Detailed root cause analysis with specific evidence."
        )

        remediation_task = Task(
            description=f"""
            Based on root cause, execute remediation for {service}/{namespace}.
            Safety rules: Only allowed namespaces, prefer rolling restart, check dry-run.
            Steps:
            1. Check current pod status
            2. Determine safest remediation
            3. Execute action
            4. Report exact action and expected outcome
            """,
            agent=remediation_agent,
            expected_output="Report of remediation action taken."
        )

        validation_task = Task(
            description=f"""
            Validate remediation for {service}/{namespace} was successful.
            Steps:
            1. Check service health metrics
            2. Wait and retry up to 5 times (30s intervals)
            3. Confirm no alerts firing
            4. Verify traces show normal operation
            Report whether incident is fully resolved.
            """,
            agent=validator_agent,
            expected_output="Validation report confirming resolution or escalation."
        )

        if os.getenv("MOCK_LLM", "false").lower() == "true":
            logger.info("Executing SRE Copilot in MOCK LLM mode (bypassing CrewAI LLM calls)...")
            
            # Step 1: Mock Diagnostic Agent
            logger.info("[Mock Diagnostic Agent] Inspecting incident data...")
            traces = _query_traces(service, "30m")
            logs = _query_logs(service, "error", "30m")
            health = _check_service_health(service, namespace)
            
            diag_report = f"""
            === MOCK DIAGNOSIS REPORT ===
            Active Alerts: Firing alert {alert_name} for {service} in {namespace}.
            Traces checked: {traces[:200]}...
            Logs checked: {logs[:200]}...
            Metrics checked: {health}
            Root Cause: Detected failing pod or high error rate in service {service}.
            """
            logger.info(diag_report)
            
            # Step 2: Mock Remediation Agent
            logger.info("[Mock Remediation Agent] Determining remediation action...")
            remediation_result = _restart_deployment(namespace, service)
            logger.info(f"[Mock Remediation Agent] Result: {remediation_result}")
            
            # Step 3: Mock Validator Agent
            logger.info("[Mock Validator Agent] Validating recovery...")
            validation_result = _wait_and_validate(service, namespace, retries=3)
            logger.info(f"[Mock Validator Agent] Result: {validation_result}")
            
            result = f"PASSED:\n{diag_report}\n{remediation_result}\n{validation_result}"
        else:
            self.crew.tasks = [diagnosis_task, remediation_task, validation_task]
            result = self.crew.kickoff()

        # Retrieve current trace ID for correlation in the report
        trace_id = trace.format_trace_id(span.get_span_context().trace_id)

        report = {
            "incident_id": f"{service}-{alert_name}-{int(time.time())}",
            "service": service,
            "namespace": namespace,
            "alert": alert_name,
            "severity": severity,
            "status": "resolved" if "PASSED" in str(result) else "escalated",
            "result": str(result),
            "trace_id": trace_id,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        span.set_attribute("incident.status", report["status"])
        span.set_attribute("incident.id", report["incident_id"])
        logger.info(f"Incident {report['incident_id']} status: {report['status']}")
        return report

app = Flask(__name__)
manager = IncidentManager()

# Instrument Flask & Requests for automatic trace propagation
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "sre-copilot"})

@app.route("/webhook/alert", methods=["POST"])
def handle_alert_webhook():
    with tracer.start_as_current_span("webhook.alert") as span:
        data = request.json or {}
        span.set_attribute("webhook.alert_name", data.get("alert_name", "unknown"))

        alert_data = {
            "service": data.get("labels", {}).get("service_name") or data.get("labels", {}).get("service", "unknown"),
            "namespace": data.get("labels", {}).get("namespace", "default"),
            "alert_name": data.get("alert_name", "unknown"),
            "severity": data.get("labels", {}).get("severity", "warning"),
        }

        try:
            report = manager.handle_incident(alert_data)
            return jsonify({"status": "processing", "report": report}), 202
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8085"))
    app.run(host="0.0.0.0", port=port)
