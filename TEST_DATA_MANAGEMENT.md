# Test Data Management

## Översikt

Vi har nu separata databaser för test och produktion:
- **Produktion:** `guestbook.db` (används av `app.py`)
- **Test:** `guestbook_test.db` (används av tester)

## Hur Det Fungerar

### 1. Databas Separation

**database.py** har uppdaterats med `test_mode` parameter:
```python
get_db_path(test_mode=False)  # Returnerar rätt databas
init_db(test_mode=False)       # Initierar rätt databas
get_db(test_mode=False)        # Ansluter till rätt databas
clear_test_db()                # Rensar test-databasen
```

### 2. Pytest Fixtures (conftest.py)

Automatisk setup av test-databas:
```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Skapar test-databas innan alla tester"""
    
@pytest.fixture(scope="function")
def clean_test_db():
    """Rensar test-databas innan varje test"""
```

### 3. Test App (test_app.py)

En separat version av app.py som använder test-databasen.

## Användning

### Kör Produktion (Normal App)
```bash
# Använder guestbook.db
python app.py
```

### Kör Tester (Test Database)
```bash
# Använder guestbook_test.db automatiskt
pytest test_guestbook_api.py -v

# Med HTML rapport
pytest test_guestbook_api.py --html=reports/test_report.html --cov=. --cov-report=html

# Utan cleanup (data stannar i test DB)
pytest test_guestbook_api.py -k "not zzz_cleanup" -v
```

### Kör Test App Manuellt
```bash
# Starta test app (använder guestbook_test.db)
python test_app.py

# Nu kan du testa mot http://localhost:8080
# All data går till test-databasen
```

### Rensa Test Database
```python
# I Python
from database import clear_test_db
clear_test_db()
```

Eller via pytest:
```bash
pytest test_guestbook_api.py -k "zzz_cleanup" -v
```

## Fördelar

✅ **Separation:** Test och produktionsdata blandas aldrig
✅ **Säkerhet:** Tester kan inte förstöra produktionsdata
✅ **Flexibilitet:** Kan köra tester utan att påverka produktion
✅ **Cleanup:** Enkel att rensa test-data
✅ **CI/CD:** Perfekt för automatiserade tester

## Filstruktur

```
TestApiSkills/
├── guestbook.db          # Produktionsdatabas
├── guestbook_test.db     # Test-databas (auto-skapad)
├── app.py                # Produktions-app
├── test_app.py           # Test-app (använder test DB)
├── database.py           # Uppdaterad med test_mode
├── conftest.py           # Pytest fixtures
└── test_guestbook_api.py # API tester
```

## .gitignore

Båda databaserna är ignorerade:
```
*.db
*.sqlite
*.sqlite3
```

## Nästa Steg

1. ✅ Test rapportering (KLART)
2. ✅ Test data management (KLART)
3. ⏳ API dokumentation (Swagger)
4. ⏳ Logging & Monitoring
