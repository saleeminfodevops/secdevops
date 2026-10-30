#!/bin/bash
set -e

IMAGE_NAME=${1:-"vulnerables/web-dvwa:latest"}
OUTPUT_DIR="/home/devsecops/container-vulnerability-scanner/reporting"
mkdir -p "$OUTPUT_DIR"

BASE_DIR="/home/devsecops/container-vulnerability-scanner/scanner"

echo "=== Pulling Target Image: $IMAGE_NAME ==="
docker pull "$IMAGE_NAME"

echo "=== Executing Trivy Vulnerability Scan ==="
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$BASE_DIR/config:/home/devsecops/container-vulnerability-scanner/scanner/config" \
  -v "$OUTPUT_DIR:/home/devsecops/container-vulnerability-scanner/reporting" \
  aquasec/trivy:latest image \
  --format json \
  --config "/home/devsecops/container-vulnerability-scanner/scanner/config/trivy.yml" \
  --output "/home/devsecops/container-vulnerability-scanner/reporting/scan_report.json" \
  "$IMAGE_NAME"

echo "Scan report generated at $OUTPUT_DIR/scan_report.json"

echo "==== Processing Metrics & Sending Alert ==="
python3 /home/devsecops/container-vulnerability-scanner/reporting/generate_report.py

echo "Scan report alert sending on slack"

