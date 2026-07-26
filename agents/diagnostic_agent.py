"""SigNoz SRE Copilot - Diagnostic Agent."""
import os
import json
import requests
from dotenv import load_dotenv
from crewai import Agent, LLM
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
        "service.name": "sre-diagnostic-agent",
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

tracer = trace.get_tracer("diagnostic-agent")

MCP_BASE_URL = os.getenv("SIGNOZ_MCP_URL", "http://localhost:8000")
SIGNOZ_API_KEY = os.getenv("SIGNOZ_API_KEY", "")

def _parse_mcp_response(response_json: dict) -> str:
    """Safely extract content from standard JSON-RPC 2.0 response or return direct JSON."""
    result = response_json.get("result", {})
    if isinstance(result, dict) and "content" in result:
        content = result.get("content", [])
        if isinstance(content, list) and len(content) > 0:
            item = content[0]
            if isinstance(item, dict) and "text" in item:
                return item["text"]
    return json.dumps(response_json, indent=2)

def _query_traces(service: str, time_range: str = "1h", min_duration_ms: int = 0) -> str:
    """Query SigNoz traces via MCP."""
    with tracer.start_as_current_span("mcp.query_traces") as span:
        span.set_attribute("mcp.service", service)
        span.set_attribute("mcp.time_range", time_range)
        span.set_attribute("mcp.min_duration_ms", min_duration_ms)
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "query_traces",
                    "arguments": {
                        "service": service,
                        "time_range": time_range,
                        "min_duration_ms": min_duration_ms
                    }
                },
                "id": 1
            }
            headers = {"Content-Type": "application/json"}
            if SIGNOZ_API_KEY:
                headers["SIGNOZ-API-KEY"] = SIGNOZ_API_KEY
            response = requests.post(f"{MCP_BASE_URL}/mcp", json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            span.set_status(trace.StatusCode.OK)
            return _parse_mcp_response(response.json())
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return f"Error: {str(e)}"

def _query_metrics(promql: str, time_range: str = "1h") -> str:
    """Execute PromQL query against SigNoz."""
    with tracer.start_as_current_span("mcp.query_metrics") as span:
        span.set_attribute("mcp.promql", promql)
        span.set_attribute("mcp.time_range", time_range)
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "query_metrics",
                    "arguments": {
                        "query": promql,
                        "time_range": time_range
                    }
                },
                "id": 2
            }
            headers = {"Content-Type": "application/json"}
            if SIGNOZ_API_KEY:
                headers["SIGNOZ-API-KEY"] = SIGNOZ_API_KEY
            response = requests.post(f"{MCP_BASE_URL}/mcp", json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            span.set_status(trace.StatusCode.OK)
            return _parse_mcp_response(response.json())
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return f"Error: {str(e)}"

def _query_logs(service: str, query: str = "", time_range: str = "1h", limit: int = 100) -> str:
    """Search logs in SigNoz."""
    with tracer.start_as_current_span("mcp.query_logs") as span:
        span.set_attribute("mcp.service", service)
        span.set_attribute("mcp.query", query)
        span.set_attribute("mcp.time_range", time_range)
        span.set_attribute("mcp.limit", limit)
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "query_logs",
                    "arguments": {
                        "service": service,
                        "query": query,
                        "time_range": time_range,
                        "limit": limit
                    }
                },
                "id": 3
            }
            headers = {"Content-Type": "application/json"}
            if SIGNOZ_API_KEY:
                headers["SIGNOZ-API-KEY"] = SIGNOZ_API_KEY
            response = requests.post(f"{MCP_BASE_URL}/mcp", json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            span.set_status(trace.StatusCode.OK)
            return _parse_mcp_response(response.json())
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return f"Error: {str(e)}"

def _get_active_alerts() -> str:
    """Fetch firing alerts from SigNoz."""
    with tracer.start_as_current_span("mcp.get_alerts") as span:
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "get_alerts",
                    "arguments": {
                        "state": "firing"
                    }
                },
                "id": 4
            }
            headers = {"Content-Type": "application/json"}
            if SIGNOZ_API_KEY:
                headers["SIGNOZ-API-KEY"] = SIGNOZ_API_KEY
            response = requests.post(f"{MCP_BASE_URL}/mcp", json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            span.set_status(trace.StatusCode.OK)
            return _parse_mcp_response(response.json())
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return f"Error: {str(e)}"

# LangChain tools
@tool("Query SigNoz traces for service")
def query_traces(service: str, time_range: str = "1h", min_duration_ms: int = 0) -> str:
    """Query SigNoz traces via MCP."""
    return _query_traces(service, time_range, min_duration_ms)

@tool("Query SigNoz metrics using PromQL")
def query_metrics(promql: str, time_range: str = "1h") -> str:
    """Execute PromQL query against SigNoz."""
    return _query_metrics(promql, time_range)

@tool("Query SigNoz logs")
def query_logs(service: str, query: str = "", time_range: str = "1h", limit: int = 100) -> str:
    """Search logs in SigNoz."""
    return _query_logs(service, query, time_range, limit)

@tool("Get active alerts from SigNoz")
def get_active_alerts() -> str:
    """Fetch firing alerts from SigNoz."""
    return _get_active_alerts()

class SigNozMCPTools:
    """Class wrapper for backwards compatibility."""
    def query_traces(self, service: str, time_range: str = "1h", min_duration_ms: int = 0) -> str:
        return _query_traces(service, time_range, min_duration_ms)

    def query_metrics(self, promql: str, time_range: str = "1h") -> str:
        return _query_metrics(promql, time_range)

    def query_logs(self, service: str, query: str = "", time_range: str = "1h", limit: int = 100) -> str:
        return _query_logs(service, query, time_range, limit)

    def get_active_alerts(self) -> str:
        return _get_active_alerts()

# Configure LLM dynamically
agent_llm = None
if os.getenv("GEMINI_API_KEY"):
    agent_llm = LLM(
        model="gemini/gemini-2.0-flash",
        api_key=os.getenv("GEMINI_API_KEY")
    )

diagnostic_agent = Agent(
    role="Senior SRE Diagnostic Engineer",
    goal="Identify root cause of infrastructure incidents using SigNoz observability data",
    backstory=(
        "You are an expert SRE with 15 years of experience in distributed systems. "
        "You specialize in root cause analysis using traces, metrics, and logs. "
        "You always verify hypotheses with data before concluding. "
        "You use the SigNoz MCP server to query observability data. "
        "You never guess - you always look at the data first."
    ),
    tools=[
        query_traces,
        query_metrics,
        query_logs,
        get_active_alerts,
    ],
    verbose=True,
    allow_delegation=False,
    memory=True,
    llm=agent_llm,
)
