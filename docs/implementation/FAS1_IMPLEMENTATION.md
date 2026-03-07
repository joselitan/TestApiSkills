# Fas 1: API Testing Enhancement - Implementation Guide

## Implementerat (2024-01-XX)

### 1. Test Data Factory ✅
**Fil:** `tests/factories.py`

Använder Faker för att generera realistisk testdata:
- `create_guestbook_entry()` - Generera en entry
- `create_multiple_entries(count)` - Generera flera entries
- `create_user_credentials()` - Generera login credentials
- `create_invalid_entry()` - Generera invalid data för negative testing

**Användning:**
```python
from tests.factories import create_guestbook_entry

# I dina tester
def test_with_factory(auth_token):
    entry = create_guestbook_entry()
    response = requests.post(f"{BASE_URL}/api/guestbook", json=entry, headers=headers)
```

### 2. API Contract Testing ✅
**Fil:** `tests/test_api_contract.py`

JSON Schema validation för alla API responses:
- Login response schema
- Guestbook list schema (med pagination)
- Single entry schema
- Validerar datatyper, required fields, format

**Kör tester:**
```bash
pytest tests/test_api_contract.py -v
```

### 3. Negative Testing ✅
**Fil:** `tests/test_negative_cases.py`

Testar felhantering och säkerhet:
- Authentication errors (missing credentials, wrong password)
- Invalid tokens
- Missing required fields
- Invalid email format
- SQL injection attempts
- XSS attempts
- Non-existent resources (404)
- Wrong data types
- Oversized payloads

**Kör tester:**
```bash
pytest tests/test_negative_cases.py -v
```

### 4. Performance Testing ✅
**Fil:** `tests/locustfile.py`

Load testing med Locust:
- Simulerar riktiga användare
- Olika task weights (read > create)
- Automatisk login och token management

**Kör load test:**
```bash
# Starta Locust web UI
locust -f tests/locustfile.py --host=http://localhost:8080

# Eller headless mode
locust -f tests/locustfile.py --host=http://localhost:8080 --users 50 --spawn-rate 5 --run-time 1m --headless
```

Öppna http://localhost:8089 för att se dashboard.

### 5. Uppdaterad conftest.py ✅
**Fil:** `conftest.py`

Lagt till shared fixtures:
- `auth_token` - Återanvändbar auth token för alla tester
- `test_entry` - Generera en test entry med factory
- `test_entries` - Generera flera test entries

### 6. Allure Rapportering ✅
**Filer:** `pytest.ini`, `ALLURE_GUIDE.md`, Allure decorators i test-filer

Enterprise-grade test rapportering:
- Features och Stories gruppering
- Severity levels (CRITICAL, NORMAL, MINOR)
- Step-by-step test execution
- Visuella grafer och trends
- Timeline och statistics

**Kör med Allure:**
```bash
# Generera Allure data
pytest tests/test_api_contract.py tests/test_negative_cases.py --alluredir=reports/allure-results

# Visa rapport
allure serve reports/allure-results
```

Se `ALLURE_GUIDE.md` för fullständig guide.

## Kör Alla Fas 1 Tester

```bash
# Alla nya tester med Allure
pytest tests/test_api_contract.py tests/test_negative_cases.py --alluredir=reports/allure-results -v

# Med HTML och coverage
pytest tests/ --cov=. --cov-report=html --html=reports/test_report.html

# Kombinerat
pytest tests/ --alluredir=reports/allure-results --cov=. --cov-report=html --html=reports/test_report.html
```

## Sammanfattning

✅ Test Data Factory - Faker integration
✅ API Contract Testing - JSON Schema validation  
✅ Negative Testing - 20+ security & error tests
✅ Performance Testing - Locust load testing
✅ Allure Rapportering - Enterprise-grade reporting
✅ pytest.ini - Test configuration
✅ Uppdaterad conftest.py - Shared fixtures

**Resultat:** Fas 1 är nu KOMPLETT med professionell API testing suite och enterprise rapportering!
