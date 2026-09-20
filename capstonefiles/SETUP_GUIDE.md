# Setup Guide - Kubernetes Health Monitoring System

## Prerequisites

### Required Tools
- Kubernetes cluster v1.20+
- kubectl configured with cluster access
- Helm 3.0+
- Docker (for building custom images)
- Git
- Go 1.21+ (for development)

### Cluster Requirements
- Minimum 3 master nodes
- Minimum 10 worker nodes
- 100GB available persistent storage
- Network connectivity between all nodes

### Permissions
Your Kubernetes user must have cluster-admin rights to install the monitoring system.

---

## Step 1: Clone Repository and Dependencies

```bash
# Clone the health monitoring project
git clone https://github.com/company/k8s-health-monitor.git
cd k8s-health-monitor

# Install Go dependencies
go mod download

# Create Docker registry secret (if using private registry)
kubectl create secret docker-registry regcred \
  --docker-server=registry.company.com \
  --docker-username=<username> \
  --docker-password=<token> \
  --docker-email=ops@company.com
```

---

## Step 2: Create Monitoring Namespace

```bash
# Create namespace for all monitoring components
kubectl create namespace monitoring

# Label the namespace for pod security policies
kubectl label namespace monitoring pod-security.kubernetes.io/enforce=baseline

# Set resource quotas to prevent monitoring from consuming entire cluster
kubectl apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: monitoring-quota
  namespace: monitoring
spec:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    limits.cpu: "20"
    limits.memory: "40Gi"
EOF
```

---

## Step 3: Install Prometheus Stack

```bash
# Add Prometheus community Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack (includes Prometheus, Grafana, Alertmanager)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values config/prometheus-values.yaml \
  --wait

# Verify installation
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

### Configuration: `config/prometheus-values.yaml`

```yaml
prometheus:
  prometheusSpec:
    retention: 30d
    retentionSize: "50GB"
    
    resources:
      requests:
        cpu: 500m
        memory: 2Gi
      limits:
        cpu: 2
        memory: 4Gi
    
    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 50Gi
    
    serviceMonitorSelectorNilUsesHelmValues: false
    podMonitorSelectorNilUsesHelmValues: false
    
    additionalScrapeConfigs: []

grafana:
  enabled: true
  adminPassword: "GENERATE_SECURE_PASSWORD"
  persistence:
    enabled: true
    size: 10Gi
  
  datasources:
    datasources.yaml:
      apiVersion: 1
      datasources:
      - name: Prometheus
        type: prometheus
        url: http://prometheus-kube-prometheus-prometheus:9090
        isDefault: true

alertmanager:
  enabled: true
  config:
    global:
      resolve_timeout: 5m
    route:
      receiver: 'default'
      group_by: ['alertname', 'cluster']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 12h
    receivers:
    - name: 'default'
```

---

## Step 4: Build and Push Custom Health Monitor Image

```bash
# Build Docker image
docker build -t registry.company.com/k8s-health-monitor:v1.0.0 .

# Push to registry
docker push registry.company.com/k8s-health-monitor:v1.0.0

# Or build with Kaniko in cluster
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kaniko
  namespace: monitoring
---
apiVersion: batch/v1
kind: Job
metadata:
  name: build-health-monitor
  namespace: monitoring
spec:
  template:
    spec:
      serviceAccountName: kaniko
      containers:
      - name: kaniko
        image: gcr.io/kaniko-project/executor:latest
        args:
        - --dockerfile=Dockerfile
        - --context=git://github.com/company/k8s-health-monitor.git#main
        - --destination=registry.company.com/k8s-health-monitor:v1.0.0
EOF
```

---

## Step 5: Deploy Health Monitor with Helm

```bash
# Create ServiceAccount and RBAC rules
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: health-monitor
  namespace: monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: health-monitor
