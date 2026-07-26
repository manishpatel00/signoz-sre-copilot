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
# pyrefly: ignore [missing-import]
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

import time

def _get_start_end_ms(time_range: str):
    try:
        unit = time_range[-1]
        val = int(time_range[:-1])
    except Exception:
        unit = "h"
        val = 1
    
    multiplier = 60
    if unit == "h":
        multiplier = 3600
    elif unit == "d":
        multiplier = 86400
    
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - (val * multiplier * 1000)
    return start_ms, end_ms

def _query_traces(service: str, time_range: str = "1h", min_duration_ms: int = 0) -> str:
    """Query SigNoz traces via MCP."""
    with tracer.start_as_current_span("mcp.query_traces") as span:
        span.set_attribute("mcp.service", service)
        span.set_attribute("mcp.time_range", time_range)
        span.set_attribute("mcp.min_duration_ms", min_duration_ms)
        try:
            arguments = {
                "service": service,
                "timeRange": time_range
            }
            if min_duration_ms > 0:
                arguments["minDuration"] = str(min_duration_ms * 1_000_000)
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "signoz_search_traces",
                    "arguments": arguments
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
            start_ms, end_ms = _get_start_end_ms(time_range)
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "signoz_execute_builder_query",
                    "arguments": {
                        "query": {
                            "compositeQuery": {
                                "queryType": "promql",
                                "panelType": "graph",
                                "queries": [
                                    {
                                        "name": "A",
                                        "query": promql,
                                        "legend": ""
                                    }
                                ]
                            },
                            "start": start_ms,
                            "end": end_ms,
                            "requestType": "time_series"
                        }
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
            arguments = {
                "service": service,
                "timeRange": time_range,
                "limit": limit
            }
            if query:
                arguments["searchText"] = query
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "signoz_search_logs",
                    "arguments": arguments
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
                    "name": "signoz_list_alerts",
                    "arguments": {
                        "active": True,
                        "silenced": False,
                        "inhibited": False
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
if os.getenv("GROQ_API_KEY"):
    agent_llm = LLM(
        model="groq/llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY")
    )
elif os.getenv("GEMINI_API_KEY"):
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
    memory=False,
    llm=agent_llm,
)
