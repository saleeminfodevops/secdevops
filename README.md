# 🛡️ Container Image Vulnerability Scanner with Reporting

An automated, pipeline-integrated DevSecOps solution designed to scan container images, enforce security compliance gates, distribute real-time alerts, and aggregate historical vulnerability trends.

---

## 🏗️ Project Overview

This project addresses critical security gaps in modern containerized workflows by automating vulnerability management. DevOps pipelines often skip or manually handle container image scanning due to a lack of native tooling. 

This project delivers a CI/CD-integrated vulnerability scanner that automatically checks images against known exploit databases. It automates the gatekeeping process, shifting security left and guaranteeing that only compliant container images are deployed.

* **The Challenge**: DevOps teams lack seamless tools to catch container vulnerabilities, risking insecure production deployments.
* **The Solution**: An automated security scanner built directly into the CI/CD pipeline ecosystem.
* **The Impact**: Eradicates manual checks, delivers instant security reports, and ensures only verified images reach production environments.

---

## 🎯 Project Goals

* **Automate Security Audits**: Build a container image scanner that automatically cross-references code against established CVE databases before production deployment.
* **Streamline Pipeline Integration**: Embed the scanner natively into standard CI/CD workflows, specifically targeting Jenkins, GitHub Actions, and GitLab CI/CD.
* **Visualize Security Health**: Launch a centralized dashboard tracking historical data on detected, resolved, and outstanding vulnerabilities.  
* **Accelerate Incident Response**: Deliver comprehensive vulnerability logs and trigger instant alerts via Slack and Microsoft Teams.

---

## 🧰 Technology Stack


| Category | Tools & Technologies | Project Purpose |
| :--- | :--- | :--- |
| **Core Dev** 🐳 | Python, Bash, Docker | Build scripts, pipeline execution, container engine |
| **Security** 🛡️ | Trivy, Clair, CVE Database | Automated container scanning and threat definition lookup |
| **DevOps** 🚀 | GitHub Actions, Jenkins, GitLab CI/CD | Continuous automation and pipeline gatekeeping |
| **Observability** 📊 | Prometheus, Grafana | Metric collection, logging, and historical trend dashboarding |
| **Alerting** 💬 | Slack API, MS Teams API | Instant ChatOps notifications for engineering teams |

---

## 📁 Repository Directory Structure

```text
├── .github/workflows/       # GitHub Actions CI/CD workflow pipeline definitions
├── jenkins/                 # Jenkinsfile configuration templates
├── scanner/                 # Scanner wrapper engines and automation scripts
│   ├── config/              # Central configuration variables and CVE policy profiles
│   ├── policy/              # Exception controls (.trivyignore templates)
│   └── scripts/             # Core parsing, rescan, and error-handling utilities
├── reporting/               # Modules generating PDF, HTML, and JSON format logs
├── monitoring/              # Prometheus metric scrapers & Grafana layout exports
└── docs/                    # Installation runbooks and troubleshooting manuals
```

---

## 🚀 Getting Started

### Prerequisites
Before deployment, verify your local system has the following CLI tools installed:
* [Docker Desktop / Engine](https://docker.com) (v20.10+)
* [Trivy CLI](https://github.iolatest/getting-started/installation/)
* [Prometheus & Grafana](https://prometheus.io)

### 🛠️ Local Installation & Usage

1. **Clone the repository**:
   ```bash
   git clone https://github.com
   cd container-vulnerability-scanner
   ```

2. **Run an isolated manual container image scan**:
   ```bash
   # Scan a target image and filter strictly by High and Critical threats
   trivy image --severity HIGH,CRITICAL nginx:alpine
   ```

3. **Execute the automation wrapper script**:
   ```bash
   # Provide executable permissions to the scanner utility script
   chmod +x scanner/scripts/scan_image.sh
   
   # Run the custom automated engine to output structured text
   ./scanner/scripts/scan_image.sh --image=python:3.9-slim --format=json
   ```

---

## 🔄 Project Roadmap & Sprint Delivery

### Sprint 1: Initial Setup and Basic Vulnerability Scanning
* **Tasks**: Built repository skeleton layout; configured standalone Trivy/Clair environments; performed initial sample image vulnerability checks; connected live CVE database sync feeds.
* **Goal**: Establish a functional image parsing tool footprint.

### Sprint 2: Integrating Vulnerability Scanning with CI/CD Pipelines
* **Tasks**: Wrote pipeline scripts for GitHub Actions/Jenkins; built strict build-failure logic flags tied to risk severities; exposed threshold configuration variables.
* **Goal**: Embed security gates directly into active deployment paths.

### Sprint 3: Report Generation and Notification System
* **Tasks**: Built modules generating structured PDF, HTML, and JSON files; linked webhook handlers to Slack/Teams APIs; configured automated daily threat summary digests.
* **Goal**: Push structural vulnerability insights directly to engineering teams.

### Sprint 4: Web Dashboard for Historical Vulnerability Tracking
* **Tasks**: Mounted operational Grafana graphing dashboards; exposed active scanner metrics to Prometheus collection engines; filtered views by individual image name and risk scope.
* **Goal**: Provide long-term observability into security health and trends.

### Sprint 5: Advanced Scanner Customization and Exception Handling
* **Tasks**: Configured targeted policy ignore lists (`.trivyignore`); built scheduling utilities for automated image rescans; developed graceful error-retry handling logic inside pipelines.
* **Goal**: Deliver a flexible policy scanning ecosystem that minimizes false alarms.

### Sprint 6: Documentation, Testing, and Final Deployment
* **Tasks**: Produced deployment runbooks; performed extensive multi-platform CI engine regression checks; collected and implemented user feedback updates.
* **Goal**: Deliver a polished, production-ready DevSecOps pipeline asset.

---

## 📦 Summary of Project Deliverables

1. **Automated Vulnerability Scanner**: Core vulnerability assessment engine utilizing updated CVE data feeds.
2. **CI/CD Gate Integration**: Reusable workflow pipelines configured to block high-risk image builds.
3. **Real-Time Notification Engine**: Live messaging hooks feeding structured alerts into Slack or Teams.
4. **Web Security Dashboard**: Grafana tracking configurations summarizing historical compliance metrics over time.
5. **Operational Runbook**: Comprehensive setup, deployment script, and custom policy exception manuals.

---

## 🤝 Contributors

* **Saleem Shaikh** 
* **Abdulkadir Boxwala** 
* **Manikanadan Muthu**
* **Punit Patel** 
* **Gautam Gohel** 

---
<p align="center"><i>"Stopping vulnerabilities before they reach production. 🛑"</i></p>
