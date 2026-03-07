# Allure Rapportering - Användningsguide

## Installation

Allure är redan installerat via `allure-pytest>=2.13.0` i requirements.txt.

För att visa rapporter behöver du Allure command-line tool:

### Windows:
```bash
# Med Scoop
scoop install allure

# Eller ladda ner från: https://github.com/allure-framework/allure2/releases
```

## Kör Tester med Allure

### 1. Kör tester och generera Allure data:
```bash
pytest tests/test_api_contract.py tests/test_negative_cases.py --alluredir=reports/allure-results
```

### 2. Generera HTML rapport:
```bash
allure generate reports/allure-results -o reports/allure-report --clean
```

### 3. Öppna rapport i browser:
```bash
allure open reports/allure-report
```

## Eller allt i ett kommando:
```bash
pytest tests/ --alluredir=reports/allure-results && allure serve reports/allure-results
```

## Allure Features i Testerna

### Decorators:
- `@allure.feature('Feature Name')` - Gruppera tester per feature
- `@allure.story('Story Name')` - Gruppera tester per user story
- `@allure.severity(allure.severity_level.CRITICAL)` - Sätt severity (BLOCKER, CRITICAL, NORMAL, MINOR, TRIVIAL)

### Steps:
```python
with allure.step("Step description"):
    # Test code
```

### Attachments:
```python
allure.attach(response.text, name="Response", attachment_type=allure.attachment_type.JSON)
```

## Exempel från våra tester:

```python
@allure.feature('API Contract')
@allure.story('Authentication')
@allure.severity(allure.severity_level.CRITICAL)
def test_login_response_schema():
    with allure.step("Send login request"):
        response = requests.post(...)
    with allure.step("Validate response"):
        assert response.status_code == 200
```

## Allure Rapport Innehåll

Rapporten visar:
- ✅ Overview - Test statistics, trends
- 📊 Categories - Grupperade failures
- 🎯 Suites - Test suites och deras resultat
- 📈 Graphs - Visuella grafer
- ⏱️ Timeline - Test execution timeline
- 🔍 Behaviors - Features och stories
- 📦 Packages - Test organization

## Tips

1. **Kör regelbundet**: Generera rapporter efter varje test-körning
2. **Spara historik**: Allure kan visa trends över tid
3. **Dela rapporter**: HTML-rapporten kan delas med teamet
4. **CI/CD Integration**: Lägg till i GitHub Actions workflow

## Nästa Steg för CI/CD

Lägg till i `.github/workflows/test.yml`:
```yaml
- name: Run tests with Allure
  run: pytest tests/ --alluredir=reports/allure-results

- name: Upload Allure results
  uses: actions/upload-artifact@v3
  with:
    name: allure-results
    path: reports/allure-results
```
