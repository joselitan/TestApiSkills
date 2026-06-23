# 🚀 Snabbstart - Testa Rate Limiting NU!

## Steg 1: Starta servern

```bash
cd /Users/josemartin/TestApiSkills/src
python app.py
```

Servern startar på `http://localhost:8080`

## Steg 2: Testa med Python-scriptet (Enklast!)

Öppna en NY terminal:

```bash
cd /Users/josemartin/TestApiSkills
python scripts/test_rate_limiting.py
```

Du kommer att se:
- ✓ Login rate limit test (5/minut)
- ✓ Registration rate limit test (3/timme)
- ✓ Authentication test
- ✓ Headers test
- ✓ Burst protection test
- ✓ Password reset test

## Steg 3: Eller testa med curl

```bash
cd /Users/josemartin/TestApiSkills
./scripts/test_rate_limit_curl.sh
```

## Snabbtest med curl (1 kommando)

```bash
# Testa login rate limit - kör detta 6 gånger snabbt
for i in {1..6}; do echo "Request $i:" && curl -X POST http://localhost:8080/api/v1/login -H "Content-Type: application/json" -d '{"username":"test","password":"test"}' -w "\nHTTP Status: %{http_code}\n\n"; sleep 0.3; done
```

Den 6:e requesten ska ge **429 Rate Limit Exceeded**!

## Testa via Swagger UI

1. Öppna: http://localhost:8080/apidocs/
2. Hitta `POST /api/v1/login`
3. Klicka "Try it out"
4. Fyll i:
   - username: `test`
   - password: `test123`
5. Klicka "Execute" 6 gånger snabbt
6. Den 6:e ska ge **429**!

## Vad händer?

### Request 1-5:
```json
{
  "message": "Invalid credentials"
}
```
Status: **401** (OK - rate limit inte träffad än)

### Request 6:
```json
{
  "message": "Rate limit exceeded. Please try again later.",
  "retry_after": "2024-03-06 10:35:00"
}
```
Status: **429** (Rate limited! ✓)

## Implementerade Skydd

| Endpoint | Limit | Skyddar mot |
|----------|-------|-------------|
| Login | 5/min | Brute-force |
| Register | 3/timme | Spam |
| API Read | 100/min | DDoS |
| API Write | 30/min | Missbruk |
| Cleanup | 2/timme | Överanvändning |

## KLART! 🎉

Rate limiting fungerar nu! Se `RATE_LIMITING_IMPLEMENTATION.md` för detaljer.
