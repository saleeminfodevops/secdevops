#!/bin/bash

IMAGE=$1
OUTPUT_DIR=${2:-.}

echo "Scanning image: $IMAGE"

trivy image \
  --config trivy_config.yaml \
  --format json \
  --output "$OUTPUT_DIR/scan-result-$(date +%s).json" \
  "$IMAGE"

echo "Scan complete. Results saved to $OUTPUT_DIR"
