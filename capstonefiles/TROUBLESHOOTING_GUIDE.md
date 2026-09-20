# Troubleshooting Guide - Kubernetes Health Monitoring System

## Common Issues and Solutions

---

## Issue 1: Health Monitor Pod Not Starting

### Symptoms
- Pod stuck in `Pending`, `CrashLoopBackOff`, or `ImagePullBackOff` state
- `kubectl get pods -n monitoring` shows unhealthy status

### Diagnosis Steps

```bash
# Check pod status
kubectl get pods -n monitoring | grep health-monitor

# View pod events
kubectl describe pod -n monitoring <pod-name>

# Check logs
kubectl logs -n monitoring -l app=health-monitor --all-containers=true --tail=100

# Check resource availability
kubectl top nodes
kubectl describe nodes | grep -A 5 "Allocated resources"
```

### Common Causes and Solutions

#### ImagePullBackOff
```bash
# Issue: Docker image not found or not accessible
# Solution: Verify image exists and is accessible
docker pull registry.company.com/k8s-health-monitor:v1.0.0

# Check image pull secrets
kubectl get secrets -n monitoring | grep regcred

# Verify image in values.yaml
helm get values health-monitor -n monitoring | grep image
```

#### CrashLoopBackOff
```bash
# Issue: Container crashes immediately on startup
# Solution: Check logs for errors
kubectl logs -n monitoring <pod-name> --previous

# Common causes:
# 1. Kubernetes API unreachable
# 2. Missing service account permissions
# 3. Configuration file errors

# Verify RBAC
kubectl get clusterrole health-monitor
kubectl get clusterrolebinding health-monitor
```

#### Pending Status
```bash
# Issue: Pod cannot be scheduled
# Solution: Check node resources and taints
kubectl describe nodes | grep -A 10 "Taints:"

# Check for node selectors
kubectl get pod -n monitoring <pod-name> -o yaml | grep nodeSelector

# Verify PVC is bound (if using persistent storage)
kubectl get pvc -n monitoring
kubectl describe pvc -n monitoring <pvc-name>
```

---

## Issue 2: Prometheus Not Collecting Metrics

### Symptoms
- Prometheus scrape count not increasing
- "No data" error in Prometheus UI
- Graph queries return empty results

### Diagnosis Steps

```bash
# Access Prometheus UI
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Visit http://localhost:9090

# Check targets in Prometheus
# 1. Go to Status > Targets
# 2. Look for "Unhealthy" targets
# 3. Check error messages

# Check scrape configuration
kubectl get prometheus -n monitoring -o yaml | grep -A 20 "scrapeConfigs:"

# Check ServiceMonitor resources
kubectl get servicemonitor -n monitoring
kubectl describe servicemonitor -n monitoring health-monitor
```

### Common Causes and Solutions

#### Targets show "Down"
```bash
# Issue: Service endpoints not accessible
# Solution: Verify service exists and has endpoints
kubectl get svc -n monitoring health-monitor
kubectl get endpoints -n monitoring health-monitor

# Check if metrics port is open
kubectl exec -it -n monitoring <health-monitor-pod> -- \
  nc -zv localhost 8081

# Verify health monitor is exposing metrics
kubectl port-forward -n monitoring <health-monitor-pod> 8081:8081
curl http://localhost:8081/metrics
```

#### ServiceMonitor not recognized
```bash
# Issue: Prometheus not using ServiceMonitor
# Solution: Verify CRD is installed
kubectl get crds | grep servicemonitor

# Check Prometheus operator logs
kubectl logs -n monitoring deployment/prometheus-operator

# Verify RBAC for Prometheus operator
kubectl get clusterrolebinding | grep prometheus

# Ensure ServiceMonitor labels match Prometheus selector
kubectl get prometheus -n monitoring -o yaml | \
  grep -A 5 "serviceMonitorSelector:"
```

#### High cardinality metrics
```bash
# Issue: Too many unique metric combinations
# Solution: Implement relabeling to reduce cardinality
kubectl edit prometheus -n monitoring

# Add metric relabeling rules:
spec:
  prometheus:
    prometheusSpec:
      metricRelabelings:
      - source_labels: [__name__]
        regex: 'k8s_pod_.*'
        action: keep
```

---

## Issue 3: Alertmanager Not Sending Notifications

