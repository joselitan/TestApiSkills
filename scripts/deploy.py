#!/usr/bin/env python3
"""
Automated Deployment Script for QA Test Platform
Handles deployment to staging and production environments
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime


class DeploymentManager:
    def __init__(self, environment="staging"):
        self.environment = environment
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.deployment_log = f"deployment_{self.environment}_{self.timestamp}.log"

    def log(self, message):
        """Log deployment messages"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)

        with open(f"logs/{self.deployment_log}", "a") as f:
            f.write(log_message + "\n")

    def run_command(self, command, check=True):
        """Run shell command and log output"""
        self.log(f"Running: {command}")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.stdout:
                self.log(f"Output: {result.stdout.strip()}")
            if result.stderr and result.returncode != 0:
                self.log(f"Error: {result.stderr.strip()}")

            if check and result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, command)

            return result
        except Exception as e:
            self.log(f"Command failed: {e}")
            if check:
                raise

    def health_check(self, url="http://localhost:8080/health", timeout=60):
        """Perform health check on deployed application"""
        self.log(f"Performing health check on {url}")

        import requests

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.log("✅ Health check passed")
                    return True
            except:
                pass

            time.sleep(5)

        self.log("❌ Health check failed")
        return False

    def backup_database(self):
        """Backup current database before deployment"""
        if self.environment == "production":
            backup_name = f"guestbook_backup_{self.timestamp}.db"
            self.log(f"Creating database backup: {backup_name}")
            self.run_command(f"cp guestbook.db backups/{backup_name}")

    def deploy_staging(self):
        """Deploy to staging environment"""
        self.log("🚀 Starting staging deployment")

        # Stop existing containers
        self.run_command("docker-compose down", check=False)

        # Build new image
        self.log("Building Docker image...")
        self.run_command("docker-compose build")

        # Start services
        self.log("Starting services...")
        self.run_command("docker-compose up -d qa-platform")

        # Wait for service to be ready
        time.sleep(30)

        # Health check
        if not self.health_check():
            self.log("❌ Staging deployment failed - health check failed")
            return False

        # Run smoke tests
        self.log("Running smoke tests...")
        result = self.run_command(
            "docker-compose run --rm test-runner pytest test_guestbook_api.py::TestGuestbookAPI::test_login -v",
            check=False,
        )

        if result.returncode == 0:
            self.log("✅ Staging deployment successful")
            return True
        else:
            self.log("❌ Staging deployment failed - smoke tests failed")
            return False

    def deploy_production(self):
        """Deploy to production environment"""
        self.log("🌟 Starting production deployment")

        # Backup database
        self.backup_database()

        # Stop existing containers gracefully
        self.log("Stopping existing services...")
        self.run_command("docker-compose down", check=False)

        # Build production image
        self.log("Building production Docker image...")
        self.run_command("docker-compose build")

        # Start services
        self.log("Starting production services...")
        self.run_command("docker-compose up -d qa-platform")

        # Wait for service to be ready
        time.sleep(45)

        # Health check
        if not self.health_check():
            self.log("❌ Production deployment failed - health check failed")
            self.rollback()
            return False

        # Run full test suite
        self.log("Running production validation tests...")
        result = self.run_command(
            "docker-compose run --rm test-runner pytest test_guestbook_api.py -v",
            check=False,
        )

        if result.returncode == 0:
            self.log("✅ Production deployment successful")
            self.cleanup_old_backups()
            return True
        else:
            self.log("❌ Production deployment failed - validation tests failed")
            self.rollback()
            return False

    def rollback(self):
        """Rollback to previous version"""
        self.log("🔄 Starting rollback procedure...")

        # Find latest backup
        backups = [
            f for f in os.listdir("backups/") if f.startswith("guestbook_backup_")
        ]
        if backups:
            latest_backup = sorted(backups)[-1]
            self.log(f"Restoring from backup: {latest_backup}")
            self.run_command(f"cp backups/{latest_backup} guestbook.db")

        # Restart services
        self.run_command("docker-compose restart qa-platform")

        self.log("✅ Rollback completed")

    def cleanup_old_backups(self, keep_count=5):
        """Keep only the latest N backups"""
        backups = [
            f for f in os.listdir("backups/") if f.startswith("guestbook_backup_")
        ]
        if len(backups) > keep_count:
            old_backups = sorted(backups)[:-keep_count]
            for backup in old_backups:
                os.remove(f"backups/{backup}")
                self.log(f"Removed old backup: {backup}")

    def generate_deployment_report(self, success):
        """Generate deployment report"""
        report = {
            "environment": self.environment,
            "timestamp": self.timestamp,
            "success": success,
            "deployment_log": self.deployment_log,
        }

        report_file = f"reports/deployment_{self.environment}_{self.timestamp}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        self.log(f"Deployment report saved: {report_file}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python deploy.py [staging|production]")
        sys.exit(1)

    environment = sys.argv[1]
    if environment not in ["staging", "production"]:
        print("Environment must be 'staging' or 'production'")
        sys.exit(1)

    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    os.makedirs("backups", exist_ok=True)

    deployer = DeploymentManager(environment)

    try:
        if environment == "staging":
            success = deployer.deploy_staging()
        else:
            success = deployer.deploy_production()

        deployer.generate_deployment_report(success)

        if success:
            print(f"✅ {environment.title()} deployment completed successfully!")
            sys.exit(0)
        else:
            print(f"❌ {environment.title()} deployment failed!")
            sys.exit(1)

    except Exception as e:
        deployer.log(f"Deployment failed with exception: {e}")
        deployer.generate_deployment_report(False)
        print(f"❌ {environment.title()} deployment failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
