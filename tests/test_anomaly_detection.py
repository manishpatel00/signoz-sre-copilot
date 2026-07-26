"""Tests for Isolation Forest integration."""

# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from opentelemetry.sdk.trace import TracerProvider
# pyrefly: ignore [missing-import]
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
# pyrefly: ignore [missing-import]
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

def test_anomaly_span_tagging():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("test")
    with tracer.start_as_current_span("test-span") as span:
        span.set_attribute("anomaly.is_anomaly", "true")
        span.set_attribute("anomaly.isolation_score", 0.85)
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].attributes["anomaly.is_anomaly"] == "true"
    assert spans[0].attributes["anomaly.isolation_score"] == 0.85

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
