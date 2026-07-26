"""Unit tests for remediation safety."""
# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch
from agents.remediation_agent import RemediationEngine

class TestRemediationSafety:
    def test_dry_run_mode(self):
        with patch.dict("os.environ", {"REMEDIATION_DRY_RUN": "true"}):
            engine = RemediationEngine()
            result = engine.restart_deployment("default", "test-app")
            assert "[DRY RUN]" in result

    def test_namespace_blocking(self):
        with patch.dict("os.environ", {"ALLOWED_NAMESPACES": "default,hackathon"}):
            engine = RemediationEngine()
            result = engine.restart_deployment("production", "test-app")
            assert "BLOCKED" in result

    def test_allowed_namespace(self):
        with patch.dict("os.environ", {"ALLOWED_NAMESPACES": "default,hackathon", "REMEDIATION_DRY_RUN": "true"}):
            engine = RemediationEngine()
            result = engine.restart_deployment("hackathon", "test-app")
            assert "BLOCKED" not in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
