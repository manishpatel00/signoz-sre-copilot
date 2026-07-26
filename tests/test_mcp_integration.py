"""Integration tests for SigNoz MCP."""
import os
import pytest
import requests

MCP_URL = os.getenv("SIGNOZ_MCP_URL", "http://localhost:8000")
SIGNOZ_API_KEY = os.getenv("SIGNOZ_API_KEY", "")

class TestMCPIntegration:
    @pytest.fixture(autouse=True)
    def check_mcp_running(self):
        try:
            response = requests.get(f"{MCP_URL}/livez", timeout=2)
            if response.status_code != 200:
                pytest.skip("MCP server not running or unhealthy")
        except Exception:
            pytest.skip("MCP server not reachable")

    def test_mcp_health(self):
        response = requests.get(f"{MCP_URL}/livez", timeout=10)
        assert response.status_code == 200

    def test_mcp_traces_query(self):
        payload = {
            "jsonrpc": "2.0", "method": "tools/call",
            "params": {"name": "query_traces", "arguments": {
                "service": "sre-copilot-orchestrator", "time_range": "1h", "limit": 10
            }}, "id": 1
        }
        headers = {"Content-Type": "application/json"}
        if SIGNOZ_API_KEY:
            headers["SIGNOZ-API-KEY"] = SIGNOZ_API_KEY
        response = requests.post(f"{MCP_URL}/mcp", json=payload, headers=headers, timeout=30)
        assert response.status_code == 200

    def test_mcp_metrics_query(self):
        payload = {
            "jsonrpc": "2.0", "method": "tools/call",
            "params": {"name": "query_metrics", "arguments": {"query": "up", "time_range": "5m"}},
            "id": 2
        }
        headers = {"Content-Type": "application/json"}
        if SIGNOZ_API_KEY:
            headers["SIGNOZ-API-KEY"] = SIGNOZ_API_KEY
        response = requests.post(f"{MCP_URL}/mcp", json=payload, headers=headers, timeout=30)
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
