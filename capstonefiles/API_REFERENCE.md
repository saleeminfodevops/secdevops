# API Reference - Kubernetes Health Monitor

## Overview
The Health Monitor exposes two main HTTP interfaces:
- **Metrics API** (Port 8081): Prometheus-compatible metrics endpoint
- **Admin API** (Port 8080): Dashboard and control endpoints

---

## Metrics API (Port 8081)

### GET /metrics
Returns Prometheus-format metrics for all monitored resources.

**Request**:
```
GET /metrics HTTP/1.1
Host: health-monitor:8081
```

**Response** (200 OK):
```
# HELP k8s_node_health_status Node health status: 1=healthy, 0=degraded
# TYPE k8s_node_health_status gauge
k8s_node_health_status{node_name="worker-01",status="healthy"} 1
k8s_node_health_status{node_name="worker-02",status="healthy"} 1
k8s_node_health_status{node_name="worker-03",status="degraded"} 0

# HELP k8s_pod_health_status Pod health status: 1=ready, 0=not ready
# TYPE k8s_pod_health_status gauge
k8s_pod_health_status{namespace="default",pod_name="app-1",phase="Running"} 1
k8s_pod_health_status{namespace="default",pod_name="app-2",phase="Pending"} 0

# HELP k8s_pod_restart_count Total pod restarts
# TYPE k8s_pod_restart_count gauge
k8s_pod_restart_count{namespace="default",pod_name="app-1"} 2
k8s_pod_restart_count{namespace="default",pod_name="app-2"} 5

# HELP k8s_node_resource_utilization Node resource utilization
# TYPE k8s_node_resource_utilization gauge
k8s_node_resource_utilization{node_name="worker-01",resource_type="cpu"} 65
k8s_node_resource_utilization{node_name="worker-01",resource_type="memory"} 72
```

**Parameters**: None

**Notes**:
- This endpoint is scraped by Prometheus every 30 seconds
- Metrics are cumulative since pod startup
- All metric names start with `k8s_` prefix

---

## Admin API (Port 8080)

### GET /health
Health check endpoint for liveness/readiness probes.

**Request**:
```
GET /health HTTP/1.1
Host: health-monitor:8080
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:32:45Z",
  "uptime_seconds": 3600,
  "version": "1.0.0",
  "kubernetes_api": "connected",
  "prometheus": "connected"
}
```

**Response** (503 Service Unavailable):
```json
{
  "status": "unhealthy",
  "reason": "kubernetes_api_unreachable",
  "error": "connection timeout"
}
```

---

### GET /api/cluster-status
Returns overall cluster health summary.

**Request**:
```
GET /api/cluster-status HTTP/1.1
Host: health-monitor:8080
Accept: application/json
```

**Response** (200 OK):
```json
{
  "cluster_name": "production",
  "timestamp": "2024-01-15T14:32:45Z",
  "nodes": {
    "total": 50,
    "healthy": 48,
    "degraded": 2,
    "unhealthy": 0,
    "health_percentage": 96
  },
  "pods": {
    "total": 350,
    "running": 342,
    "pending": 5,
    "failed": 3,
    "ready_percentage": 97.7
  },
  "resources": {
    "cpu": {
      "available": "100",
      "used": "65.4",
      "utilization_percent": 65.4
    },
    "memory": {
      "available": "200Gi",
      "used": "142Gi",
      "utilization_percent": 71
    }
  },
  "issues": [
    {
      "type": "node_degraded",
      "severity": "warning",
      "node_name": "worker-07",
      "description": "Node has disk pressure condition"
    }
  ]
}
```

**Query Parameters**:
- `namespace` (optional): Filter by specific namespace
- `detailed` (optional, default=false): Include per-node/pod details

---

### GET /api/nodes
Get status of all nodes.

**Request**:
```
GET /api/nodes HTTP/1.1
Host: health-monitor:8080
```

