"""UI Tests for Dark Mode Toggle (DEV-14)"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8080"
PAGES_WITH_TOGGLE = [
    ("/login", "Login - Guest Book"),
    ("/register", "Register - Guest Book"),
    ("/reset-password-request", "Forgot Password - Guest Book"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _has_dark_mode(page: Page) -> bool:
    """Return True if dark-mode class is present on html element."""
    return page.evaluate("document.documentElement.classList.contains('dark-mode')")


def _get_saved_preference(page: Page) -> str | None:
    """Return the localStorage darkMode value."""
    return page.evaluate("localStorage.getItem('darkMode')")


def _clear_dark_mode_preference(page: Page) -> None:
    """Remove dark mode preference from localStorage."""
    page.evaluate("localStorage.removeItem('darkMode')")


# ---------------------------------------------------------------------------
# Toggle visibility on all pages
# ---------------------------------------------------------------------------


@pytest.mark.ui
def test_toggle_visible_on_login_page(page: Page):
    """Dark mode toggle button is visible on the login page."""
    page.goto(f"{BASE_URL}/login")
    toggle = page.locator("#darkModeToggle")
    expect(toggle).to_be_visible()


@pytest.mark.ui
def test_toggle_visible_on_register_page(page: Page):
    """Dark mode toggle button is visible on the register page."""
    page.goto(f"{BASE_URL}/register")
    toggle = page.locator("#darkModeToggle")
    expect(toggle).to_be_visible()


@pytest.mark.ui
def test_toggle_visible_on_reset_password_request_page(page: Page):
    """Dark mode toggle button is visible on the forgot password page."""
    page.goto(f"{BASE_URL}/reset-password-request")
    toggle = page.locator("#darkModeToggle")
    expect(toggle).to_be_visible()


@pytest.mark.ui
def test_toggle_visible_on_guestbook_page(authenticated_page: Page):
    """Dark mode toggle button is visible on the guestbook page."""
    toggle = authenticated_page.locator("#darkModeToggle")
    expect(toggle).to_be_visible()


# ---------------------------------------------------------------------------
# Default is light mode
# ---------------------------------------------------------------------------


@pytest.mark.ui
def test_default_mode_is_light(page: Page):
    """New users see light mode by default (no dark-mode class on body)."""
    page.goto(f"{BASE_URL}/login")
    _clear_dark_mode_preference(page)
    page.reload()
    page.wait_for_load_state("networkidle")
    assert not _has_dark_mode(page), "Dark mode should NOT be active by default"


# ---------------------------------------------------------------------------
# Toggle switches between modes
# ---------------------------------------------------------------------------


@pytest.mark.ui
def test_toggle_activates_dark_mode(page: Page):
    """Clicking the toggle adds dark-mode class to body."""
    page.goto(f"{BASE_URL}/login")
    _clear_dark_mode_preference(page)
    page.reload()
    page.wait_for_load_state("networkidle")
    assert not _has_dark_mode(page)
    page.click("#darkModeToggle")
    assert _has_dark_mode(page), "dark-mode class should be on body after toggle click"


@pytest.mark.ui
def test_toggle_deactivates_dark_mode(page: Page):
    """Clicking the toggle twice returns to light mode."""
    page.goto(f"{BASE_URL}/login")
    _clear_dark_mode_preference(page)
    page.reload()
    page.wait_for_load_state("networkidle")
    page.click("#darkModeToggle")  # enable
    assert _has_dark_mode(page)
    page.click("#darkModeToggle")  # disable
    assert not _has_dark_mode(page), "dark-mode class should be removed after second click"


# ---------------------------------------------------------------------------
# localStorage persistence
# ---------------------------------------------------------------------------


@pytest.mark.ui
def test_preference_saved_to_localstorage_on_enable(page: Page):
    """Enabling dark mode saves 'enabled' to localStorage."""
    page.goto(f"{BASE_URL}/login")
    _clear_dark_mode_preference(page)
    page.reload()
    page.wait_for_load_state("networkidle")
    page.click("#darkModeToggle")
    assert _get_saved_preference(page) == "enabled"


@pytest.mark.ui
def test_preference_saved_to_localstorage_on_disable(page: Page):
    """Disabling dark mode saves 'disabled' to localStorage."""
    page.goto(f"{BASE_URL}/login")
    _clear_dark_mode_preference(page)
    page.reload()
    page.wait_for_load_state("networkidle")
    page.click("#darkModeToggle")  # enable
    page.click("#darkModeToggle")  # disable
    assert _get_saved_preference(page) == "disabled"


@pytest.mark.ui
def test_dark_mode_persists_after_page_reload(page: Page):
    """Dark mode preference is restored after page reload."""
    page.goto(f"{BASE_URL}/login")
    _clear_dark_mode_preference(page)
    page.reload()
    page.wait_for_load_state("networkidle")
    page.click("#darkModeToggle")  # enable
    assert _has_dark_mode(page)
    page.reload()
    page.wait_for_load_state("networkidle")
    assert _has_dark_mode(page), "Dark mode should persist after reload"


@pytest.mark.ui
def test_light_mode_persists_after_page_reload(page: Page):
    """Light mode preference is restored after page reload."""
    page.goto(f"{BASE_URL}/login")
    # Set to disabled explicitly
    page.evaluate("localStorage.setItem('darkMode', 'disabled')")
    page.reload()
    page.wait_for_load_state("networkidle")
    assert not _has_dark_mode(page), "Light mode should persist after reload"


@pytest.mark.ui
def test_dark_mode_persists_across_pages(page: Page):
    """Dark mode preference carries over when navigating to another page."""
    page.goto(f"{BASE_URL}/login")
    _clear_dark_mode_preference(page)
    page.reload()
    page.wait_for_load_state("networkidle")
    page.click("#darkModeToggle")  # enable on login page
    page.goto(f"{BASE_URL}/register")
    page.wait_for_load_state("networkidle")
    assert _has_dark_mode(page), "Dark mode should persist when navigating to a different page"


# ---------------------------------------------------------------------------
# Persistence across logout/login
# ---------------------------------------------------------------------------


@pytest.mark.ui
def test_dark_mode_persists_after_logout_and_login(page: Page):
    """Dark mode preference survives a logout and re-login cycle."""
    # Login first
    page.goto(f"{BASE_URL}/login")
    _clear_dark_mode_preference(page)
    page.reload()
    page.wait_for_load_state("networkidle")
    page.fill("#identifier", "admin")
    page.fill("#password", "password123")
    page.click("button[type='submit']")
    page.wait_for_url(f"{BASE_URL}/guestbook")
    page.wait_for_load_state("networkidle")

    # Enable dark mode on guestbook
    page.click("#darkModeToggle")
    page.wait_for_function("document.documentElement.classList.contains('dark-mode')")

    # Logout
    page.click(".logout-btn")
    # logout() redirects to '/' which serves the login page
    page.wait_for_url(f"{BASE_URL}/")
    page.wait_for_selector("#darkModeToggle", state="visible")
    # Inline head script applies dark-mode before first paint — wait for it
    page.wait_for_function("document.documentElement.classList.contains('dark-mode')")

    # Re-login
    page.fill("#identifier", "admin")
    page.fill("#password", "password123")
    page.click("button[type='submit']")
    page.wait_for_url(f"{BASE_URL}/guestbook")
    page.wait_for_selector("#darkModeToggle", state="visible")
    page.wait_for_function("document.documentElement.classList.contains('dark-mode')")


# ---------------------------------------------------------------------------
# UI elements readable in dark mode
# ---------------------------------------------------------------------------


@pytest.mark.ui
def test_toggle_icon_changes_in_dark_mode(page: Page):
    """Toggle button shows sun icon in dark mode and moon in light mode."""
    page.goto(f"{BASE_URL}/login")
    _clear_dark_mode_preference(page)
    page.reload()
    page.wait_for_load_state("networkidle")

    toggle = page.locator("#darkModeToggle")
    # Light mode: should show moon emoji
    assert "🌙" in toggle.inner_text()

    page.click("#darkModeToggle")
    # Dark mode: should show sun emoji
    assert "☀️" in toggle.inner_text()


@pytest.mark.ui
def test_form_inputs_visible_in_dark_mode(page: Page):
    """Login form inputs are still visible after enabling dark mode."""
    page.goto(f"{BASE_URL}/login")
    _clear_dark_mode_preference(page)
    page.reload()
    page.wait_for_load_state("networkidle")
    page.click("#darkModeToggle")

    expect(page.locator("#identifier")).to_be_visible()
    expect(page.locator("#password")).to_be_visible()
    expect(page.locator("button[type='submit']")).to_be_visible()
