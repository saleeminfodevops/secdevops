import json
import sys
from typing import Dict, List

def parse_trivy_json(filepath: str) -> Dict:
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    results = {
        'critical': [],
        'high': [],
        'medium': [],
        'total': 0
    }
    
    for result in data.get('Results', []):
        for vuln in result.get('Vulnerabilities', []):
            severity = vuln.get('Severity', 'UNKNOWN').lower()
            if severity in results:
                results[severity].append({
                    'cve': vuln.get('VulnerabilityID'),
                    'package': vuln.get('PkgName'),
                    'version': vuln.get('InstalledVersion'),
                    'description': vuln.get('Description')
                })
            results['total'] += 1
    
    return results

def check_thresholds(results: Dict, severity_threshold: str = 'HIGH') -> bool:
    threshold_map = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2}
    threshold_level = threshold_map.get(severity_threshold, 1)
    
    if threshold_level <= 0 and results['critical']:
        print(f"❌ CRITICAL vulnerabilities found: {len(results['critical'])}")
        return False
    
    if threshold_level <= 1 and results['high']:
        print(f"❌ HIGH vulnerabilities found: {len(results['high'])}")
        return False
    
    print(f"✓ Scan passed. Total vulnerabilities: {results['total']}")
    return True

if __name__ == '__main__':
    results = parse_trivy_json('scan-results.json')
    passed = check_thresholds(results, sys.argv[1] if len(sys.argv) > 1 else 'HIGH')
    sys.exit(0 if passed else 1)
