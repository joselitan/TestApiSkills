"""UI Tests for Pagination"""

import pytest
import requests
from playwright.sync_api import Page, expect


def cleanup_all_entries_via_api(page: Page):
    """Remove all entries from guestbook using the cleanup API endpoint"""
    token = page.evaluate("() => sessionStorage.getItem('token')")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    base_url = "http://localhost:8080"

    # Use the new cleanup API endpoint with test_mode=true
    requests.delete(f"{base_url}/api/guestbook/cleanup?test_mode=true", headers=headers)


def seed_test_entries(page: Page, count: int = 15):
    """Helper function to quickly create test entries via API"""
    # Get token from browser session
    token = page.evaluate("() => sessionStorage.getItem('token')")

    # Sample test data
    test_data = [
        ("Alice Smith", "alice@example.com", "Just checking out the site!"),
        ("Bob Jones", "bob@test.co", "Great API documentation."),
        ("Charlie Day", "charlie@mail.com", "I found a bug in the matrix."),
        ("Dana White", "dana@ufc.com", "Testing the pagination feature."),
        ("Eve Polastri", "eve@mi6.gov.uk", "Has anyone seen Villanelle?"),
        ("Frank Castle", "frank@punisher.com", "Justice will be served."),
        (
            "Grace Hopper",
            "grace@navy.mil",
            "It's easier to ask forgiveness than permission.",
        ),
        (
            "Henry Ford",
            "henry@ford.com",
            "Whether you think you can or can't, you're right.",
        ),
        ("Iris West", "iris@ccpn.com", "We are the Flash!"),
        ("Jack Ryan", "jack@cia.gov", "Analyzing the threat landscape."),
        ("Karen Page", "karen@bulletin.com", "The truth matters."),
        ("Luke Cage", "luke@harlem.com", "Sweet Christmas!"),
        ("Maya Lopez", "maya@echo.com", "Actions speak louder than words."),
        ("Natasha Romanoff", "natasha@shield.gov", "I've got red in my ledger."),
        ("Oliver Queen", "oliver@queenind.com", "You have failed this city!"),
        (
            "Peter Parker",
            "peter@dailybugle.com",
            "With great power comes great responsibility.",
        ),
        ("Quinn Fabray", "quinn@mckinley.edu", "I'm more than just a pretty face."),
        (
            "Rachel Green",
            "rachel@centralperk.com",
            "It's like all my life everyone has told me...",
        ),
        ("Steve Rogers", "steve@avengers.org", "I can do this all day."),
        ("Tony Stark", "tony@starkindustries.com", "I am Iron Man."),
    ]

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    base_url = "http://localhost:8080"

    # Create entries via API
    for i in range(min(count, len(test_data))):
        name, email, comment = test_data[i]
        payload = {"name": name, "email": email, "comment": comment}
        requests.post(f"{base_url}/api/guestbook", json=payload, headers=headers)


def test_pagination_with_search(authenticated_page: Page):
    """Test that pagination works with search"""
    page = authenticated_page
    page.fill("#searchInput", "test")
    page.click("button:has-text('Search')")
    page.wait_for_timeout(1000)

    # Pagination should still work
    if page.locator("button:has-text('Next')").is_enabled():
        page.click("button:has-text('Next')")
        page.wait_for_timeout(1000)
        expect(page.locator("#pageInfo")).to_contain_text("Page 2")


def test_pagination_buttons_disabled_on_first_page(authenticated_page: Page):
    """Test that Previous button is disabled on first page"""
    page = authenticated_page
    # On first page, Previous should be disabled
    expect(page.locator("button:has-text('Previous')")).to_be_disabled()


def test_pagination_buttons_disabled_with_few_entries(authenticated_page: Page):
    """Test that Next button is disabled when total entries <= 10"""
    page = authenticated_page

    # Clear all existing entries via API
    cleanup_all_entries_via_api(page)

    # Add only 5 entries (less than 10)
    for i in range(5):
        page.fill("#name", f"Test User {i+1}")
        page.fill("#email", f"test{i+1}@example.com")
        page.fill("#comment", f"Test comment {i+1}")
        page.click("#entryForm button[type='submit']")
        page.wait_for_timeout(500)

    # Reload entries to update pagination
    page.reload()
    page.wait_for_timeout(1000)

    # Next button should be disabled (only 1 page with 5 entries)
    expect(page.locator("button:has-text('Next')")).to_be_disabled()
    expect(page.locator("#pageInfo")).to_contain_text("Page 1 of 1")


def test_pagination_buttons_enabled_with_many_entries(authenticated_page: Page):
    """Test that Next button is enabled when total entries > 10"""
    page = authenticated_page

    # Clear all existing entries via API
    cleanup_all_entries_via_api(page)

    # Add 15 entries via API (much faster than UI)
    seed_test_entries(page, 15)

    # Reload entries to update pagination
    page.reload()
    page.wait_for_timeout(1000)

    # Next button should be enabled (2 pages with 15 entries)
    expect(page.locator("button:has-text('Next')")).to_be_enabled()
    expect(page.locator("#pageInfo")).to_contain_text("Page 1 of 2")

    # Go to page 2
    page.click("button:has-text('Next')")
    page.wait_for_timeout(1000)

    # On last page, Next should be disabled
    expect(page.locator("button:has-text('Next')")).to_be_disabled()
    expect(page.locator("#pageInfo")).to_contain_text("Page 2 of 2")


def test_pagination_navigation(authenticated_page: Page):
    """Test navigating through pages"""
    page = authenticated_page
    expect(page.locator("#pageInfo")).to_be_visible()

    # Click next page
    page.click("button:has-text('Next')")
    page.wait_for_timeout(1000)
    expect(page.locator("#pageInfo")).to_contain_text("Page 2")

    # Click previous page
    page.click("button:has-text('Previous')")
    page.wait_for_timeout(1000)
    expect(page.locator("#pageInfo")).to_contain_text("Page 1")
