# Add health check import at the top
from health_check import setup_health_routes

# Add this after app initialization (around line 20)
# Setup health check routes
setup_health_routes(app)
