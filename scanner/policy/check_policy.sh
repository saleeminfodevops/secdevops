#!/bin/bash
IMAGE=$1
MAX_RETRIES=3
RETRY_COUNT=0

until [ $RETRY_COUNT -ge $MAX_RETRIES ]
do
   echo "Scanning attempt $(($RETRY_COUNT+1))..."
   trivy image --ignorefile scanner/.trivyignore --exit-code 0 $IMAGE && break
   RETRY_COUNT=$(($RETRY_COUNT+1))
   sleep 5
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
   echo "Scan failed consistently after $MAX_RETRIES attempts."
   exit 1
fi
