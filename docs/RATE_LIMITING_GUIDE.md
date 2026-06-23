# Rate Limiting & API Throttling Guide

## Översikt

Rate limiting har implementerats i Guestbook API för att skydda mot:
- **DDoS-attacker**: Förhindra överbelastning av servern
- **Brute-force-attacker**: Begränsa login-försök
- **API-missbruk**: Kontrollera användning av resurser
- **Kostnadshantering**: Reglera API-anrop per användare

## Implementationsdetaljer

### Teknologi
- **flask-limiter**: Python-bibliotek för rate limiting
- **Storage**: In-memory (kan konfigureras till Redis för produktion)
- **Strategi**: Fixed-window rate limiting
- **Identifiering**: Per IP-adress (anonym) eller per användare (autentiserad)

### Konfigurerade Gränser

#### Autentiseringsendpoints (Brute-force-skydd)
| Endpoint | Gräns | Syfte |
|----------|-------|-------|
| `POST /api/v1/login` | 5/minut, 20/timme | Förhindra brute-force på lösenord |
| `POST /api/v1/register` | 3/timme, 10/dag | Förhindra spam-registreringar |
| `POST /api/v1/password-reset-request` | 3/timme, 10/dag | Förhindra email-spam |
| `POST /api/v1/password-reset` | 5/timme | Begränsa återställningsförsök |
| `GET /api/v1/verify-email` | 10/timme | Begränsa verifieringsförsök |

#### Guestbook-endpoints (API-skydd)
| Endpoint | Gräns | Syfte |
|----------|-------|-------|
| `GET /api/v1/guestbook` | 100/minut, 1000/timme | Läsoperationer |
| `GET /api/v1/guestbook/:id` | 100/minut, 1000/timme | Läsoperationer |
| `POST /api/v1/guestbook` | 30/minut, 300/timme | Skrivoperationer |
| `PUT /api/v1/guestbook/:id` | 30/minut, 300/timme | Uppdateringsoperationer |
| `DELETE /api/v1/guestbook/:id` | 20/minut, 200/timme | Raderingsoperationer |
| `DELETE /api/v1/guestbook/bulk` | 10/minut, 50/timme | Bulk-operationer |
| `DELETE /api/v1/guestbook/cleanup` | 2/timme, 5/dag | Databas-cleanup |
| `POST /api/v1/guestbook/import` | 5/minut, 30/timme | Import-operationer |

#### Övriga endpoints
| Endpoint | Gräns | Syfte |
|----------|-------|-------|
| `GET /health`, `GET /ready` | 60/minut | Health checks |
| `GET /api/v1/rate-limit/status` | 10/minut | Status-kontroll |

### Filstruktur

```
src/
├── app.py                          # Huvudapplikation med rate limit-konfiguration
├── rate_limiter.py                 # Rate limiting-konfiguration och utilities
└── blueprints/v1/
    ├── auth.py                     # Auth-endpoints (rate limited)
    ├── guestbook.py                # Guestbook-endpoints (rate limited)
    └── rate_limit_test.py          # Test-endpoint för rate limiting

tests/
└── test_rate_limiting.py           # Pytest-testsvit för rate limiting

scripts/
└── test_rate_limiting.py           # Interaktiv testscript
```

## Hur Rate Limiting Fungerar

### Identifiering
Rate limiting spårar förfrågningar baserat på:

1. **Autentiserade användare**: Använder JWT-token för att identifiera användare
   ```
   Identifier: user:john@example.com
   ```

2. **Anonyma användare**: Använder IP-adress
   ```
   Identifier: ip:192.168.1.100
   ```

### Response Headers
När rate limiting är aktivt inkluderas följande headers i svaret:

```
X-RateLimit-Limit: 5          # Max antal requests per tidsfönster
X-RateLimit-Remaining: 3      # Återstående requests
X-RateLimit-Reset: 1234567890 # Timestamp när limit återställs
```

### HTTP 429 Response
När gränsen överskrids returneras:

```json
{
  "message": "Rate limit exceeded. Please try again later.",
  "retry_after": "2024-03-06 10:35:00"
}
```

## Konfiguration

### Environment Variables

Rate limiting kan konfigureras via environment variables:

```bash
# Default rate limit för alla routes
RATE_LIMIT_DEFAULT="1000 per hour, 100 per minute"

# Storage backend (default: memory, production: redis)
RATE_LIMIT_STORAGE_URI="memory://"
# För Redis:
# RATE_LIMIT_STORAGE_URI="redis://localhost:6379"

# Environment (påverkar felhantering)
ENVIRONMENT="development"  # eller "production"
```

### Anpassning

För att ändra rate limits, modifiera `src/app.py`:

```python
# Exempel: Ändra login-limit till 10/minut
limiter.limit("10 per minute, 40 per hour")(
    app.view_functions.get("auth_v1.login")
)
```

## Testing

### 1. Automatiska tester med pytest

```bash
# Kör alla rate limiting-tester
pytest tests/test_rate_limiting.py -v

# Kör specifik testklass
pytest tests/test_rate_limiting.py::TestRateLimitingAuth -v

# Kör specifikt test
pytest tests/test_rate_limiting.py::TestRateLimitingAuth::test_login_rate_limit_per_minute -v
```

### 2. Interaktiv testscript

```bash
# Starta Flask-servern först
cd src && python app.py

# I en annan terminal, kör testscript
python scripts/test_rate_limiting.py
```

