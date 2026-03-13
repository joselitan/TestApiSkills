#!/usr/bin/env python3
"""
Exempel på hur du kan utnyttja health check-funktionaliteten
"""

import requests
import json
import time


def check_application_health():
    """Kontrollera applikationens hälsa"""
    base_url = "http://localhost:8080"

    # 1. Grundläggande hälsokontroll
    try:
        response = requests.get(f"{base_url}/health")
        print("=== Grundläggande hälsokontroll ===")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Fel vid grundläggande hälsokontroll: {e}")

    # 2. Detaljerad hälsokontroll
    try:
        response = requests.get(f"{base_url}/health/detailed")
        print("\n=== Detaljerad hälsokontroll ===")
        health_data = response.json()
        print(json.dumps(health_data, indent=2))

        # Analysera resultatet
        if health_data.get("status") == "unhealthy":
            print("⚠️ VARNING: Applikationen är ohälsosam!")
        elif health_data.get("status") == "degraded":
            print("⚠️ VARNING: Applikationen har degraderad prestanda!")
        else:
            print("✅ Applikationen är hälsosam")

    except Exception as e:
        print(f"Fel vid detaljerad hälsokontroll: {e}")


def monitor_continuously():
    """Kontinuerlig övervakning"""
    print("Startar kontinuerlig övervakning...")
    while True:
        try:
            response = requests.get("http://localhost:8080/health/detailed")
            data = response.json()

            status = data.get("status", "unknown")
            uptime = data.get("uptime", "unknown")

            print(f"[{time.strftime('%H:%M:%S')}] Status: {status}, Uptime: {uptime}")

            # Varna för problem
            if status != "healthy":
                print(f"⚠️ Problem upptäckt: {status}")

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Fel vid hälsokontroll: {e}")

        time.sleep(30)  # Kontrollera var 30:e sekund


if __name__ == "__main__":
    check_application_health()