rules:
- apiGroups: [""]
  resources: ["nodes", "pods", "services"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "statefulsets", "daemonsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["delete", "create"]
- apiGroups: ["policy"]
  resources: ["poddisruptionbudgets"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: health-monitor
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: health-monitor
subjects:
- kind: ServiceAccount
  name: health-monitor
  namespace: monitoring
EOF

# Install health monitor Helm chart
helm install health-monitor ./helm/k8s-health-monitor \
  --namespace monitoring \
  --values helm/values.yaml \
  --wait
```

### Chart Values: `helm/values.yaml`

```yaml
replicaCount: 2

image:
  repository: registry.company.com/k8s-health-monitor
  tag: v1.0.0
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8080
  metricsPort: 8081

config:
  healthCheckInterval: 30s
  clusterName: production
  kubernetesAPI:
    timeout: 10s
  
  alerts:
    criticalThreshold: 5
    warningThreshold: 2
  
  actions:
    enabled: true
    maxActionsPerCycle: 5
    cooldownPeriod: 60s

resources:
  requests:
    cpu: 250m
    memory: 512Mi
  limits:
    cpu: 500m
    memory: 1Gi

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - health-monitor
        topologyKey: kubernetes.io/hostname
```

---

## Step 6: Configure Prometheus Scraping

```bash
# Create ServiceMonitor for health monitor
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: health-monitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: health-monitor
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
EOF
```

---

## Step 7: Configure Alerts

```bash
# Create PrometheusRule for alerting
kubectl apply -f config/alert-rules.yaml

# Verify rules are loaded
kubectl logs -n monitoring prometheus-kube-prometheus-prometheus-0 | grep "alert"
```

---

## Step 8: Setup Slack Notifications

```bash
# Create Slack webhook (Steps in Slack):
# 1. Go to api.slack.com/apps
# 2. Create New App > From scratch
# 3. Enable "Incoming Webhooks"
# 4. Add webhook to desired channel
# 5. Copy webhook URL

# Create secret with Slack webhook
kubectl create secret generic slack-webhook \
  --from-literal=webhook-url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL' \
  -n monitoring

# Update Alertmanager config with webhook
kubectl patch alertmanager alertmanager-kube-prometheus-alertmanager \
  -n monitoring \
  --type merge \
  -p '{"spec":{"slack":{"webhookUrl":"https://hooks.slack.com/services/YOUR/WEBHOOK/URL"}}}'
```

---

## Step 9: Access Dashboards

### Prometheus UI
```bash
# Port forward to access Prometheus
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# Access at http://localhost:9090
```

### Grafana
```bash
# Port forward to Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Access at http://localhost:3000
# Default credentials: admin / (password from values.yaml)
```

### Health Monitor Dashboard
```bash
# Port forward to health monitor
kubectl port-forward -n monitoring svc/health-monitor 8080:8080

# Access at http://localhost:8080/dashboard
```

---

## Step 10: Verify Installation

```bash
# Check all pods are running
kubectl get pods -n monitoring

# Verify Prometheus is scraping targets
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Visit http://localhost:9090/targets

# Check for any errors in logs
kubectl logs -n monitoring -l app=health-monitor --tail=50

# Query a test metric
kubectl exec -it -n monitoring <prometheus-pod> -- \
  promtool query instant 'up{job="kubernetes-apiservers"}'
```

---

## Post-Installation Configuration

### Set Resource Limits
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: monitoring-compute
  namespace: monitoring
spec:
  hard:
    requests.cpu: "8"
    requests.memory: "16Gi"
    limits.cpu: "16"
    limits.memory: "32Gi"
    pods: "100"
EOF
```

### Configure Network Policies
```bash
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: monitoring-deny-ingress
  namespace: monitoring
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
EOF
```

### Enable Pod Disruption Budgets
```bash
kubectl apply -f - <<EOF
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: health-monitor-pdb
  namespace: monitoring
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: health-monitor
EOF
```

---

## Troubleshooting Installation

### Prometheus not scraping metrics
```bash
# Check Prometheus targets
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring
# Visit http://localhost:9090/targets
# Look for "Unhealthy" status and error messages
```

### Alertmanager not sending to Slack
```bash
# Verify webhook secret
kubectl get secret slack-webhook -n monitoring -o yaml

# Check Alertmanager logs
kubectl logs alertmanager-kube-prometheus-alertmanager-0 -n monitoring

# Test webhook manually
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test"}' \
  YOUR_WEBHOOK_URL
```

### High memory/CPU usage
```bash
# Check resource usage
kubectl top pods -n monitoring

# Adjust retention in Prometheus values
# Reduce retention.size or retention to free up space
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values config/prometheus-values.yaml
```

---

## Uninstall

```bash
# Remove all components
helm uninstall prometheus -n monitoring
helm uninstall health-monitor -n monitoring
kubectl delete namespace monitoring
```

---

## Security Hardening

### Network Security
- Restrict Prometheus access to authenticated users
- Enable TLS for all component communication
- Use network policies to limit pod-to-pod traffic

### RBAC
- Use service accounts with minimal required permissions
- Regularly audit RBAC rules
- Implement pod security policies

### Data Protection
- Enable encryption at rest for persistent volumes
- Backup Prometheus and Grafana data regularly
- Implement audit logging for all administrative actions

---

**Next Steps**: Review the [Usage Guide](USAGE.md) to start monitoring your cluster.