**Response** (200 OK):
```json
{
  "nodes": [
    {
      "name": "worker-01",
      "role": "worker",
      "status": "Ready",
      "health": "healthy",
      "conditions": [
        {
          "type": "Ready",
          "status": "True",
          "last_transition": "2024-01-14T10:00:00Z"
        }
      ],
      "resources": {
        "cpu": {
          "capacity": "4",
          "allocatable": "3.5",
          "used": "2.1",
          "utilization_percent": 60
        },
        "memory": {
          "capacity": "8Gi",
          "allocatable": "7Gi",
          "used": "5.2Gi",
          "utilization_percent": 74.3
        }
      },
      "pods_running": 45
    }
  ],
  "summary": {
    "total_nodes": 50,
    "healthy_nodes": 48,
    "degraded_nodes": 2
  }
}
```

**Query Parameters**:
- `filter` (optional): Filter by status (Ready, NotReady, Unknown)

---

### GET /api/nodes/{node-name}
Get detailed status of specific node.

**Request**:
```
GET /api/nodes/worker-01 HTTP/1.1
Host: health-monitor:8080
```

**Response** (200 OK):
```json
{
  "name": "worker-01",
  "role": "worker",
  "status": "Ready",
  "health": "healthy",
  "api_version": "v1",
  "uid": "12345-abcde-67890",
  "created_at": "2023-06-01T12:00:00Z",
  "last_heartbeat": "2024-01-15T14:32:45Z",
  "conditions": [
    {
      "type": "Ready",
      "status": "True",
      "reason": "KubeletReady",
      "message": "kubelet is posting ready status",
      "last_transition": "2024-01-14T10:00:00Z"
    },
    {
      "type": "MemoryPressure",
      "status": "False",
      "last_transition": "2023-06-01T12:00:00Z"
    },
    {
      "type": "DiskPressure",
      "status": "False",
      "last_transition": "2023-06-01T12:00:00Z"
    }
  ],
  "allocatable": {
    "cpu": "3500m",
    "memory": "7Gi",
    "ephemeral_storage": "50Gi"
  },
  "capacity": {
    "cpu": "4",
    "memory": "8Gi",
    "ephemeral_storage": "100Gi"
  },
  "info": {
    "machine_id": "ec2-12345",
    "os": "linux",
    "kernel_version": "5.15.0"
  },
  "pods": [
    {
      "namespace": "default",
      "name": "app-pod-1",
      "phase": "Running"
    }
  ]
}
```

---

### GET /api/pods
Get status of all pods across cluster.

**Request**:
```
GET /api/pods?namespace=default&status=running HTTP/1.1
Host: health-monitor:8080
```

**Response** (200 OK):
```json
{
  "pods": [
    {
      "namespace": "default",
      "name": "app-1",
      "phase": "Running",
      "ready": true,
      "restart_count": 0,
      "containers": [
        {
          "name": "app",
          "state": "running",
          "restart_count": 0,
          "last_state": "terminated"
        }
      ],
      "node_name": "worker-01",
      "created_at": "2024-01-01T00:00:00Z",
      "start_time": "2024-01-15T14:30:00Z",
      "conditions": [
        {
          "type": "Ready",
          "status": "True"
        },
        {
          "type": "ContainersReady",
          "status": "True"
        }
      ]
    }
  ],
  "summary": {
    "total": 350,
    "running": 342,
    "pending": 5,
    "failed": 3
  }
}
```

**Query Parameters**:
- `namespace` (optional): Filter by namespace
- `status` (optional): Filter by phase (Running, Pending, Failed, Unknown, Succeeded)
- `node` (optional): Filter by node name
- `health` (optional): Filter by health (healthy, degraded, critical)

---

### GET /api/pods/{namespace}/{pod-name}
Get detailed status of specific pod.

**Request**:
```
GET /api/pods/default/app-1 HTTP/1.1
Host: health-monitor:8080
```

**Response** (200 OK):
```json
{
  "namespace": "default",
  "name": "app-1",
  "uid": "abc123",
  "phase": "Running",
  "ready": true,
  "restart_count": 0,
  "qos_class": "Burstable",
  "node_name": "worker-01",
  "host_ip": "10.0.1.5",
  "pod_ip": "10.244.0.1",
  "created_at": "2024-01-01T00:00:00Z",
  "start_time": "2024-01-15T14:30:00Z",
  "containers": [
    {
      "name": "app",
      "image": "myapp:1.0.0",
      "state": "running",
      "started": "2024-01-15T14:30:00Z",
      "restart_count": 0,
      "ready": true,
      "cpu": {
        "request": "100m",
        "limit": "500m"
      },
      "memory": {
        "request": "128Mi",
        "limit": "512Mi"
      }
    }
  ],
  "conditions": [
    {
      "type": "Initialized",
      "status": "True",
      "reason": "PodCompleted"
    },
    {
      "type": "Ready",
      "status": "True",
      "reason": "PodCompleted"
    }
  ],
  "health": {
    "status": "healthy",
    "issues": []
  }
}
```

