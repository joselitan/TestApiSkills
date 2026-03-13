#!/usr/bin/env python3
"""
Alerting system för QA Platform
Övervakar health status och skickar varningar
"""

import json
import logging
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText

import requests


class HealthMonitor:
    def __init__(self, base_url="http://localhost:8080", check_interval=60):
        self.base_url = base_url
        self.check_interval = check_interval
        self.last_status = None
        self.alert_count = 0

        # Konfigurera logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("logs/health_monitor.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def check_health(self):
        """Kontrollera applikationens hälsa"""
        try:
            response = requests.get(f"{self.base_url}/health/detailed", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def send_alert(self, health_data, alert_type="status_change"):
        """Skicka varning (här bara logga, men kan utökas med email/Slack)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = health_data.get("status", "unknown")

        alert_message = f"""
        HEALTH ALERT - {alert_type.upper()}
        Timestamp: {timestamp}
        Status: {status}
        Uptime: {health_data.get('uptime', 'unknown')}
        
        System Metrics:
        - CPU: {health_data.get('system', {}).get('cpu_usage', 'N/A')}
        - Memory: {health_data.get('system', {}).get('memory_usage', 'N/A')}
        - Disk: {health_data.get('system', {}).get('disk_usage', 'N/A')}
        
        Database: {health_data.get('database', {}).get('status', 'N/A')}
        """

        self.logger.warning(alert_message)

        # Här kan du lägga till email/Slack-notifikationer
        # self.send_email(alert_message)
        # self.send_slack(alert_message)

    def analyze_health(self, health_data):
        """Analysera hälsodata och avgör om varning behövs"""
        current_status = health_data.get("status", "unknown")

        # Statusförändring
        if self.last_status and self.last_status != current_status:
            self.send_alert(health_data, "status_change")
            self.alert_count += 1

        # Kritiska tillstånd
        if current_status == "unhealthy":
            self.send_alert(health_data, "critical")
            self.alert_count += 1

        # Resursvarningar
        system = health_data.get("system", {})
        if system:
            cpu_usage = float(system.get("cpu_usage", "0%").replace("%", ""))
            memory_usage = float(system.get("memory_usage", "0%").replace("%", ""))
            disk_usage = float(system.get("disk_usage", "0%").replace("%", ""))

            if cpu_usage > 80:
                self.logger.warning(f"Hög CPU-användning: {cpu_usage}%")
            if memory_usage > 80:
                self.logger.warning(f"Hög minnesanvändning: {memory_usage}%")
            if disk_usage > 90:
                self.logger.warning(f"Lågt diskutrymme: {disk_usage}%")

        self.last_status = current_status

    def run_monitoring(self):
        """Kör kontinuerlig övervakning"""
        self.logger.info("Startar health monitoring...")

        while True:
            try:
                health_data = self.check_health()
                self.analyze_health(health_data)

                # Logga status var 10:e kontroll
                if self.alert_count % 10 == 0:
                    status = health_data.get("status", "unknown")
                    uptime = health_data.get("uptime", "unknown")
                    self.logger.info(f"Health check: {status} (uptime: {uptime})")

            except Exception as e:
                self.logger.error(f"Fel vid health monitoring: {e}")

            time.sleep(self.check_interval)


if __name__ == "__main__":
    monitor = HealthMonitor()
    monitor.run_monitoring()
