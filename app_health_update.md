# Health Check Integration Instructions

To integrate health check functionality into your Flask app:

## 1. Add health check import at the top of your app.py:
```python
from health_check import setup_health_routes
```

## 2. Add this after app initialization (around line 20):
```python
# Setup health check routes
setup_health_routes(app)
```

This will add the following endpoints:
- `/health` - Basic health check
- `/health/detailed` - Comprehensive health check
- `/health/ready` - Kubernetes readiness probe
- `/health/live` - Kubernetes liveness probe