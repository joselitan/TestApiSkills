# 📊 Logging & Monitoring - Snabbguide

## Vad Har Implementerats?

✅ **Strukturerad logging** med Python logging module
✅ **Automatisk request/response logging** för alla API-anrop
✅ **Error tracking** med full traceback
✅ **Performance monitoring** (slow request detection)
✅ **Security logging** (login attempts, failures)
✅ **Roterande log-filer** (max 10MB per fil, 10 backups)

## Log-filer

```
logs/
├── app.log       # Alla loggar (INFO, WARNING, ERROR)
├── error.log     # Bara errors (ERROR, CRITICAL)
└── access.log    # API access logs (requests/responses)
```

## Log Format

```
[TIMESTAMP] LEVEL - MESSAGE
[2024-03-06 14:30:15] INFO - POST /api/login | User: admin | IP: 127.0.0.1 | Status: 200 | Time: 23ms
```

## Exempel på Loggar

### Lyckad Login
```
[2024-03-06 14:30:10] INFO - Login attempt for user: admin from IP: 127.0.0.1
[2024-03-06 14:30:10] INFO - Login successful for user: admin
[2024-03-06 14:30:10] INFO - POST /api/login | User: anonymous | IP: 127.0.0.1 | Status: 200 | Time: 23ms
```

### Misslyckad Login
```
[2024-03-06 14:31:05] INFO - Login attempt for user: hacker from IP: 192.168.1.100
[2024-03-06 14:31:05] WARNING - Login failed for user: hacker - Invalid credentials
[2024-03-06 14:31:05] WARNING - POST /api/login | User: anonymous | IP: 192.168.1.100 | Status: 401 | Time: 15ms
```

### API Request
```
[2024-03-06 14:32:00] INFO - POST /api/guestbook | User: admin | IP: 127.0.0.1 | Status: 201 | Time: 45ms
```

### Slow Request
```
[2024-03-06 14:35:00] INFO - GET /api/guestbook?limit=1000 | User: admin | IP: 127.0.0.1 | Status: 200 | Time: 1250ms
[2024-03-06 14:35:00] WARNING - Slow request detected: /api/guestbook took 1250ms
```

### Error
```
[2024-03-06 14:40:00] ERROR - Unhandled exception: Database connection failed
[2024-03-06 14:40:00] ERROR - Traceback (most recent call last):
  File "app.py", line 145, in create_entry
    conn = get_db()
  ...
[2024-03-06 14:40:00] ERROR - POST /api/guestbook | User: admin | IP: 127.0.0.1 | Status: 500 | Time: 102ms
```

## Hur Man Använder Loggarna

### Se Senaste Loggarna (Real-time)
```bash
# Windows
type logs\app.log

# Mac/Linux
tail -f logs/app.log
```

### Sök Efter Errors
```bash
# Windows
findstr "ERROR" logs\error.log

# Mac/Linux
grep "ERROR" logs/error.log
```

### Hitta Långsamma Requests
```bash
# Windows
findstr "Slow request" logs\app.log

# Mac/Linux
grep "Slow request" logs/app.log
```

### Hitta Misslyckade Logins
```bash
# Windows
findstr "Login failed" logs\app.log

# Mac/Linux
grep "Login failed" logs/app.log
```

### Se Specifik Användares Aktivitet
```bash
# Windows
findstr "User: admin" logs\access.log

# Mac/Linux
grep "User: admin" logs/access.log
```

## Log Nivåer

| Nivå | Användning | Exempel |
|------|------------|---------|
| **DEBUG** | Detaljerad info för debugging | Utveckling |
| **INFO** | Normal operation | Lyckade requests |
| **WARNING** | Något konstigt | Slow requests, failed login |
| **ERROR** | Något gick fel | Exceptions, errors |
| **CRITICAL** | Allvarligt fel | System crash |

## Automatisk Logging

### Alla API Requests Loggas Automatiskt
- HTTP Method (GET, POST, etc.)
- Endpoint path
- User (från JWT token)
- IP Address
- Response Status Code
- Response Time (ms)

### Errors Loggas Automatiskt
- Exception message
- Full traceback
- Request context

### Performance Monitoring
- Requests > 500ms loggas som WARNING
- Hjälper identifiera flaskhalsar

## Roterande Log-filer

Loggar roteras automatiskt:
- Max storlek: 10MB per fil
- Backups: 10 filer
- Exempel: `app.log`, `app.log.1`, `app.log.2`, etc.

## Tips & Tricks

### Analysera Traffic Patterns
```bash
# Räkna requests per endpoint
grep "GET /api" logs/access.log | wc -l
```

### Hitta Säkerhetshot
```bash
# Hitta upprepade failed logins från samma IP
grep "Login failed" logs/app.log | grep "192.168.1.100"
```

### Performance Analysis
```bash
# Hitta alla requests > 1000ms
grep "Time: [0-9][0-9][0-9][0-9]ms" logs/access.log
```

## Nästa Steg

1. ✅ Logging implementerat
2. ⏳ Starta appen och se loggar i console
3. ⏳ Testa några API-anrop
4. ⏳ Kolla logs/ mappen
5. ⏳ Analysera loggarna