---

### GET /api/actions
Get history of auto-healing actions.

**Request**:
```
GET /api/actions?limit=50&status=success HTTP/1.1
Host: health-monitor:8080
```

**Response** (200 OK):
```json
{
  "actions": [
    {
      "id": "action-001",
      "timestamp": "2024-01-15T14:32:45Z",
      "type": "pod_restart",
      "namespace": "default",
      "resource_name": "app-1",
      "resource_kind": "Pod",
      "status": "success",
      "reason": "CrashLoopBackOff",
      "duration_seconds": 2.5,
      "message": "Pod restarted successfully"
    },
    {
      "id": "action-002",
      "timestamp": "2024-01-15T14:25:30Z",
      "type": "pod_reschedule",
      "namespace": "production",
      "resource_name": "worker-db-1",
      "resource_kind": "Pod",
      "status": "success",
      "reason": "node_pressure",
      "duration_seconds": 1.8,
      "message": "Pod rescheduled to worker-05"
    },
    {
      "id": "action-003",
      "timestamp": "2024-01-15T14:20:15Z",
      "type": "pod_scale",
      "namespace": "production",
      "resource_name": "api-service",
      "resource_kind": "Deployment",
      "status": "success",
      "reason": "high_load",
      "duration_seconds": 3.2,
      "message": "Scaled from 5 to 8 replicas"
    }
  ],
  "summary": {
    "total_actions": 245,
    "success_count": 240,
    "failed_count": 5
  }
}
```

**Query Parameters**:
- `limit` (optional, default=50): Maximum number of actions to return
- `status` (optional): Filter by status (success, failed, pending)
- `type` (optional): Filter by action type (pod_restart, pod_reschedule, pod_scale)
- `namespace` (optional): Filter by namespace
- `since` (optional): ISO 8601 timestamp, return actions after this time

---

### POST /api/actions/execute
Manually trigger a self-healing action.

**Request**:
```
POST /api/actions/execute HTTP/1.1
Host: health-monitor:8080
Content-Type: application/json

{
  "action_type": "pod_restart",
  "namespace": "default",
  "pod_name": "app-1",
  "reason": "manual_trigger"
}
```

**Response** (202 Accepted):
```json
{
  "action_id": "action-004",
  "status": "pending",
  "timestamp": "2024-01-15T14:35:00Z",
  "message": "Action scheduled for execution"
}
```

**Response** (400 Bad Request):
```json
{
  "error": "invalid_action_type",
  "message": "Action type must be one of: pod_restart, pod_reschedule, pod_scale"
}
```

**Supported Actions**:
- `pod_restart`: Delete pod to trigger restart
- `pod_reschedule`: Evict pod for rescheduling
- `pod_scale`: Scale deployment replicas
- `node_cordon`: Cordon node to prevent scheduling

---

### GET /api/alerts
Get list of active alerts.

**Request**:
```
GET /api/alerts?severity=critical HTTP/1.1
Host: health-monitor:8080
```

**Response** (200 OK):
```json
{
  "alerts": [
    {
      "id": "alert-001",
      "name": "HighMemoryPressure",
      "severity": "warning",
      "state": "firing",
      "node_name": "worker-03",
      "message": "Node has elevated memory pressure",
      "started_at": "2024-01-15T14:30:00Z",
      "updated_at": "2024-01-15T14:32:45Z"
    },
    {
      "id": "alert-002",
      "name": "PodCrashLooping",
      "severity": "critical",
      "state": "firing",
      "pod_name": "auth-service-5d8f4",
      "namespace": "production",
      "message": "Pod is crash looping (5 restarts in 10 minutes)",
      "started_at": "2024-01-15T14:28:00Z",
      "updated_at": "2024-01-15T14:32:45Z"
    }
  ],
  "summary": {
    "total": 2,
    "critical": 1,
    "warning": 1
  }
}
```

