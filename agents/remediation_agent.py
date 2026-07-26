"""SigNoz SRE Copilot - Remediation Agent."""
import os
import json
import subprocess
import datetime
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
        "service.name": "sre-remediation-agent",
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

tracer = trace.get_tracer("remediation-agent")

DRY_RUN = os.getenv("REMEDIATION_DRY_RUN", "true").lower() == "true"
ALLOWED_NAMESPACES = [ns.strip() for ns in os.getenv("ALLOWED_NAMESPACES", "default,hackathon-demo").split(",") if ns.strip()]

# Expand KUBECONFIG path if it contains ~
if "KUBECONFIG" in os.environ:
    os.environ["KUBECONFIG"] = os.path.expanduser(os.environ["KUBECONFIG"])

def _restart_deployment(namespace: str, deployment: str) -> str:
    """Rolling restart of a K8s deployment."""
    with tracer.start_as_current_span("remediation.restart") as span:
        span.set_attribute("k8s.namespace", namespace)
        span.set_attribute("k8s.deployment", deployment)
        allowed = [ns.strip() for ns in os.getenv("ALLOWED_NAMESPACES", "default,hackathon-demo").split(",") if ns.strip()]
        dry_run = os.getenv("REMEDIATION_DRY_RUN", "true").lower() == "true"
        if namespace not in allowed:
            msg = f"BLOCKED: Namespace {namespace} not allowed"
            span.set_status(trace.StatusCode.ERROR, msg)
            return msg
        if dry_run:
            msg = f"[DRY RUN] Would restart {namespace}/{deployment}"
            span.set_status(trace.StatusCode.OK, msg)
            return msg
        try:
            now = datetime.datetime.utcnow().isoformat() + "Z"
            patch = json.dumps({"spec": {"template": {"metadata": {"annotations": {"kubectl.kubernetes.io/restartedAt": now}}}}})
            cmd = ["kubectl", "patch", "deployment", deployment, "-n", namespace, "--type", "merge", "-p", patch]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                span.set_status(trace.StatusCode.OK)
                return result.stdout
            else:
                span.set_status(trace.StatusCode.ERROR, result.stderr)
                return f"Failed: {result.stderr}"
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return f"Error: {str(e)}"

def _scale_deployment(namespace: str, deployment: str, replicas: int) -> str:
    """Scale a K8s deployment."""
    with tracer.start_as_current_span("remediation.scale") as span:
        span.set_attribute("k8s.namespace", namespace)
        span.set_attribute("k8s.deployment", deployment)
        span.set_attribute("k8s.replicas", replicas)
        allowed = [ns.strip() for ns in os.getenv("ALLOWED_NAMESPACES", "default,hackathon-demo").split(",") if ns.strip()]
        dry_run = os.getenv("REMEDIATION_DRY_RUN", "true").lower() == "true"
        if namespace not in allowed:
            msg = f"BLOCKED: Namespace {namespace} not allowed"
            span.set_status(trace.StatusCode.ERROR, msg)
            return msg
        if dry_run:
            msg = f"[DRY RUN] Would scale {namespace}/{deployment} to {replicas}"
            span.set_status(trace.StatusCode.OK, msg)
            return msg
        try:
            cmd = ["kubectl", "scale", "deployment", deployment, "-n", namespace, f"--replicas={replicas}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                span.set_status(trace.StatusCode.OK)
                return result.stdout
            else:
                span.set_status(trace.StatusCode.ERROR, result.stderr)
                return f"Failed: {result.stderr}"
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return f"Error: {str(e)}"

def _get_pod_status(namespace: str, deployment: str) -> str:
    """Get current pod status."""
    with tracer.start_as_current_span("remediation.pods") as span:
        span.set_attribute("k8s.namespace", namespace)
        span.set_attribute("k8s.deployment", deployment)
        try:
            cmd = ["kubectl", "get", "pods", "-n", namespace, "-l", f"app={deployment}", "-o", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                span.set_status(trace.StatusCode.OK)
                pods = json.loads(result.stdout)
                statuses = []
                for p in pods.get("items", []):
                    pod_name = p['metadata']['name']
                    phase = p['status']['phase']
                    container_statuses = p['status'].get('containerStatuses', [])
                    reason = ""
                    if container_statuses:
                        state = container_statuses[0].get('state', {})
                        waiting = state.get('waiting', {})
                        if waiting:
                            reason = f" ({waiting.get('reason', 'Waiting')})"
                    statuses.append(f"{pod_name}: {phase}{reason}")
                return "\n".join(statuses) if statuses else "No pods found"
            else:
                span.set_status(trace.StatusCode.ERROR, result.stderr)
                return f"Error: {result.stderr}"
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return f"Error: {str(e)}"

# LangChain tools
@tool("Restart a Kubernetes deployment")
def restart_deployment(namespace: str, deployment: str) -> str:
    """Rolling restart of a K8s deployment."""
    return _restart_deployment(namespace, deployment)

@tool("Scale a Kubernetes deployment")
def scale_deployment(namespace: str, deployment: str, replicas: int) -> str:
    """Scale a K8s deployment."""
    return _scale_deployment(namespace, deployment, replicas)

@tool("Get pod status for deployment")
def get_pod_status(namespace: str, deployment: str) -> str:
    """Get current pod status."""
    return _get_pod_status(namespace, deployment)

class RemediationEngine:
    """Class wrapper for backwards compatibility."""
    def restart_deployment(self, namespace: str, deployment: str) -> str:
        return _restart_deployment(namespace, deployment)

    def scale_deployment(self, namespace: str, deployment: str, replicas: int) -> str:
        return _scale_deployment(namespace, deployment, replicas)

    def get_pod_status(self, namespace: str, deployment: str) -> str:
        return _get_pod_status(namespace, deployment)

# Configure LLM dynamically
agent_llm = None
if os.getenv("GEMINI_API_KEY"):
    agent_llm = LLM(
        model="gemini/gemini-2.0-flash",
        api_key=os.getenv("GEMINI_API_KEY")
    )

remediation_agent = Agent(
    role="Senior SRE Remediation Engineer",
    goal="Execute safe infrastructure remediation actions",
    backstory=(
        "You are an expert SRE who specializes in incident remediation. "
        "You have deep knowledge of Kubernetes and Helm. "
        "You always verify state before acting. "
        "You prefer rolling restarts. You never delete data."
    ),
    tools=[
        restart_deployment,
        scale_deployment,
        get_pod_status,
    ],
    verbose=True,
    allow_delegation=False,
    memory=True,
    llm=agent_llm,
)
