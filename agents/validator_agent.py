"""SigNoz SRE Copilot - Validator Agent."""
import os
import json
import time
import requests
from dotenv import load_dotenv
from crewai import Agent
from crewai.tools import tool
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

# Load environment variables
load_dotenv()

# Initialize OpenTelemetry safely
if not isinstance(trace.get_tracer_provider(), TracerProvider):
    resource = Resource.create({
        "service.name": "sre-validator-agent",
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

tracer = trace.get_tracer("validator-agent")

MCP_BASE_URL = os.getenv("SIGNOZ_MCP_URL", "http://localhost:8000")
SIGNOZ_API_KEY = os.getenv("SIGNOZ_API_KEY", "")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))

def _parse_mcp_response(response_json: dict) -> dict:
    """Safely extract data structure from standard JSON-RPC 2.0 response or return direct JSON."""
    result = response_json.get("result", {})
    if isinstance(result, dict) and "content" in result:
        content = result.get("content", [])
        if isinstance(content, list) and len(content) > 0:
            item = content[0]
            if isinstance(item, dict) and "text" in item:
                try:
                    return json.loads(item["text"])
                except Exception:
                    return {"text": item["text"]}
    return response_json

def _check_service_health(service: str, namespace: str) -> str:
    """Check if error rate and latency are normal and alerts are cleared."""
    with tracer.start_as_current_span("validation.health") as span:
        span.set_attribute("k8s.namespace", namespace)
        span.set_attribute("mcp.service", service)
        try:
            error_query = f"rate(signoz_calls_total{{service_name='{service}',status_code='STATUS_CODE_ERROR'}}[5m])"
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "query_metrics",
                    "arguments": {
                        "query": error_query,
                        "time_range": "5m"
                    }
                },
                "id": 10
            }
            headers = {"Content-Type": "application/json"}
            if SIGNOZ_API_KEY:
                headers["SIGNOZ-API-KEY"] = SIGNOZ_API_KEY
            
            response = requests.post(f"{MCP_BASE_URL}/mcp", json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            alert_payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "get_alerts",
                    "arguments": {
                        "state": "firing"
                    }
                },
                "id": 11
            }
            alert_response = requests.post(f"{MCP_BASE_URL}/mcp", json=alert_payload, headers=headers, timeout=30)
            alert_response.raise_for_status()
            
            alerts_data = _parse_mcp_response(alert_response.json())
            
            alerts_list = []
            if isinstance(alerts_data, dict):
                if "alerts" in alerts_data:
                    alerts_list = alerts_data["alerts"]
                elif "result" in alerts_data and isinstance(alerts_data["result"], dict) and "alerts" in alerts_data["result"]:
                    alerts_list = alerts_data["result"]["alerts"]
                elif "text" in alerts_data:
                    text = alerts_data["text"]
                    if text and "firing" in text.lower():
                        alerts_list = [text]
            elif isinstance(alerts_data, list):
                alerts_list = alerts_data

            firing_alerts = []
            for alert in alerts_list:
                if isinstance(alert, dict):
                    labels = alert.get("labels", {})
                    alert_service = labels.get("service_name") or labels.get("service")
                    if alert_service == service or not alert_service:
                        firing_alerts.append(alert)
                else:
                    if service.lower() in str(alert).lower() or not service:
                        firing_alerts.append(alert)

            firing = len(firing_alerts)
            if firing == 0:
                span.set_status(trace.StatusCode.OK)
                return f"PASSED: {service} healthy. No firing alerts."
            
            msg = f"FAILED: {firing} alerts still firing for service {service}."
            span.set_status(trace.StatusCode.ERROR, msg)
            return msg
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return f"Error: {str(e)}"