Testscriptet kör följande tester:
1. ✓ Login Rate Limit (5/minut)
2. ✓ Registration Rate Limit (3/timme)
3. ✓ Authenticated vs Unauthenticated
4. ✓ Rate Limit Headers
5. ✓ Burst Protection
6. ✓ Password Reset Rate Limit

### 3. Manuell testning med curl

#### Test login rate limit
```bash
# Skicka 6 login-requests snabbt
for i in {1..6}; do
  curl -X POST http://localhost:8080/api/v1/login \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","password":"test123"}' \
    -w "\nStatus: %{http_code}\n"
  sleep 0.5
done
```

#### Test authenticated vs unauthenticated
```bash
# Utan token (IP-baserad)
curl http://localhost:8080/api/v1/rate-limit/status

# Med token (user-baserad)
TOKEN="your-jwt-token-here"
curl http://localhost:8080/api/v1/rate-limit/status \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Load testing med locust

Skapa `locustfile.py`:

```python
from locust import HttpUser, task, between

class RateLimitUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    @task(3)
    def test_login(self):
        self.client.post("/api/v1/login", json={
            "username": "testuser",
            "password": "test123"
        })
    
    @task(1)
    def test_register(self):
        import time
        self.client.post("/api/v1/register", json={
            "email": f"test{time.time()}@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!"
        })
```

Kör locust:
```bash
locust -f locustfile.py --host http://localhost:8080
```

## Produktionsinställningar

### Redis Backend
För produktion rekommenderas Redis för rate limiting-storage:

```python
# Installera redis
pip install redis

# Environment variable
RATE_LIMIT_STORAGE_URI="redis://localhost:6379/0"
```

### Docker-compose exempel
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  api:
    build: .
    environment:
      - RATE_LIMIT_STORAGE_URI=redis://redis:6379/0
    depends_on:
      - redis
```

### Monitoring
Övervaka rate limiting i produktion:

```python
# Logga rate limit-träffar
@app.errorhandler(429)
def ratelimit_handler(e):
    current_app.logger.warning(
        f"Rate limit exceeded for {get_user_identifier()} on {request.path}"
    )
    # Skicka till monitoring-system (Prometheus, Datadog, etc.)
    metrics.increment('rate_limit.exceeded', tags=[
        f'endpoint:{request.path}',
        f'user:{get_user_identifier()}'
    ])
    return jsonify({
        "message": "Rate limit exceeded",
        "retry_after": e.description
    }), 429
```

## Best Practices

### 1. Graduell Rate Limiting
Använd flera tidsfönster för bättre skydd:
```python
"5 per minute, 20 per hour, 100 per day"
```

### 2. Olika limits för olika användare
```python
# VIP-användare: högre limits
if user.is_vip:
    limit = "1000 per hour"
else:
    limit = "100 per hour"
```

### 3. Exponential Backoff
Implementera exponential backoff på klientsidan:
```python
import time

def call_api_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url)
        if response.status_code != 429:
            return response
        
        # Exponential backoff
        wait_time = 2 ** attempt
        time.sleep(wait_time)
    
    raise Exception("Max retries exceeded")
```

### 4. Whitelist för interna tjänster
```python
# I rate_limiter.py
def get_user_identifier():
    # Whitelist för interna IP-adresser
    if request.remote_addr in ['10.0.0.1', '10.0.0.2']:
        return "internal:whitelisted"
    
    # Normal rate limiting
    ...
```

## Felsökning

### Problem: Rate limits träffas för snabbt
**Lösning**: Öka limits i `app.py` eller använd Redis för bättre prestanda

### Problem: Rate limits fungerar inte
**Lösning**: 
1. Kontrollera att `flask-limiter` är installerat
2. Verifiera att `init_limiter(app)` anropas
3. Kolla loggar för felmeddelanden

### Problem: Olika IP-adresser får samma limit
**Lösning**: Kontrollera `get_remote_address()` funktion, kan behöva konfigurera proxy-headers

## Säkerhetsöverväganden

1. **IP Spoofing**: Använd `X-Forwarded-For` header försiktigt, validera proxy-källor
2. **Distributed Attacks**: Rate limiting per IP skyddar inte mot distribuerade attacker från många IP-adresser
3. **CAPTCHA Integration**: Överväg CAPTCHA efter flera misslyckade försök
4. **Account Lockout**: Komplettera med account lockout-mekanism efter X misslyckade försök

## Sammanfattning

Rate limiting är nu implementerat och ger:
- ✅ Skydd mot brute-force-attacker på login (5/minut)
- ✅ Förhindrar spam-registreringar (3/timme)
- ✅ Kontrollerar API-användning (olika limits per endpoint)
- ✅ Separata limits för autentiserade vs anonyma användare
- ✅ Automatisk 429-response när limit överskrids
- ✅ Lätt att konfigurera och testa
- ✅ Produktionsklar med Redis-support

## Nästa Steg

1. **Testa implementationen**: Kör testscripten för att verifiera
2. **Justera limits**: Anpassa baserat på faktisk användning
3. **Övervaka**: Implementera metrics och alerts
4. **Redis i produktion**: Byt till Redis för bättre skalbarhet
5. **CAPTCHA**: Överväg att lägga till CAPTCHA för extra skydd

## Support

För frågor eller problem, kontakta utvecklingsteamet eller se dokumentationen:
- Flask-Limiter: https://flask-limiter.readthedocs.io/
- API-dokumentation: http://localhost:8080/apidocs/
