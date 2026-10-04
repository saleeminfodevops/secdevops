from prometheus_client import Counter, Gauge, start_http_server
import json
import time

# Define metrics
critical_vulns = Counter(
    'vulnerabilities_critical_total',
    'Total critical vulnerabilities found',
    ['image', 'date']
)

high_vulns = Counter(
    'vulnerabilities_high_total',
    'Total high vulnerabilities found',
    ['image', 'date']
)

scan_duration = Gauge(
    'scan_duration_seconds',
    'Time taken to scan image',
    ['image']
)

images_scanned = Counter(
    'images_scanned_total',
    'Total images scanned',
    ['status']  # passed, failed
)

def export_metrics(scan_result_file: str, image_name: str):
    with open(scan_result_file) as f:
        data = json.load(f)
    
    # Count vulnerabilities by severity
    crit_count = 0
    high_count = 0
    
    for result in data.get('Results', []):
        for vuln in result.get('Vulnerabilities', []):
            if vuln.get('Severity') == 'CRITICAL':
                crit_count += 1
            elif vuln.get('Severity') == 'HIGH':
                high_count += 1
    
    # Record metrics
    critical_vulns.labels(image=image_name, date=datetime.now().date()).inc(crit_count)
    high_vulns.labels(image=image_name, date=datetime.now().date()).inc(high_count)
    
    status = 'passed' if (crit_count == 0 and high_count == 0) else 'failed'
    images_scanned.labels(status=status).inc()

if __name__ == '__main__':
    start_http_server(9090)
    time.sleep(86400)  # Run indefinitely