### Symptoms
- Alerts firing in Prometheus but no Slack messages
- Alertmanager shows "Error" in Status page

### Diagnosis Steps

```bash
# Check Alertmanager status
kubectl port-forward -n monitoring svc/alertmanager-kube-prometheus-alertmanager 9093:9093
# Visit http://localhost:9093

# Check Alertmanager logs
kubectl logs -n monitoring -l app.kubernetes.io/name=alertmanager --tail=50

# Verify secret exists
kubectl get secret -n monitoring | grep slack

# Check alert rules are loaded
kubectl logs -n monitoring prometheus-kube-prometheus-prometheus-0 | \
  grep "alert_rules"

# Test Prometheus rule evaluation
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Go to Alerts tab, check rule evaluation
```

### Common Causes and Solutions

#### Slack webhook invalid
```bash
# Issue: Webhook URL incorrect or expired
# Solution: Regenerate and update webhook
kubectl delete secret slack-webhook -n monitoring
kubectl create secret generic slack-webhook \
  --from-literal=webhook-url='https://hooks.slack.com/services/NEW/WEBHOOK/URL' \
  -n monitoring

# Restart Alertmanager to pick up new secret
kubectl rollout restart statefulset alertmanager-kube-prometheus-alertmanager -n monitoring

# Test webhook manually
WEBHOOK_URL=$(kubectl get secret slack-webhook -n monitoring -o jsonpath='{.data.webhook-url}' | base64 -d)
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test from health monitor"}' \
  $WEBHOOK_URL
```

#### Alert routing misconfigured
```bash
# Issue: Alerts routed to wrong receiver
# Solution: Check Alertmanager config
kubectl get alertmanager -n monitoring -o yaml | grep -A 30 "config:"

# Test alert routing with amtool
kubectl exec -it -n monitoring alertmanager-kube-prometheus-alertmanager-0 -- \
  amtool config routes

# Temporarily disable grouping to debug
kubectl edit alertmanager alertmanager-kube-prometheus-alertmanager -n monitoring
# Set group_wait: 0s and group_interval: 0s for immediate alerts
```

#### Alerts not being generated
```bash
# Issue: Alert rules not evaluating to "firing"
# Solution: Check alert rule conditions
kubectl get prometheusrule -n monitoring
kubectl describe prometheusrule -n monitoring health-monitor-alerts

# Manually query the alert condition
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Go to Graph tab and test the PromQL query from the alert

# Check alert rule syntax
kubectl exec -it -n monitoring prometheus-kube-prometheus-prometheus-0 -- \
  cat /etc/prometheus/rules/prometheus-kube-prometheus-*.yaml | \
  promtool check rules /dev/stdin
```

---

## Issue 4: High Resource Consumption

### Symptoms
- Prometheus OOM kills
- Slow dashboard queries
- Node CPU/Memory spike

### Diagnosis Steps

```bash
# Check resource usage
kubectl top pods -n monitoring --sort-by=memory
kubectl top pods -n monitoring --sort-by=cpu

# Check storage usage
kubectl exec -it -n monitoring prometheus-kube-prometheus-prometheus-0 -- \
  df -h /prometheus

# View Prometheus memory usage
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Visit http://localhost:9090/graph
# Query: process_resident_memory_bytes{job="prometheus"}

# Check metric cardinality
kubectl exec -it -n monitoring prometheus-kube-prometheus-prometheus-0 -- \
  promtool query instant 'count(count by (__name__) ({{__name__=~".+"}}))'
```

### Common Causes and Solutions

#### Excessive metric cardinality
```bash
# Issue: Too many unique metric combinations
# Solution: Reduce scraped metrics
kubectl get servicemonitor -n monitoring -o yaml | grep metricRelabelings

# Add relabeling to drop unnecessary metrics
kubectl edit prometheus -n monitoring
# Add to spec.prometheus.prometheusSpec:
metricRelabelings:
- source_labels: [__name__]
  regex: 'kubernetes_.*|kube_pod_container_status.*'
  action: drop
```

#### Long retention period
```bash
# Issue: Storing too much data
# Solution: Reduce retention
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --set prometheus.prometheusSpec.retention=7d \
  --set prometheus.prometheusSpec.retentionSize=50GB

# Clear existing data (optional)
kubectl delete pvc prometheus-kube-prometheus-prometheus-db-prometheus-kube-prometheus-prometheus-0 -n monitoring
kubectl rollout restart statefulset prometheus-kube-prometheus-prometheus -n monitoring
```