**Query Parameters**:
- `severity` (optional): Filter by severity (critical, warning, info)
- `state` (optional): Filter by state (firing, resolved)

---

### GET /api/config
Get current configuration.

**Request**:
```
GET /api/config HTTP/1.1
Host: health-monitor:8080
```

**Response** (200 OK):
```json
{
  "version": "1.0.0",
  "cluster_name": "production",
  "health_check_interval": "30s",
  "self_healing": {
    "enabled": true,
    "max_actions_per_cycle": 5,
    "cooldown_period": "60s"
  },
  "thresholds": {
    "cpu_utilization": 85,
    "memory_utilization": 90,
    "disk_pressure": 75,
    "pod_restart_threshold": 5
  },
  "features": {
    "auto_scale_nodes": true,
    "auto_scale_pods": true,
    "auto_restart_pods": true,
    "pod_eviction": true
  },
  "notifications": {
    "slack": {
      "enabled": true,
      "webhook_configured": true
    }
  }
}
```

---

### PUT /api/config
Update configuration (admin only).

**Request**:
```
PUT /api/config HTTP/1.1
Host: health-monitor:8080
Content-Type: application/json
Authorization: Bearer <admin-token>

{
  "health_check_interval": "60s",
  "self_healing": {
    "enabled": false
  }
}
```

**Response** (200 OK):
```json
{
  "status": "updated",
  "changes": {
    "health_check_interval": "30s -> 60s",
    "self_healing.enabled": "true -> false"
  }
}
```

---

## Error Responses

All endpoints may return error responses with the following format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "status_code": 400,
  "timestamp": "2024-01-15T14:32:45Z"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `invalid_request` | 400 | Request format or parameters invalid |
| `not_found` | 404 | Requested resource not found |
| `unauthorized` | 401 | Authentication required |
| `forbidden` | 403 | Permission denied |
| `conflict` | 409 | Resource conflict (e.g., pod already restarting) |
| `rate_limited` | 429 | Too many requests |
| `internal_error` | 500 | Server error |
| `service_unavailable` | 503 | Service temporarily unavailable |

---

## Authentication

Admin endpoints (`POST`, `PUT`, `DELETE`) require authentication:

```bash
# Include bearer token in Authorization header
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X POST http://health-monitor:8080/api/actions/execute
```

Retrieve token from secret:
```bash
kubectl get secret health-monitor-admin -n monitoring \
  -o jsonpath='{.data.api-token}' | base64 -d
```

---

## Rate Limiting

- Default: 100 requests per minute per IP
- Burst: Up to 10 requests in 1-second window
- Returns `429 Too Many Requests` when exceeded

Headers in response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705337565
```

---

## Examples

### Get all unhealthy pods
```bash
curl http://health-monitor:8080/api/pods?health=degraded | jq .
```

### Restart a specific pod
```bash
curl -X POST http://health-monitor:8080/api/actions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "pod_restart",
    "namespace": "default",
    "pod_name": "app-1",
    "reason": "manual_intervention"
  }'
```

### Monitor health check metrics
```bash
kubectl port-forward -n monitoring svc/health-monitor 8081:8081
curl http://localhost:8081/metrics | grep k8s_
```

---

## SDK Support

SDKs available for:
- **Python**: `health-monitor-sdk` (PyPI)
- **Go**: `github.com/company/k8s-health-monitor/sdk`
- **Node.js**: `@company/health-monitor-sdk` (npm)

Installation:
```bash
# Python
pip install health-monitor-sdk

# Go
go get github.com/company/k8s-health-monitor/sdk

# Node.js
npm install @company/health-monitor-sdk
```

Example (Go):
```go
package main

import "github.com/company/k8s-health-monitor/sdk"

func main() {
    client := sdk.NewClient("http://health-monitor:8080")
    status, _ := client.GetClusterStatus(ctx)
    fmt.Printf("Cluster health: %d%%\n", status.HealthPercentage)
}
```

---

**API Version**: 1.0
**Last Updated**: 2024-01
**Base URL**: `http://health-monitor:8080` (or `http://health-monitor:8081/metrics`)
