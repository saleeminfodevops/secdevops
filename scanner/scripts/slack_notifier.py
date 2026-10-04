import requests
import json
from typing import Dict, List

class SlackNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_scan_summary(self, image: str, stats: Dict, vulnerabilities: List):
        color_map = {
            'CRITICAL': '#d32f2f',
            'HIGH': '#f57c00',
            'MEDIUM': '#fbc02d'
        }
        
        fields = [
            {
                "title": "Image",
                "value": image,
                "short": True
            },
            {
                "title": "Critical",
                "value": str(stats.get('critical', 0)),
                "short": True
            },
            {
                "title": "High",
                "value": str(stats.get('high', 0)),
                "short": True
            },
            {
                "title": "Medium",
                "value": str(stats.get('medium', 0)),
                "short": True
            }
        ]
        
        # Determine alert color based on highest severity found
        color = '#36a64f'  # Green by default
        if stats.get('critical', 0) > 0:
            color = color_map['CRITICAL']
        elif stats.get('high', 0) > 0:
            color = color_map['HIGH']
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": "🔍 Container Vulnerability Scan Report",
                    "fields": fields,
                    "footer": "Trivy Container Scanner",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        response = requests.post(self.webhook_url, json=payload)
        return response.status_code == 200