#### Slow queries
```bash
# Issue: Dashboard loading slowly
# Solution: Optimize Grafana queries
# 1. Open query in Grafana
# 2. Increase step parameter if appropriate
# 3. Use rate() for counter metrics
# 4. Add range selector [1m] to limit lookback

# Check Prometheus query performance
# Visit http://localhost:9090/graph
# Slow queries tab shows query execution times
```

---

## Issue 5: Grafana Dashboard Not Displaying Data

### Symptoms
- "No data" error in Grafana
- Graph shows "loading..." indefinitely
- Wrong data displayed

### Diagnosis Steps

```bash
# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Login with admin credentials

# Check data source connection
# 1. Configuration > Data Sources > Prometheus
# 2. Click "Test"
# 3. Look for error messages

# Check Grafana logs
kubectl logs -n monitoring deployment/prometheus-grafana

# Verify database connectivity
kubectl exec -it -n monitoring deployment/prometheus-grafana -- \
  grafana-cli admin reset-admin-password "newpassword"
```

### Common Causes and Solutions

#### Data source connection failed
```bash
# Issue: Grafana cannot reach Prometheus
# Solution: Verify URL and credentials
kubectl get svc -n monitoring | grep prometheus

# Check Prometheus service DNS name
nslookup prometheus-kube-prometheus-prometheus.monitoring

# Update data source URL if needed
kubectl edit configmap prometheus-grafana-datasources -n monitoring
```

#### Query syntax errors
```bash
# Issue: PromQL query incorrect
# Solution: Test query in Prometheus first
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Test query in http://localhost:9090/graph

# Common mistakes:
# - Using wrong metric name
# - Missing labels in group by
# - Incorrect rate() usage with counters
```

#### Wrong data in dashboard
```bash
# Issue: Metrics showing unexpected values
# Solution: Verify metric calculation
# 1. Query same metric in Prometheus
# 2. Check timestamp alignment
# 3. Verify scrape interval matches dashboard refresh rate

# Check Prometheus scrape status
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Status > Targets > Filter by job
```

---

## Issue 6: Self-Healing Actions Not Triggering

### Symptoms
- Pods remain in failed state
- No action logs appearing
- Auto-scaling not working

### Diagnosis Steps

```bash
# Check health monitor logs
kubectl logs -n monitoring -l app=health-monitor --tail=100

# Verify RBAC permissions
kubectl auth can-i delete pods --as=system:serviceaccount:monitoring:health-monitor

# Check action logs
kubectl get events -n monitoring --sort-by='.lastTimestamp'

# Verify health checks are running
kubectl exec -it -n monitoring <health-monitor-pod> -- \
  curl localhost:8081/metrics | grep health_check
```

### Common Causes and Solutions

#### Insufficient RBAC permissions
```bash
# Issue: ServiceAccount lacks necessary permissions
# Solution: Verify and update ClusterRole
kubectl get clusterrole health-monitor -o yaml

# Required permissions for self-healing:
# - pods: [delete, create, get, list, watch]
# - nodes: [patch, get, list]
# - events: [create, watch]

# Apply corrected RBAC
kubectl apply -f config/rbac.yaml
```

#### Healing disabled in configuration
```bash
# Issue: Self-healing feature disabled
# Solution: Check configuration
kubectl get configmap -n monitoring health-monitor-config -o yaml

# Enable self-healing
kubectl patch configmap health-monitor-config -n monitoring \
  --type merge \
  -p '{"data":{"selfHealingEnabled":"true"}}'

# Restart health monitor
kubectl rollout restart deployment health-monitor -n monitoring
```

#### Pod protection policies blocking actions
```bash
# Issue: Pod Disruption Budgets preventing pod deletion
# Solution: Review and adjust PDB
kubectl get pdb -n monitoring

# Temporarily remove PDB for debugging
kubectl delete pdb <pdb-name> -n <namespace>

# Or adjust minAvailable
kubectl patch pdb <pdb-name> -n <namespace> \
  --type merge \
  -p '{"spec":{"minAvailable":0}}'
```

---

## Issue 7: Cluster Autoscaling Not Working

### Symptoms
- Nodes not scaling up when load increases
- Pods remain Pending indefinitely
- Scaling metrics not updating

