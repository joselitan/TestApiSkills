#!/bin/bash
# CI/CD Health Check Script

BASE_URL="http://localhost:8080"
MAX_RETRIES=10
RETRY_DELAY=5

echo "=== Deployment Health Check ==="

# Vänta på att applikationen ska starta
echo "Väntar på att applikationen ska starta..."
for i in $(seq 1 $MAX_RETRIES); do
    if curl -s "$BASE_URL/health/live" > /dev/null; then
        echo "✅ Applikationen svarar"
        break
    fi
    
    if [ $i -eq $MAX_RETRIES ]; then
        echo "❌ Applikationen svarar inte efter $MAX_RETRIES försök"
        exit 1
    fi
    
    echo "Försök $i/$MAX_RETRIES - väntar $RETRY_DELAY sekunder..."
    sleep $RETRY_DELAY
done

# Kontrollera readiness
echo "Kontrollerar readiness..."
READY_RESPONSE=$(curl -s -w "%{http_code}" "$BASE_URL/health/ready")
READY_CODE="${READY_RESPONSE: -3}"

if [ "$READY_CODE" = "200" ]; then
    echo "✅ Applikationen är redo"
else
    echo "❌ Applikationen är inte redo (HTTP $READY_CODE)"
    exit 1
fi

# Detaljerad hälsokontroll
echo "Utför detaljerad hälsokontroll..."
HEALTH_RESPONSE=$(curl -s "$BASE_URL/health/detailed")
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))")

case "$HEALTH_STATUS" in
    "healthy")
        echo "✅ Deployment lyckades - applikationen är hälsosam"
        exit 0
        ;;
    "degraded")
        echo "⚠️ Deployment delvis lyckad - applikationen har degraderad prestanda"
        echo "$HEALTH_RESPONSE" | python -m json.tool
        exit 0
        ;;
    "unhealthy")
        echo "❌ Deployment misslyckades - applikationen är ohälsosam"
        echo "$HEALTH_RESPONSE" | python -m json.tool
        exit 1
        ;;
    *)
        echo "❌ Okänd hälsostatus: $HEALTH_STATUS"
        exit 1
        ;;
esac