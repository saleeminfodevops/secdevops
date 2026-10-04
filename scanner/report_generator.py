import json
from datetime import datetime
from jinja2 import Template
import smtplib

class VulnerabilityReportGenerator:
    def __init__(self, scan_result_file: str):
        with open(scan_result_file) as f:
            self.data = json.load(f)
    
    def generate_html_report(self, output_file: str):
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Container Scan Report</title>
            <style>
                body { font-family: Arial; margin: 20px; }
                .critical { color: #d32f2f; font-weight: bold; }
                .high { color: #f57c00; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            </style>
        </head>
        <body>
            <h1>Container Vulnerability Scan Report</h1>
            <p>Generated: {{ timestamp }}</p>
            <p>Image: {{ image_name }}</p>
            
            <h2>Summary</h2>
            <table>
                <tr>
                    <th>Severity</th>
                    <th>Count</th>
                </tr>
                <tr>
                    <td class="critical">CRITICAL</td>
                    <td>{{ stats.critical }}</td>
                </tr>
                <tr>
                    <td class="high">HIGH</td>
                    <td>{{ stats.high }}</td>
                </tr>
                <tr>
                    <td>MEDIUM</td>
                    <td>{{ stats.medium }}</td>
                </tr>
            </table>
            
            <h2>Vulnerabilities</h2>
            <table>
                <tr>
                    <th>CVE ID</th>
                    <th>Package</th>
                    <th>Severity</th>
                    <th>Description</th>
                </tr>
                {% for vuln in vulnerabilities %}
                <tr>
                    <td>{{ vuln.cve_id }}</td>
                    <td>{{ vuln.package }}</td>
                    <td class="{{ vuln.severity.lower() }}">{{ vuln.severity }}</td>
                    <td>{{ vuln.description[:100] }}...</td>
                </tr>
                {% endfor %}
            </table>
        </body>
        </html>
        """
        
        template = Template(html_template)
        report = template.render(
            timestamp=datetime.now().isoformat(),
            image_name=self.data.get('ArtifactName'),
            stats=self._calculate_stats(),
            vulnerabilities=self._flatten_vulnerabilities()
        )
        
        with open(output_file, 'w') as f:
            f.write(report)
    
    def _calculate_stats(self) -> dict:
        stats = {'critical': 0, 'high': 0, 'medium': 0}
        for result in self.data.get('Results', []):
            for vuln in result.get('Vulnerabilities', []):
                severity = vuln.get('Severity', '').lower()
                if severity in stats:
                    stats[severity] += 1
        return stats
    
    def _flatten_vulnerabilities(self) -> list:
        vulns = []
        for result in self.data.get('Results', []):
            for vuln in result.get('Vulnerabilities', []):
                vulns.append({
                    'cve_id': vuln.get('VulnerabilityID'),
                    'package': vuln.get('PkgName'),
                    'severity': vuln.get('Severity'),
                    'description': vuln.get('Description')
                })
        return vulns