### Diagnosis Steps

```bash
# Check Horizontal Pod Autoscaler status
kubectl get hpa -n <namespace>
kubectl describe hpa -n <namespace> <hpa-name>

# Check Metrics Server (required for HPA)
kubectl get deployment metrics-server -n kube-system

# Verify metrics are available
kubectl top nodes
kubectl top pods -n <namespace>

# Check cluster autoscaler logs (if using cloud provider)
kubectl logs -n kube-system -l app=cluster-autoscaler

# Check current resource requests/limits
kubectl describe node <node-name> | grep -A 10 "Allocated resources"
```

### Common Causes and Solutions

#### Metrics Server not installed
```bash
# Issue: HPA cannot get CPU/memory metrics
# Solution: Install Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify installation
kubectl get deployment metrics-server -n kube-system
kubectl get apiservices | grep custom.metrics
```

#### Pod resource requests not set
```bash
# Issue: HPA cannot calculate utilization
# Solution: Set resource requests/limits
kubectl set resources deployment app \
  --requests=cpu=100m,memory=128Mi \
  --limits=cpu=500m,memory=512Mi

# Verify
kubectl get deployment app -o yaml | grep -A 5 resources
```

#### Cluster autoscaler misconfigured
```bash
# Issue: Autoscaler cannot scale infrastructure
# Solution: Verify cloud provider configuration
# For AWS: Check autoscaling group tags
# For GCP: Check node pool configuration

# Check autoscaler logs
kubectl logs -n kube-system -l app=cluster-autoscaler | grep -i "scale"

# Verify min/max node counts
kubectl logs -n kube-system -l app=cluster-autoscaler | grep "nodeGroup"
```

---

## Performance Tuning

### Optimize Prometheus Scraping
```yaml
# Reduce scrape frequency for less critical metrics
prometheus:
  prometheusSpec:
    scrapeInterval: 60s  # default is 30s
    evaluationInterval: 60s
```

### Optimize Grafana Performance
```bash
# Increase dashboard refresh interval
# Dashboard Settings > General > Refresh

# Limit time range queries
# Use relative time ranges (last 7 days) instead of absolute

# Cache dashboard JSON
# Enable dashboard caching in Grafana config
```

### Optimize Health Monitor
```bash
# Increase check interval if load is high
helm upgrade health-monitor ./helm/k8s-health-monitor \
  --set config.healthCheckInterval=60s

# Disable unnecessary health checks
helm upgrade health-monitor ./helm/k8s-health-monitor \
  --set config.checks.pods.enabled=false
```

---

## Emergency Procedures

### Reset Prometheus Data
```bash
# WARNING: This deletes all historical data
kubectl exec -it -n monitoring prometheus-kube-prometheus-prometheus-0 -- \
  rm -rf /prometheus/wal /prometheus/chunks_head

kubectl rollout restart statefulset prometheus-kube-prometheus-prometheus -n monitoring
```

### Disable Alerting Temporarily
```bash
kubectl patch alertmanager alertmanager-kube-prometheus-alertmanager -n monitoring \
  --type merge \
  -p '{"spec":{"routes":[{"receiver":"null-receiver"}]}}'

# Re-enable
kubectl patch alertmanager alertmanager-kube-prometheus-alertmanager -n monitoring \
  --type merge \
  -p '{"spec":{"routes":[{"receiver":"default"}]}}'
```

### Pause Self-Healing Actions
```bash
kubectl patch deployment health-monitor -n monitoring \
  --type merge \
  -p '{"spec":{"replicas":0}}'

# Resume
kubectl patch deployment health-monitor -n monitoring \
  --type merge \
  -p '{"spec":{"replicas":2}}'
```

---

## Support and Escalation

If issues persist after troubleshooting:

1. **Collect diagnostic data**:
   ```bash
   kubectl get all -n monitoring
   kubectl describe nodes
   kubectl get events -A --sort-by='.lastTimestamp'
   kubectl logs -n monitoring --all-containers=true -l app=health-monitor
   ```

2. **Create issue with**:
   - Error messages and logs
   - Diagnostic output from above
   - Steps to reproduce
   - Expected vs actual behavior

3. **Contact**:
   - DevOps team: devops@company.com
   - On-call: Use PagerDuty
   - GitHub issues: [repository]/issues

---

**Last Updated**: 2024
**Maintained by**: DevOps Team
