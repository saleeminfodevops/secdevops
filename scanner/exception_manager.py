import json
from datetime import datetime, timedelta

class ExceptionManager:
    def __init__(self, exceptions_file: str):
        self.exceptions_file = exceptions_file
        self.exceptions = self._load_exceptions()
    
    def _load_exceptions(self) -> dict:
        try:
            with open(self.exceptions_file) as f:
                return json.load(f)
        except FileNotFoundError:
            return {'approved': []}
    
    def add_exception(self, cve_id: str, reason: str, expires_in_days: int = 90):
        """Add an approved vulnerability exception"""
        expiration = datetime.now() + timedelta(days=expires_in_days)
        exception = {
            'cve_id': cve_id,
            'reason': reason,
            'created_at': datetime.now().isoformat(),
            'expires_at': expiration.isoformat(),
            'approved_by': 'admin'  # Should come from user context
        }
        self.exceptions['approved'].append(exception)
        self._save_exceptions()
        return exception
    
    def is_exception_valid(self, cve_id: str) -> bool:
        """Check if CVE has a valid exception"""
        for exc in self.exceptions.get('approved', []):
            if exc['cve_id'] == cve_id:
                expiration = datetime.fromisoformat(exc['expires_at'])
                if datetime.now() < expiration:
                    return True
        return False
    
    def _save_exceptions(self):
        with open(self.exceptions_file, 'w') as f:
            json.dump(self.exceptions, f, indent=2)

# Usage in scan results processing
def filter_results_with_exceptions(scan_results: dict, exceptions_mgr: ExceptionManager) -> dict:
    filtered_results = {'Results': []}
    
    for result in scan_results.get('Results', []):
        filtered_vulns = []
        for vuln in result.get('Vulnerabilities', []):
            cve_id = vuln.get('VulnerabilityID')
            if not exceptions_mgr.is_exception_valid(cve_id):
                filtered_vulns.append(vuln)
            else:
                print(f"⊘ Skipping excepted vulnerability: {cve_id}")
        
        if filtered_vulns:
            result['Vulnerabilities'] = filtered_vulns
            filtered_results['Results'].append(result)
    
    return filtered_results
