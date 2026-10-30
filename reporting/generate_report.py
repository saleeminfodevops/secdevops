import json
import os
import requests

REPORT_PATH = "/home/devsecops/container-vulnerability-scanner/reporting/scan_report.json"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def parse_and_notify():
    if not os.path.exists(REPORT_PATH):
        print(f"Error: No scan report found at {REPORT_PATH}")
        return

    try:
        with open(REPORT_PATH, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse {REPORT_PATH}. The file might be corrupted or empty.")
        return

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

    payload = {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Container Security Scan Complete*" if critical_count > 0 else "*Container Security Scan Complete*"
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
            print("Notification successfully sent to Slack.")
        else:
            print(f"Slack Webhook returned an error: Status {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Slack API: {e}")

if __name__ == "__main__":
    parse_and_notify()
