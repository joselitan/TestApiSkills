"""
Shared Flask extensions — importeras av app.py och blueprints.
Håller alla extension-objekt på ett ställe för att undvika cirkulära importer.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Rate limiter — initialiseras med app i app.py via limiter.init_app(app)
# Inga default_limits — vi sätter limiter explicit bara på auth-endpoints
# så att guestbook och andra routes inte påverkas.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",  # In-memory storage, ingen Redis behövs
)
