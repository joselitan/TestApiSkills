"""Automated Security Scanning Script"""
import subprocess
import json
import os
import sys
from datetime import datetime


def run_bandit_scan():
    """Run Bandit security scan"""
    print("Running Bandit security scan...")
    
    try:
        # Run Bandit scan
        result = subprocess.run([
            "bandit", "-r", ".", 
            "-f", "json", 
            "-o", "reports/bandit_report.json",
            "--exclude", "tests/,reports/,venv/,.venv/"
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        if result.returncode == 0:
            print("Bandit scan completed successfully")
        else:
            print(f"Bandit scan completed with issues (exit code: {result.returncode})")
        
        # Parse results
        try:
            with open("reports/bandit_report.json", "r") as f:
                bandit_data = json.load(f)
                
            issues = bandit_data.get("results", [])
            print(f"Bandit found {len(issues)} security issues")
            
            # Categorize by severity
            severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for issue in issues:
                severity = issue.get("issue_severity", "UNKNOWN")
                if severity in severity_counts:
                    severity_counts[severity] += 1
            
            for severity, count in severity_counts.items():
                if count > 0:
                    print(f"   {severity}: {count} issues")
            
            return len(issues)
            
        except FileNotFoundError:
            print("Bandit report file not found")
            return -1
        except json.JSONDecodeError:
            print("Failed to parse Bandit report")
            return -1
            
    except FileNotFoundError:
        print("Bandit not found. Install with: pip install bandit")
        return -1
    except Exception as e:
        print(f"Bandit scan failed: {str(e)}")
        return -1


def run_safety_scan():
    """Run Safety dependency vulnerability scan"""
    print("\nRunning Safety dependency scan...")
    
    try:
        # Run Safety scan
        result = subprocess.run([
            "safety", "check", 
            "--json", 
            "--output", "reports/safety_report.json"
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        if result.returncode == 0:
            print("Safety scan completed - no vulnerabilities found")
            return 0
        else:
            print(f"Safety scan found vulnerabilities (exit code: {result.returncode})")
        
        # Parse results
        try:
            with open("reports/safety_report.json", "r") as f:
                safety_data = json.load(f)
            
            vulnerabilities = safety_data if isinstance(safety_data, list) else []
            print(f"Safety found {len(vulnerabilities)} vulnerable dependencies")
            
            for vuln in vulnerabilities[:5]:  # Show first 5
                package = vuln.get("package", "Unknown")
                version = vuln.get("installed_version", "Unknown")
                vuln_id = vuln.get("vulnerability_id", "Unknown")
                print(f"   {package} {version} - {vuln_id}")
            
            if len(vulnerabilities) > 5:
                print(f"   ... and {len(vulnerabilities) - 5} more")
            
            return len(vulnerabilities)
            
        except FileNotFoundError:
            print("Safety report file not found")
            return -1
        except json.JSONDecodeError:
            print("Failed to parse Safety report")
            return -1
            
    except FileNotFoundError:
        print("Safety not found. Install with: pip install safety")
        return -1
    except Exception as e:
        print(f"Safety scan failed: {str(e)}")
        return -1


def run_security_tests():
    """Run security test suite"""
    print("\nRunning security test suite...")
    
    try:
        # Run security tests
        result = subprocess.run([
            "pytest", "tests/security/", 
            "-v", 
            "--alluredir=reports/allure-results",
            "--html=reports/security_test_report.html",
            "--self-contained-html"
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        print("Security test results:")
        print(result.stdout)
        
        if result.stderr:
            print("Test warnings/errors:")
            print(result.stderr)
        
        return result.returncode
        
    except FileNotFoundError:
        print("pytest not found. Install with: pip install pytest")
        return -1
    except Exception as e:
        print(f"Security tests failed: {str(e)}")
        return -1


def generate_security_summary():
    """Generate security scan summary"""
    print("\nGenerating security summary...")
    
    summary = {
        "scan_date": datetime.now().isoformat(),
        "bandit_issues": 0,
        "safety_vulnerabilities": 0,
        "test_results": "unknown",
        "overall_status": "unknown"
    }
    
    # Read Bandit results
    try:
        with open("reports/bandit_report.json", "r") as f:
            bandit_data = json.load(f)
        summary["bandit_issues"] = len(bandit_data.get("results", []))
    except:
        pass
    
    # Read Safety results
    try:
        with open("reports/safety_report.json", "r") as f:
            safety_data = json.load(f)
        if isinstance(safety_data, list):
            summary["safety_vulnerabilities"] = len(safety_data)
    except:
        pass
    
    # Determine overall status
    total_issues = summary["bandit_issues"] + summary["safety_vulnerabilities"]
    
    if total_issues == 0:
        summary["overall_status"] = "GOOD"
        status_emoji = "GOOD"
    elif total_issues <= 5:
        summary["overall_status"] = "WARNING"
        status_emoji = "WARNING"
    else:
        summary["overall_status"] = "CRITICAL"
        status_emoji = "CRITICAL"
    
    # Save summary
    with open("reports/security_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print(f"\nSecurity Scan Summary ({status_emoji}):")
    print(f"   Bandit Issues: {summary['bandit_issues']}")
    print(f"   Safety Vulnerabilities: {summary['safety_vulnerabilities']}")
    print(f"   Overall Status: {summary['overall_status']}")
    print(f"   Report saved to: reports/security_summary.json")
    
    return summary


def main():
    """Main security scanning function"""
    print("TestApiSkills Security Scanner")
    print("=" * 50)
    
    # Ensure reports directory exists
    os.makedirs("reports", exist_ok=True)
    
    # Run scans
    bandit_issues = run_bandit_scan()
    safety_vulns = run_safety_scan()
    test_result = run_security_tests()
    
    # Generate summary
    summary = generate_security_summary()
    
    # Exit with appropriate code
    total_issues = max(0, bandit_issues) + max(0, safety_vulns)
    
    if total_issues > 0 or test_result != 0:
        print(f"\nSecurity scan completed with {total_issues} issues")
        sys.exit(1)
    else:
        print("\nSecurity scan completed successfully - no issues found")
        sys.exit(0)


if __name__ == "__main__":
    main()