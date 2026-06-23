# 🎯 TESTA RATE LIMITING - STEG FÖR STEG

## 📋 Förberedelse

Du behöver:
- ✅ Python 3.x installerat
- ✅ Flask och dependencies installerade
- ✅ Två terminal-fönster

## 🚀 STEG 1: Starta Flask-servern

### Terminal 1:
```bash
cd /Users/josemartin/TestApiSkills/src
python app.py
```

**Förväntad output:**
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:8080
```

✅ **Servern körs nu!**

---

## 🧪 STEG 2: Välj din testmetod

### METOD A: Python Interactive Test (Rekommenderas! ⭐)

**Terminal 2:**
```bash
cd /Users/josemartin/TestApiSkills
python scripts/test_rate_limiting.py
```

**Du kommer se:**
```
════════════════════════════════════════════════════════════════════
                    RATE LIMITING TEST SUITE                    
════════════════════════════════════════════════════════════════════
Testing API at: http://localhost:8080

ℹ Checking if Flask server is running...
✓ Flask server is running

[1] Testing Login Rate Limit (5/minute)
──────────────────────────────────────────────────────────────────
ℹ Sending 6 login requests rapidly...
  Request 1: 401 Unauthorized (45ms)
  Request 2: 401 Unauthorized (42ms)
  Request 3: 401 Unauthorized (43ms)
  Request 4: 401 Unauthorized (44ms)
  Request 5: 401 Unauthorized (46ms)
  Request 6: 429 RATE LIMITED (12ms)
           Retry-After: Wed, 06 Mar 2024 10:35:00 GMT
✓ Login rate limiting is working correctly!

[2] Testing Registration Rate Limit (3/hour)
──────────────────────────────────────────────────────────────────
...
```

---

### METOD B: Bash/Curl Test

**Terminal 2:**
```bash
cd /Users/josemartin/TestApiSkills
chmod +x scripts/test_rate_limit_curl.sh
./scripts/test_rate_limit_curl.sh
```

---

### METOD C: Snabbt curl-kommando (1 rad!)

**Terminal 2:**
```bash
for i in {1..6}; do echo "=== Request $i ===" && curl -X POST http://localhost:8080/api/v1/login -H "Content-Type: application/json" -d '{"username":"test","password":"test"}' -s | python3 -m json.tool && echo ""; sleep 0.3; done
```

**Förväntad output:**
```
=== Request 1 ===
{
    "message": "Invalid credentials"
}

=== Request 2 ===
{
    "message": "Invalid credentials"
}

...

=== Request 6 ===
{
    "message": "Rate limit exceeded. Please try again later.",
    "retry_after": "Wed, 06 Mar 2024 10:35:00 GMT"
}
```

---

### METOD D: Via Swagger UI (Visuell!)

1. **Öppna webbläsare:** http://localhost:8080/apidocs/
2. **Hitta:** `POST /api/v1/login`
3. **Klicka:** "Try it out"
4. **Fyll i:**
   ```json
   {
     "username": "test",
     "password": "test123"
   }
   ```
5. **Klicka "Execute" 6 gånger snabbt**

**Resultat:**
- Request 1-5: `401 Unauthorized` ✅
- Request 6: `429 Rate Limit Exceeded` ✅

---

### METOD E: Pytest (Automatisk)

**Terminal 2:**
```bash
cd /Users/josemartin/TestApiSkills
pytest tests/test_rate_limiting.py -v
```

---

## ✅ VAD SKA HÄNDA?

### Första 5 requests:
```json
HTTP 401 Unauthorized
{
    "message": "Invalid credentials"
}
```
**Förklaring:** Login misslyckades (fel lösenord), men rate limit inte träffad än.

### 6:e requesten:
```json
HTTP 429 Too Many Requests
{
    "message": "Rate limit exceeded. Please try again later.",
    "retry_after": "2024-03-06 10:35:00"
}
```
**Förklaring:** Rate limit träffad! Du har gjort för många försök. ✅

---

## 🎯 SNABBTEST (30 sekunder)

Kör detta i Terminal 2:

```bash
# Test 1: Login (ska ge 429 på 6:e)
for i in {1..6}; do curl -X POST http://localhost:8080/api/v1/login -H "Content-Type: application/json" -d '{"username":"test","password":"test"}' -w "\nStatus: %{http_code}\n" -s -o /dev/null; done

