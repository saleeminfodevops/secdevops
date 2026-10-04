"""
Build Gate Decision Engine
Demonstrates how to use environments.yaml and cve_thresholds.yaml
to make automated build pass/fail decisions

Usage in CI/CD:
    python build_gate_example.py --scan-results scan-results.json \
                                 --environment production \
                                 --image myapp:1.0.0
"""

import json
import sys
import logging
from typing import Dict, List, Tuple
from pathlib import Path
from config_loader import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BuildGateDecisionEngine:
    """Makes build pass/fail decisions based on vulnerability scan results"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.build_gate = config.get_build_gate_config()
        self.severity_levels = config.get_severity_levels()
    
    def evaluate_scan_results(
        self,
        scan_results: Dict,
        image_name: str
    ) -> Tuple[bool, Dict]:
        """
        Evaluate scan results and determine if build should pass
        
        Args:
            scan_results: Parsed Trivy JSON results
            image_name: Container image name being scanned
            
        Returns:
            Tuple of (build_passed: bool, decision_details: dict)
        """
        # Parse vulnerabilities by severity
        vulnerabilities_by_severity = self._count_vulnerabilities(scan_results)
        
        logger.info(f"Scan results for {image_name}:")
        logger.info(f"  CRITICAL: {vulnerabilities_by_severity['CRITICAL']}")
        logger.info(f"  HIGH: {vulnerabilities_by_severity['HIGH']}")
        logger.info(f"  MEDIUM: {vulnerabilities_by_severity['MEDIUM']}")
        logger.info(f"  LOW: {vulnerabilities_by_severity['LOW']}")
        
        # Evaluate against thresholds
        decision = {
            'image': image_name,
            'environment': self.config.env,
            'vulnerabilities': vulnerabilities_by_severity,
            'checks': {},
            'passed': True,
            'failures': [],
            'warnings': [],
            'build_blocked': False,
            'requires_exception': False,
            'actions': []
        }
        
        # Check each severity level
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            check_result = self._check_severity_threshold(
                severity,
                vulnerabilities_by_severity[severity]
            )
            
            decision['checks'][severity] = check_result
            
            if not check_result['passed']:
                decision['passed'] = False
                decision['failures'].append(check_result['reason'])
                
                if check_result['blocks_build']:
                    decision['build_blocked'] = True
                    
                if check_result['requires_exception']:
                    decision['requires_exception'] = True
            
            if check_result['is_warning']:
                decision['warnings'].append(check_result['reason'])
        
        # Determine actions based on result
        decision['actions'] = self._determine_actions(decision)
        
        return decision['passed'] and not decision['build_blocked'], decision
    
    def _count_vulnerabilities(self, scan_results: Dict) -> Dict[str, int]:
        """Count vulnerabilities by severity"""
        counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'UNKNOWN': 0}
        
        for result in scan_results.get('Results', []):
            for vuln in result.get('Vulnerabilities', []):
                severity = vuln.get('Severity', 'UNKNOWN')
                if severity in counts:
                    counts[severity] += 1
        
        return counts
    
    def _check_severity_threshold(self, severity: str, count: int) -> Dict:
        """Check if a severity level exceeds threshold"""
        max_allowed = self.build_gate.thresholds.get(severity, {}).get('max_allowed', 0)
        action = self.build_gate.thresholds.get(severity, {}).get('action', 'log')
        
        passed = count <= max_allowed
        
        result = {
            'severity': severity,
            'count': count,
            'max_allowed': max_allowed,
            'passed': passed,
            'action': action,
            'is_warning': False,
            'blocks_build': False,
            'requires_exception': False,
            'reason': None
        }
        
        if not passed:
            excess = count - max_allowed
            result['reason'] = f"{severity}: {count} found (max {max_allowed}). Excess: {excess}"
            result['requires_exception'] = True
            
            # Determine if this blocks the build
            if self.config.should_fail_on_severity(severity):
                result['blocks_build'] = True
        
        if severity == (self.build_gate.warning_on_severity or 'UNKNOWN'):
            result['is_warning'] = True
        
        return result
    
    def _determine_actions(self, decision: Dict) -> List[Dict]:
        """Determine what actions to take based on decision"""
        actions = []
        
        if decision['build_blocked']:
            # Get action rules for the highest severity that caused failure
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                if not decision['checks'][severity]['passed']:
                    severity_actions = self.config.get_action_rules_for_severity(severity)
                    for action_rule in severity_actions:
                        # Check if action applies to this environment
                        if self.config.env in action_rule.get('environments', []):
                            actions.append(action_rule)
                    break
        
        return actions
    
    def format_report(self, decision: Dict) -> str:
        """Format decision as human-readable report"""
        lines = [
            "=" * 60,
            "BUILD GATE DECISION REPORT",
            "=" * 60,
            f"Image: {decision['image']}",
            f"Environment: {decision['environment']}",
            f"Status: {'✓ PASSED' if decision['passed'] else '✗ FAILED'}",
            ""
        ]
        
        lines.append("Vulnerability Summary:")
        for severity, count in decision['vulnerabilities'].items():
            max_allowed = self.build_gate.thresholds.get(severity, {}).get('max_allowed', 0)
            status = "✓" if count <= max_allowed else "✗"
            lines.append(f"  {status} {severity:8} {count:3} found (max {max_allowed})")
        
        lines.append("")
        lines.append("Detailed Checks:")
        for severity, check in decision['checks'].items():
            if not check['passed']:
                lines.append(f"  ✗ {check['reason']}")
        
        if decision['warnings']:
            lines.append("")
            lines.append("Warnings:")
            for warning in decision['warnings']:
                lines.append(f"  ⚠ {warning}")
        
        if decision['build_blocked']:
            lines.append("")
            lines.append("Build Blocking Issues:")
            for failure in decision['failures']:
                lines.append(f"  • {failure}")
        
        if decision['requires_exception']:
            lines.append("")
            lines.append("Actions Required:")
            lines.append("  • Exception approval required to proceed")
            
            # Show who can approve
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                if not decision['checks'][severity]['passed']:
                    approvers = self.config.get_approvers_for_severity(severity)
                    lines.append(f"  • Approvers for {severity}: {', '.join(approvers)}")
                    expiration = self.config.get_exception_expiration_days(severity)
                    lines.append(f"  • Exception expires in: {expiration} days")
                    break
        
        if decision['actions']:
            lines.append("")
            lines.append("Automated Actions to Execute:")
            for action in decision['actions']:
                lines.append(f"  • {action.get('action')}: {action.get('target', 'n/a')}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


class ExceptionHandler:
    """Handles exception checking and approval logic"""
    
    def __init__(self, config: ConfigManager, exceptions_file: str = 'exceptions.json'):
        self.config = config
        self.exceptions_file = exceptions_file
        self.exceptions = self._load_exceptions()
    
    def _load_exceptions(self) -> Dict:
        """Load exceptions from file"""
        try:
            with open(self.exceptions_file) as f:
                return json.load(f)
        except FileNotFoundError:
            return {'approved': []}
    
    def cve_has_exception(self, cve_id: str) -> bool:
        """Check if CVE has an approved exception"""
        from datetime import datetime
        
        for exception in self.exceptions.get('approved', []):
            if exception.get('cve_id') == cve_id:
                expires_at = datetime.fromisoformat(exception['expires_at'])
                if datetime.now() < expires_at:
                    return True
        return False
    
    def can_proceed_with_exception(self, decision: Dict) -> Tuple[bool, str]:
        """
        Check if build can proceed with exceptions instead of failing
        
        Returns:
            Tuple of (can_proceed: bool, reason: str)
        """
        if not self.config.allow_exceptions():
            return False, "Exceptions are not allowed in this environment"
        
        if not decision['requires_exception']:
            return True, "No exceptions required"
        
        if self.config.requires_security_review():
            return False, "Security review required before proceeding"
        
        return True, "Exception allowed to proceed"


def main():
    """Main entry point for build gate decision"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Vulnerability Scanner Build Gate')
    parser.add_argument('--scan-results', required=True, help='Path to Trivy scan results JSON')
    parser.add_argument('--environment', required=True, choices=['development', 'staging', 'production'],
                        help='Deployment environment')
    parser.add_argument('--image', required=True, help='Container image name')
    parser.add_argument('--config-dir', default='config', help='Configuration directory')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = ConfigManager(
            env=args.environment,
            env_config_path=f'{args.config_dir}/environments.yaml',
            threshold_config_path=f'{args.config_dir}/cve_thresholds.yaml'
        )
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(2)
    
    # Load scan results
    try:
        with open(args.scan_results) as f:
            scan_results = json.load(f)
    except FileNotFoundError:
        logger.error(f"Scan results file not found: {args.scan_results}")
        sys.exit(2)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in scan results: {args.scan_results}")
        sys.exit(2)
    
    # Evaluate scan results
    engine = BuildGateDecisionEngine(config)
    build_passed, decision = engine.evaluate_scan_results(scan_results, args.image)
    
    # Print report
    print(engine.format_report(decision))
    
    # Check for exceptions
    if not build_passed and decision['requires_exception']:
        exception_handler = ExceptionHandler(config)
        can_proceed, reason = exception_handler.can_proceed_with_exception(decision)
        
        if can_proceed:
            logger.info("Build can proceed with approved exceptions")
            sys.exit(0)
        else:
            logger.error(reason)
            sys.exit(1)
    
    # Exit with appropriate code
    sys.exit(0 if build_passed else 1)


if __name__ == '__main__':
    main()
