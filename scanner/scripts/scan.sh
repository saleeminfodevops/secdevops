#!/bin/bash
set -e

OUTPUT_DIR="/home/devsecops/container-vulnerability-scanner/reporting"
BASE_DIR="/home/devsecops/container-vulnerability-scanner/scanner"

mkdir -p "$OUTPUT_DIR"

# 1. Get a list of all local docker images in "repository:tag" format
# Excludes <none> dangling images
echo "=== Fetching all local Docker images ==="
IMAGES=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -v "<none>")

# 2. Loop through each image and scan it
for IMAGE_NAME in $IMAGES; do
    echo "--------------------------------------------------"
    echo "=== Executing Trivy Vulnerability Scan for: $IMAGE_NAME ==="
    
    # Sanitize image name to use as a safe filename (e.g., library/ubuntu:latest -> library_ubuntu_latest)
    SAFE_NAME=$(echo "$IMAGE_NAME" | tr '/:' '__')
    REPORT_FILE="$OUTPUT_DIR/scan_report_${SAFE_NAME}.json"

    # Run Trivy scan
    docker run --rm \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v "$BASE_DIR/config:/home/devsecops/container-vulnerability-scanner/scanner/config" \
      -v "$OUTPUT_DIR:/home/devsecops/container-vulnerability-scanner/reporting" \
      aquasec/trivy:latest image \
      --format json \
      --config "/home/devsecops/container-vulnerability-scanner/scanner/config/trivy.yml" \
      --output "/home/devsecops/container-vulnerability-scanner/reporting/scan_report_${SAFE_NAME}.json" \
      "$IMAGE_NAME"

    echo "Scan report generated at $REPORT_FILE"

    # 3. Process metrics and alert per image
    echo "==== Processing Metrics & Sending Alert for $IMAGE_NAME ==="
    # Note: If your python script expects the filename as an argument, pass it here like: 
    # python3 .../generate_report.py "$REPORT_FILE"
    python3 /home/devsecops/container-vulnerability-scanner/reporting/generate_report.py
    
    echo "Scan report alert sending on slack for $IMAGE_NAME"
done

echo "=== All images scanned successfully! ==="
