# Playwright UI Testing Guide

## Installation

### 1. Installera Python Packages
```bash
pip install playwright pytest-playwright
```

### 2. Installera Browsers
```bash
# Installera alla browsers
playwright install

# Eller specifika browsers
playwright install chromium
playwright install firefox
playwright install webkit
```

## Grundläggande Användning

### Kör Tester
```bash
# Alla UI tester
pytest tests/ui/

# Med synlig browser
pytest tests/ui/ --headed

# Specifik browser
pytest tests/ui/ --browser firefox
pytest tests/ui/ --browser webkit
pytest tests/ui/ --browser chromium

# Slow motion (för debugging)
pytest tests/ui/ --headed --slowmo 500

# Med screenshots
pytest tests/ui/ --screenshot only-on-failure

# Med video
pytest tests/ui/ --video retain-on-failure
```

### Kör Specifika Tester
```bash
# En fil
pytest tests/ui/test_login_ui.py

# Ett test
pytest tests/ui/test_login_ui.py::test_successful_login

# Med verbose output
pytest tests/ui/ -v -s
```

## Playwright Inspector (Debugging)

### Starta Inspector
```bash
# Sätt environment variable
set PWDEBUG=1
pytest tests/ui/test_login_ui.py::test_successful_login
```

Inspector öppnas och du kan:
- Stega genom test steg för steg
- Inspektera element
- Testa selectors
- Se console logs

## Skriva Tester

### Basic Test Structure
```python
from playwright.sync_api import Page, expect

def test_example(page: Page):
    # Navigate
    page.goto("http://localhost:8080")
    
    # Interact
    page.fill("#username", "admin")
    page.click("button[type='submit']")
    
    # Assert
    expect(page).to_have_url("http://localhost:8080/guestbook")
    expect(page.locator("h1")).to_contain_text("Guest Book")
```

### Selectors
```python
# By ID
page.locator("#username")

# By class
page.locator(".error-message")

# By text
page.locator("text=Login")
page.locator("button:has-text('Submit')")

# By CSS
page.locator("button[type='submit']")

# By XPath
page.locator("xpath=//button[@type='submit']")

# Chaining
page.locator("#form").locator("button")
```

### Actions
```python
# Click
page.click("button")

# Fill input
page.fill("#username", "admin")

# Type (with delay)
page.type("#username", "admin", delay=100)

# Select dropdown
page.select_option("#country", "Sweden")

# Check/uncheck
page.check("#agree")
page.uncheck("#agree")

# Upload file
page.set_input_files("#file", "path/to/file.xlsx")

# Hover
page.hover("#menu")

# Double click
page.dblclick("#item")

# Right click
page.click("#item", button="right")
```

### Waiting
```python
# Wait for selector
page.wait_for_selector("#element")

# Wait for URL
page.wait_for_url("http://localhost:8080/guestbook")

# Wait for load state
page.wait_for_load_state("networkidle")

# Wait for timeout (använd sparsamt)
page.wait_for_timeout(1000)

# Wait for function
page.wait_for_function("() => document.title === 'Guest Book'")
```

### Assertions (expect)
```python
from playwright.sync_api import expect

# URL
expect(page).to_have_url("http://localhost:8080")
expect(page).to_have_url(/.*guestbook/)

# Title
expect(page).to_have_title("Guest Book")

# Element visibility
expect(page.locator("#element")).to_be_visible()
expect(page.locator("#element")).to_be_hidden()

# Element state
expect(page.locator("button")).to_be_enabled()
expect(page.locator("button")).to_be_disabled()

# Text content
expect(page.locator("h1")).to_contain_text("Guest Book")
expect(page.locator("h1")).to_have_text("Guest Book")

# Input value
expect(page.locator("#username")).to_have_value("admin")

# Count
expect(page.locator("tr")).to_have_count(10)

# Attribute
expect(page.locator("button")).to_have_attribute("type", "submit")
```

### Hantera Dialogs
```python
# Accept dialog
page.on("dialog", lambda dialog: dialog.accept())
page.click("button:has-text('Delete')")

# Dismiss dialog
page.on("dialog", lambda dialog: dialog.dismiss())

# Get dialog message
def handle_dialog(dialog):
    print(dialog.message)
    dialog.accept()

page.on("dialog", handle_dialog)
```

### Screenshots
```python
# Full page
page.screenshot(path="screenshot.png")

# Element
page.locator("#element").screenshot(path="element.png")

# Full page with scroll
page.screenshot(path="full.png", full_page=True)
```

### Multiple Browsers
```python
@pytest.mark.parametrize("browser_name", ["chromium", "firefox", "webkit"])
def test_cross_browser(browser_name, playwright):
    browser = getattr(playwright, browser_name).launch()
    page = browser.new_page()
    page.goto("http://localhost:8080")
    # Test...
    browser.close()
```

## Fixtures

### Använd authenticated_page
```python
def test_something(authenticated_page: Page):
    # Redan inloggad
    authenticated_page.fill("#name", "Test")
```

### Custom Fixtures
```python
# I conftest.py
@pytest.fixture
def test_data(page: Page):
    # Setup test data
    return {"name": "Test", "email": "test@example.com"}

# I test
def test_with_data(authenticated_page: Page, test_data):
    authenticated_page.fill("#name", test_data["name"])
```

## Best Practices

### 1. Använd Data-Testid
```html
<button data-testid="submit-btn">Submit</button>
```
```python
page.locator("[data-testid='submit-btn']").click()
```

### 2. Vänta På Network Idle
```python
page.goto("http://localhost:8080", wait_until="networkidle")
```

### 3. Isolera Tester
Varje test ska vara oberoende och kunna köras i vilken ordning som helst.

### 4. Cleanup
```python
def test_something(authenticated_page: Page):
    # Test...
    # Cleanup sker automatiskt mellan tester
```

### 5. Använd Fixtures För Återanvändning
Skapa fixtures för vanliga operationer.

## Troubleshooting

### Browser Inte Installerad
```bash
playwright install
```

### Timeout Errors
```python
# Öka timeout
page.set_default_timeout(30000)  # 30 sekunder
```

### Element Inte Hittad
```python
# Vänta på element
page.wait_for_selector("#element", state="visible")
```

### App Inte Igång
Starta Flask app:
```bash
python src/app.py
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Install Playwright
  run: |
    pip install playwright pytest-playwright
    playwright install --with-deps

- name: Run UI Tests
  run: pytest tests/ui/ --browser chromium
```

## Resurser
- [Playwright Documentation](https://playwright.dev/python/)
- [pytest-playwright](https://github.com/microsoft/playwright-pytest)
- [Playwright Inspector](https://playwright.dev/python/docs/debug)
