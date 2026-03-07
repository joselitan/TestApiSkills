"""UI Tests for Pagination"""
import pytest
from playwright.sync_api import Page, expect

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

def test_pagination_buttons_disabled(authenticated_page: Page):
    """Test that pagination buttons are disabled appropriately"""
    page = authenticated_page
    # On first page, Previous should be disabled
    expect(page.locator("button:has-text('Previous')")).to_be_disabled()