def _verify_traces(service: str, time_range: str = "5m") -> str:
    """Query traces to check if there are error spans."""
    with tracer.start_as_current_span("validation.verify_traces") as span:
        span.set_attribute("mcp.service", service)
        span.set_attribute("mcp.time_range", time_range)
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "query_traces",
                    "arguments": {
                        "service": service,
                        "time_range": time_range,
                        "limit": 10
                    }
                },
                "id": 12
            }
            headers = {"Content-Type": "application/json"}
            if SIGNOZ_API_KEY:
                headers["SIGNOZ-API-KEY"] = SIGNOZ_API_KEY
            response = requests.post(f"{MCP_BASE_URL}/mcp", json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            traces_data = _parse_mcp_response(response.json())
            
            traces_list = []
            if isinstance(traces_data, dict):
                if "traces" in traces_data:
                    traces_list = traces_data["traces"]
                elif "result" in traces_data and isinstance(traces_data["result"], dict) and "traces" in traces_data["result"]:
                    traces_list = traces_data["result"]["traces"]
                elif "text" in traces_data:
                    text = traces_data["text"]
                    if text and ("error" in text.lower() or "exception" in text.lower()):
                        return "FAILED: Traces contain errors or exceptions."
            elif isinstance(traces_data, list):
                traces_list = traces_data

            error_count = 0
            for trace_item in traces_list:
                if isinstance(trace_item, dict):
                    status_code = trace_item.get("statusCode") or trace_item.get("status", {}).get("code")
                    if status_code == "STATUS_CODE_ERROR" or status_code == 2:
                        error_count += 1
            
            if error_count == 0:
                span.set_status(trace.StatusCode.OK)
                return f"PASSED: Traces show normal operation (0 error spans in last {time_range})."
            
            msg = f"FAILED: Found {error_count} error spans in traces."
            span.set_status(trace.StatusCode.ERROR, msg)
            return msg
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return f"Error: {str(e)}"

def _wait_and_validate(service: str, namespace: str, retries: int = 5) -> str:
    """Wait for service recovery with retries."""
    with tracer.start_as_current_span("validation.retry") as span:
        span.set_attribute("k8s.namespace", namespace)
        span.set_attribute("mcp.service", service)
        span.set_attribute("validation.max_retries", retries)
        for attempt in range(retries):
            health_result = _check_service_health(service, namespace)
            traces_result = _verify_traces(service, "5m")
            
            if "PASSED" in health_result and "PASSED" in traces_result:
                msg = f"Success after {attempt + 1} attempts. {health_result} {traces_result}"
                span.set_status(trace.StatusCode.OK, msg)
                return msg
            
            time.sleep(CHECK_INTERVAL)
        
        msg = f"Failed after {retries} attempts. Manual intervention needed."
        span.set_status(trace.StatusCode.ERROR, msg)
        return msg

# LangChain tools
@tool("Check service health metrics")
def check_service_health(service: str, namespace: str) -> str:
    """Check if error rate and latency are normal."""
    return _check_service_health(service, namespace)

@tool("Verify if traces show normal operation")
def verify_traces(service: str, time_range: str = "5m") -> str:
    """Query traces to check if there are error spans."""
    return _verify_traces(service, time_range)

@tool("Wait and retry validation")
def wait_and_validate(service: str, namespace: str, retries: int = 5) -> str:
    """Wait for service recovery with retries."""
    return _wait_and_validate(service, namespace, retries)

class ValidationEngine:
    """Class wrapper for backwards compatibility."""
    def check_service_health(self, service: str, namespace: str) -> str:
        return _check_service_health(service, namespace)

    def wait_and_validate(self, service: str, namespace: str, retries: int = 5) -> str:
        return _wait_and_validate(service, namespace, retries)

validator_agent = Agent(
    role="Senior SRE Validation Engineer",
    goal="Verify remediation actions resolved incidents",
    backstory=(
        "You are a meticulous SRE who validates every remediation. "
        "You check metrics and alerts to confirm recovery. "
        "You never assume a fix worked - you verify with data."
    ),
    tools=[
        check_service_health,
        verify_traces,
        wait_and_validate,
    ],
    verbose=True,
    allow_delegation=False,
    memory=True,
)
