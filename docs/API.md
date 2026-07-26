# API Documentation

## Endpoints

### GET /health
Health check.

**Response:**
```json
{"status": "healthy", "service": "sre-copilot"}
```

### POST /webhook/alert
Receive SigNoz alert webhooks.

**Request:**
```json
{
  "alert_name": "high-error-rate",
  "labels": {
    "service_name": "my-service",
    "namespace": "default",
    "severity": "critical"
  }
}
```

**Response:**
```json
{
  "status": "processing",
  "report": {
    "incident_id": "...",
    "status": "resolved"
  }
}
```

### GET /incident/report/<incident_id>
Get incident report.

**Response:**
```json
{
  "incident_id": "...",
  "service": "my-service",
  "status": "resolved"
}
```
