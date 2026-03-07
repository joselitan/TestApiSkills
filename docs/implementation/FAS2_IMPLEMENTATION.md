# Fas 2: UI Testing Implementation

## Översikt
Fas 2 implementerar komplett UI testing med Playwright för end-to-end testing av frontend.

## Implementerade Komponenter

### 1. Playwright Setup
- **Dependencies**: playwright>=1.40.0, pytest-playwright>=0.4.0
- **Installation**: `pip install -r requirements.txt && playwright install`

### 2. Test Struktur
```
tests/ui/
├── conftest.py              # Playwright fixtures
├── test_login_ui.py         # Login flow tests (5 tests)
├── test_guestbook_ui.py     # CRUD operations (5 tests)
├── test_search_ui.py        # Search functionality (3 tests)
└── test_pagination_ui.py    # Pagination tests (3 tests)
```

### 3. Test Cases

#### Login Tests (test_login_ui.py)
- ✅ test_login_page_loads - Verify login page loads
- ✅ test_successful_login - Test successful authentication
- ✅ test_failed_login_wrong_password - Test wrong password
- ✅ test_failed_login_empty_fields - Test empty form validation
- ✅ test_logout - Test logout functionality

#### Guestbook CRUD Tests (test_guestbook_ui.py)
- ✅ test_guestbook_page_loads - Verify page loads
- ✅ test_create_entry - Create new entry via UI
- ✅ test_edit_entry - Edit existing entry
- ✅ test_delete_entry - Delete entry with confirmation
- ✅ test_form_validation - Test required field validation

#### Search Tests (test_search_ui.py)
- ✅ test_search_entries - Search for entries
- ✅ test_clear_search - Clear search results
- ✅ test_search_no_results - Handle no results

#### Pagination Tests (test_pagination_ui.py)
- ✅ test_pagination_navigation - Navigate pages
- ✅ test_pagination_with_search - Pagination with search
- ✅ test_pagination_buttons_disabled - Button states

## Användning

### Installera Playwright Browsers
```bash
playwright install
```

### Kör Alla UI Tester
```bash
pytest tests/ui/ -v
```

### Kör Med Synlig Browser (Headed Mode)
```bash
pytest tests/ui/ --headed
```

### Kör Specifik Browser
```bash
pytest tests/ui/ --browser firefox
pytest tests/ui/ --browser webkit
```

### Kör Med Slow Motion (För Debugging)
```bash
pytest tests/ui/ --headed --slowmo 1000
```

### Kör Specifik Test Fil
```bash
pytest tests/ui/test_login_ui.py -v
```

### Kör Med Screenshots Vid Failure
```bash
pytest tests/ui/ --screenshot on
```

### Kör Med Video Recording
```bash
pytest tests/ui/ --video on
```

## Fixtures

### authenticated_page
Fixture som ger en redan inloggad sida:
```python
def test_something(authenticated_page: Page):
    # Page är redan inloggad på /guestbook
    authenticated_page.fill("#name", "Test")
```

## Konfiguration

### pytest.ini
Lagt till UI marker:
```ini
markers =
    ui: marks tests as UI tests
```

Kör endast UI tester:
```bash
pytest -m ui
```

## Best Practices

### 1. Vänta På Element
```python
page.wait_for_selector("#element")
page.wait_for_url("http://localhost:8080/guestbook")
page.wait_for_timeout(1000)  # Använd sparsamt
```

### 2. Använd expect() För Assertions
```python
from playwright.sync_api import expect
expect(page.locator("h1")).to_contain_text("Guest Book")
expect(page).to_have_url("http://localhost:8080")
```

### 3. Hantera Dialogs
```python
page.on("dialog", lambda dialog: dialog.accept())
page.click("button:has-text('Delete')")
```

## Troubleshooting

### Problem: Browser Inte Installerad
```bash
playwright install chromium
```

### Problem: Timeout Errors
Öka timeout i conftest.py:
```python
@pytest.fixture(scope="session")
def browser_context_args():
    return {"timeout": 30000}
```

### Problem: App Inte Igång
Starta Flask app först:
```bash
python src/app.py
```

## Nästa Steg

### Fas 2.2: Visual Regression Testing
- Implementera screenshot comparison
- Baseline screenshots
- Diff reports

### Fas 2.3: Accessibility Testing
- axe-core integration
- WCAG 2.1 compliance
- Keyboard navigation tests

### Fas 2.4: Cross-Browser Testing
- Matrix testing (Chrome, Firefox, Safari)
- Mobile browser testing
- Responsive design tests

## Resultat
✅ 16 UI test cases implementerade
✅ Täcker login, CRUD, search, pagination
✅ Playwright fixtures för återanvändning
✅ Dokumentation och best practices
