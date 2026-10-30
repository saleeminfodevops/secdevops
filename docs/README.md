# Container Vulnerability Scanner

[![Security Scan](https://github.com)](https://github.com)
[![License: MIT](https://shields.io)](https://opensource.org)
[![Trivy](https://shields.io)](https://github.io)

An automated, pipeline-integrated container security tool designed to scan Docker images for vulnerabilities, enforce risk thresholds, generate structured audit alerts, and track historical telemetry via a unified web dashboard.

---

## 🏗️ Project Architecture & Directory Layout

```text
container-vulnerability-scanner
├── .github
│   └── workflows
│       └── container-security.yml  # GitHub Actions CI Automation
├── Jenkinsfile
│   └── container-security.groovy # Jenkins Multi-stage Pipeline
├── dashboard
│   ├── docker-compose.yml        # Telemetry UI Core Engine Stack
│   └── grafana-dashboard.json    # Pre-built Metric Visualizations
├── dockerfiles
│   └── Dockerfile.malicious       # Local Testing Sandbox Target
├── docs
│   └── README.md                 # Project Setup & Architecture Guides
├── monitoring
│   ├── docker-compose.yml        # Shared Prometheus Scraping Stack
│   └── prometheus.yml            # Data Collection Configurations
├── reporting
│   ├── generate_report.py        # Python Notification & Parser Engine
│   └── ubuntu_1804_report.json   # Structural Data Output Sample
└── scanner
    ├── .trivyignore              # Risk Exceptions & Whitelist File
    ├── config
    │   └── trivy.yml             # Global Engine Flag Defaults
    ├── policy
    │   └── check_policy.sh       # Execution Policy & Retry Handler
    └── scripts
        └── scan.sh               # Core Scan CLI Wrapper Script
```

---

## 🚀 Quick Start & Local Execution

### Prerequisites
* **Docker & Docker Compose** installed locally.
* **Python 3.x** (with `requests` library installed for notifications).

### Step 1: Execute a Manual Scan
Run the scanner script against any target container image (defaults to `ubuntu:18.04` if omitted):
```bash
chmod +x scanner/scripts/scan.sh scanner/policy/check_policy.sh
./scanner/scripts/scan.sh "python:3.9-slim"
```

### Step 2: Generate Metrics Summary & Notify Slack
Set your webhook endpoint configuration and execute the parsing engine:
```bash
export SLACK_WEBHOOK_URL="https://slack.com"
python3 reporting/generate_report.py
```

### Step 3: Spin Up the Visual Telemetry Dashboard
Launch the tracking engine locally to view historical vulnerability trends over time:
```bash
docker-compose -f dashboard/docker-compose.yml up -d
```
* **Grafana Web UI:** Access via `http://localhost:3000` (Default credentials: `admin` / `admin`).
* **Prometheus Gateway:** Access via `http://localhost:9090`.

---

## 🛠️ CI/CD Pipeline Integration

### GitHub Actions
The tool includes a native `.github/workflows/container-security.yml` file. It automatically acts as a quality gate, failing the runner build (`exit-code 1`) whenever **HIGH** or **CRITICAL** CVE definitions are discovered during a push or Pull Request.

### Jenkins Pipeline
The provided `container-security.groovy` dynamic script reads global parameters seamlessly. Update environment thresholds on your Jenkins controller configuration:
* `SEVERITY_THRESHOLD`: Adjust levels dynamically (e.g., `CRITICAL`).
* `IMAGE_TO_SCAN`: The build tag target created during standard code assembly steps.

---

## 🔒 Advanced Adjustments & Exceptions Management

### Ignoring Known CVE Risks
If a vulnerability has an approved exception or has been mitigated internally, add the vulnerability identifier to `scanner/.trivyignore`:
```text
# scanner/.trivyignore
CVE-2020-8908
CVE-2023-45853
```

### Policy Control with Automatic Retries
The policy engine wrapper (`scanner/policy/check_policy.sh`) features automated registry connectivity fallback logic. If a database timeout occurs, it will automatically attempt a retry up to **3 times** before safely breaking the pipeline block.

---

## 📝 License
Distributed under the **MIT License**. See `LICENSE` for more information.

