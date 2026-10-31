import json
import os
import sys
import requests

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def parse_and_notify():
    # 1. Read the report path passed dynamically from the bash script
    if len(sys.argv) < 2:
        print("Error: Missing report file path argument.")
        print("Usage: python3 generate_report.py <path_to_scan_report.json>")
        return
        
    report_path = sys.argv[1]

    if not os.path.exists(report_path):
        print(f"Error: No scan report found at {report_path}")
        return

    try:
        with open(report_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse {report_path}. The file might be corrupted or empty.")
        return

    # 2. Extract image name directly from the Trivy JSON report metadata
    image_name = data.get('ArtifactName', 'Unknown Image')

    vuln_count = 0
    critical_count = 0

    results = data.get('Results', [])
    if results is None:
        results = []

    for res in results:
        vulns = res.get('Vulnerabilities', [])
        if vulns is None:
            continue
        vuln_count += len(vulns)
        for v in vulns:
            if v.get('Severity') == 'CRITICAL':
                critical_count += 1

    color = "#FF0000" if critical_count > 0 else "#36a64f"

    # 3. Dynamic payload featuring the specific image scanned
    payload = {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Container Security Scan Complete for:* `{image_name}`"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Total Issues Found:*\n{vuln_count}"},
                            {"type": "mrkdwn", "text": f"*Critical Vulnerabilities:*\n{critical_count}"}
                        ]
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            print(f"Notification successfully sent to Slack for {image_name}.")
        else:
            print(f"Slack Webhook returned an error: Status {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Slack API: {e}")

if __name__ == "__main__":
    parse_and_notify()
