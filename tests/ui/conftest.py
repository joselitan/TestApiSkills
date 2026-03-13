"""Playwright fixtures for UI testing"""

import pytest
from playwright.sync_api import Page

BASE_URL = "http://localhost:8080"


@pytest.fixture(scope="function")
def authenticated_page(page: Page):
    """Fixture that provides an authenticated page"""
    page.goto(BASE_URL)
    page.fill("#username", "admin")
    page.fill("#password", "password123")
    page.click("button[type='submit']")
    page.wait_for_url(f"{BASE_URL}/guestbook")
    return page
