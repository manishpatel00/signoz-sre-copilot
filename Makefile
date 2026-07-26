.PHONY: dev test cast demo logs clean install health

install:
	pip install -r requirements.txt

dev:
	foundryctl cast -f casting.yaml
	@echo "SigNoz UI: http://localhost:8080"
	@echo "MCP Server: http://localhost:8000"

forge:
	foundryctl forge -f casting.yaml

cast:
	foundryctl cast -f casting.yaml

test:
	pytest tests/ -v --tb=short

test-mcp:
	pytest tests/test_mcp_integration.py -v

test-remediation:
	pytest tests/test_remediation.py -v

demo:
	@echo "Triggering demo incident..."
	@kubectl apply -f tests/chaos/pod-failure.yaml 2>/dev/null || true
	@curl -X POST http://localhost:8085/webhook/alert \
	  -H "Content-Type: application/json" \
	  -d '{"alert_name":"demo-high-error-rate","labels":{"service_name":"demo-app","namespace":"hackathon-demo","severity":"warning"}}' || true

logs:
	@docker logs -f signoz-sre-copilot-sre-copilot-1 2>/dev/null || echo "Container not running"

clean:
	foundryctl clean -f casting.yaml 2>/dev/null || true
	docker compose -f pours/deployment/compose.yaml down -v 2>/dev/null || true
	rm -rf pours/

health:
	@echo "=== SigNoz Health ==="
	@curl -s http://localhost:8080/api/v1/health | jq . 2>/dev/null || echo "SigNoz not ready"
	@echo ""
	@echo "=== MCP Health ==="
	@curl -s http://localhost:8000/livez || echo "MCP not ready"
	@echo ""
	@echo "=== Copilot Health ==="
	@curl -s http://localhost:8085/health | jq . 2>/dev/null || echo "Copilot not ready"
