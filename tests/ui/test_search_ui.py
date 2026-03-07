"""UI Tests for Search Functionality"""
import pytest
from playwright.sync_api import Page, expect

def test_search_entries(authenticated_page: Page):
    """Test searching for entries"""
    page = authenticated_page
    page.fill("#searchInput", "Alice")
    page.click("button:has-text('Search')")
    page.wait_for_timeout(1000)
    expect(page.locator("text=Alice")).to_be_visible()

def test_clear_search(authenticated_page: Page):
    """Test clearing search results"""
    page = authenticated_page
    page.fill("#searchInput", "Alice")
    page.click("button:has-text('Search')")
    page.wait_for_timeout(1000)
    page.click("button:has-text('Clear')")
    page.wait_for_timeout(1000)
    expect(page.locator("#searchInput")).to_have_value("")

def test_search_no_results(authenticated_page: Page):
    """Test search with no matching results"""
    page = authenticated_page
    page.fill("#searchInput", "NonExistentUser12345")
    page.click("button:has-text('Search')")
    page.wait_for_timeout(1000)
    # Should show empty table or no results message
    rows = page.locator("#entriesBody tr").count()
    assert rows == 0 or page.locator("text=No entries found").is_visible()
