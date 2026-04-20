"""UI Tests for Login Flow"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8080"


def test_login_page_loads(page: Page):
    """Test that login page loads correctly"""
    page.goto(BASE_URL)
    expect(page).to_have_title("Login - Guest Book")
    expect(page.locator("h1")).to_contain_text("Login")


def test_successful_login(page: Page):
    """Test successful login flow"""
    page.goto(BASE_URL)
    page.fill("#identifier", "admin")
    page.fill("#password", "password123")
    page.click("button[type='submit']")
    page.wait_for_url(f"{BASE_URL}/guestbook")
    expect(page).to_have_url(f"{BASE_URL}/guestbook")
    expect(page.locator("h1")).to_contain_text("Guest Book")


def test_failed_login_wrong_password(page: Page):
    """Test login with wrong password"""
    page.goto(BASE_URL)
    page.fill("#identifier", "admin")
    page.fill("#password", "wrongpassword")
    page.click("button[type='submit']")
    expect(page.locator(".error")).to_be_visible()


def test_failed_login_empty_identifier(page: Page):
    """Test login with empty identifier"""
    page.goto(BASE_URL)
    page.fill("#password", "password123")
    page.click("button[type='submit']")
    expect(page.locator(".error")).to_have_text("Please enter your email or username")


def test_failed_login_empty_password(page: Page):
    """Test login with empty password"""
    page.goto(BASE_URL)
    page.fill("#identifier", "admin")
    page.click("button[type='submit']")
    expect(page.locator(".error")).to_have_text("Please enter your password")


def test_failed_login_empty_fields(page: Page):
    """Test login with empty fields"""
    page.goto(BASE_URL)
    page.click("button[type='submit']")
    expect(page.locator(".error")).to_have_text("Please enter your email or username")


def test_logout(authenticated_page: Page):
    """Test logout functionality"""
    page = authenticated_page
    page.wait_for_url(f"{BASE_URL}/guestbook")
    page.click(".logout-btn")
    page.wait_for_url(BASE_URL)
    expect(page).to_have_url(BASE_URL + "/")