# Vänta 2 sekunder
sleep 2

# Test 2: Rate limit status
curl http://localhost:8080/api/v1/rate-limit/status | python3 -m json.tool
```

**Förväntad output:**
```
Status: 401
Status: 401
Status: 401
Status: 401
Status: 401
Status: 429  ← RATE LIMITED! ✅

{
    "identifier": "ip:127.0.0.1",
    "ip_address": "127.0.0.1",
    "is_authenticated": false,
    "message": "Rate limit status retrieved successfully"
}
```

---

## 🔍 TESTA ANDRA ENDPOINTS

### Registration (3 per timme):
```bash
for i in {1..4}; do 
  curl -X POST http://localhost:8080/api/v1/register \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"test$i@example.com\",\"password\":\"Pass123!\",\"confirm_password\":\"Pass123!\"}" \
    -w "\nStatus: %{http_code}\n"
  sleep 0.5
done
```

### Password Reset (3 per timme):
```bash
for i in {1..4}; do 
  curl -X POST http://localhost:8080/api/v1/password-reset-request \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com"}' \
    -w "\nStatus: %{http_code}\n"
  sleep 0.5
done
```

---

## 📊 VERIFIERA FUNKTIONALITET

### ✅ Checklist:

- [ ] Starta server: `cd src && python app.py`
- [ ] Terminal 2: Kör ett test
- [ ] Första 5 requests: Status 401 (eller 200)
- [ ] 6:e request: Status 429 ✅
- [ ] Response innehåller "Rate limit exceeded"
- [ ] Loggar visar rate limit varning

### Server-loggar ska visa:
```
2024-03-06 10:30:15 WARNING Rate limit exceeded for ip:127.0.0.1 on /api/v1/login
```

---

## 🎉 SUCCESS!

Om du ser **429 Too Many Requests** på 6:e försöket = **RATE LIMITING FUNGERAR!** ✅

---

## 🔧 Felsökning

### Problem: Server startar inte
**Lösning:**
```bash
cd /Users/josemartin/TestApiSkills
pip install -r requirements.txt
cd src
python app.py
```

### Problem: "Connection refused"
**Lösning:** Kontrollera att servern körs på http://localhost:8080

### Problem: Får aldrig 429
**Lösning:** 
1. Kontrollera att `flask-limiter` är installerat: `pip install flask-limiter>=3.5.0`
2. Kolla server-loggar för errors
3. Testa från annan IP eller vänta 1 minut

### Problem: Får 429 direkt på första försöket
**Lösning:** Vänta 1 minut för rate limit att återställas

---

## 📚 Mer Information

- **Detaljerad guide:** `docs/RATE_LIMITING_GUIDE.md`
- **Implementation:** `RATE_LIMITING_IMPLEMENTATION.md`
- **Summary:** `IMPLEMENTATION_SUMMARY.md`
- **Quick start:** `SNABBSTART_RATE_LIMITING.md`

---

## 💡 Tips

1. **Testa olika endpoints** för att se olika rate limits
2. **Använd Swagger UI** för visuell testning
3. **Kolla server-loggar** för att se rate limit-träffar
4. **Vänta 1 minut** mellan test-runs för att återställa limits

---

## 🚀 Nu är det din tur!

```bash
# Terminal 1
cd /Users/josemartin/TestApiSkills/src && python app.py

# Terminal 2  
cd /Users/josemartin/TestApiSkills && python scripts/test_rate_limiting.py
```

**GO! 🎯**
