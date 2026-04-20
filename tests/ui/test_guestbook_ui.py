"""UI Tests for Guestbook CRUD Operations"""

import pytest
from playwright.sync_api import Page, expect


def test_guestbook_page_loads(authenticated_page: Page):
    """Test that guestbook page loads with entries"""
    expect(authenticated_page.locator("h1")).to_contain_text("Guest Book")
    expect(authenticated_page.locator("#entriesTable")).to_be_visible()


def test_create_entry(authenticated_page: Page):
    """Test creating a new guestbook entry via UI"""
    page = authenticated_page
    page.fill("#name", "UI Test User")
    page.fill("#email", "uitest@example.com")
    page.fill("#comment", "This is a UI test comment")
    page.click("#entryForm button[type='submit']")
    page.wait_for_timeout(1000)
    expect(page.locator("text=UI Test User")).to_be_visible()


def test_edit_entry(authenticated_page: Page):
    """Test editing an existing entry"""
    page = authenticated_page
    # Create entry first
    page.fill("#name", "Edit Test")
    page.fill("#email", "edit@test.com")
    page.fill("#comment", "Original comment")
    page.click("#entryForm button[type='submit']")
    page.wait_for_timeout(1000)

    # Click edit button to open modal
    edit_button = page.locator('button:has-text("Edit")').first
    edit_button.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    edit_button.click()

    # Wait for modal to appear and fill form
    expect(page.locator("#editModal")).to_be_visible()
    page.fill("#editName", "Edited Name")
    page.fill("#editEmail", "edited@test.com")
    page.fill("#editComment", "Edited comment")

    # Submit the edit form
    page.click("#editForm button[type='submit']")
    page.wait_for_timeout(1000)

    # Verify the entry was updated
    expect(page.locator("text=Edited Name")).to_be_visible()


def test_delete_entry(authenticated_page: Page):
    """Test deleting an entry using the delete modal"""
    page = authenticated_page
    # Create entry first
    page.fill("#name", "Delete Test")
    page.fill("#email", "delete@test.com")
    page.fill("#comment", "Will be deleted")
    page.click("#entryForm button[type='submit']")
    page.wait_for_timeout(1000)

    # Click delete button to open modal
    delete_button = page.locator('button:has-text("Delete")').first
    delete_button.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    delete_button.click()

    # Wait for delete modal to appear
    expect(page.locator("#deleteModal")).to_be_visible()

    # Verify entry details are shown in modal
    expect(page.locator("#deleteEntryName")).to_contain_text("Delete Test")
    expect(page.locator("#deleteEntryEmail")).to_contain_text("delete@test.com")
    expect(page.locator("#deleteEntryComment")).to_contain_text("Will be deleted")

    # Confirm deletion
    page.click(".delete-confirm-btn")
    page.wait_for_timeout(1000)

    # Verify the entry was deleted
    expect(page.locator("text=Delete Test")).not_to_be_visible()


def test_delete_entry_cancel(authenticated_page: Page):
    """Test canceling delete operation"""
    page = authenticated_page
    # Create entry first
    page.fill("#name", "Cancel Delete Test")
    page.fill("#email", "canceldelete@test.com")
    page.fill("#comment", "Should not be deleted")
    page.click("#entryForm button[type='submit']")
    page.wait_for_timeout(1000)

    # Click delete button to open modal
    delete_button = page.locator('button:has-text("Delete")').first
    delete_button.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    delete_button.click()

    # Wait for delete modal to appear
    expect(page.locator("#deleteModal")).to_be_visible()

    # Cancel deletion
    # page.click("button:has-text('Cancel')")
    page.click("#deleteModal button:has-text('Cancel')")
    page.wait_for_timeout(500)

    # Verify modal is closed
    expect(page.locator("#deleteModal")).not_to_be_visible()

    # Verify the entry still exists
    expect(
        page.locator("#entriesTable td:has-text('Cancel Delete Test')")
    ).to_be_visible()


def test_delete_modal_close_x(authenticated_page: Page):
    """Test closing delete modal with X button"""
    page = authenticated_page
    # Create entry first
    page.fill("#name", "Close X Test")
    page.fill("#email", "closex@test.com")
    page.fill("#comment", "Test closing with X")
    page.click("#entryForm button[type='submit']")
    page.wait_for_timeout(1000)

    # Click delete button to open modal
    delete_button = page.locator('button:has-text("Delete")').first
    delete_button.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    delete_button.click()

    # Wait for delete modal to appear
    expect(page.locator("#deleteModal")).to_be_visible()

    # Close with X button
    page.click("#deleteModal .close")
    page.wait_for_timeout(500)

    # Verify modal is closed
    expect(page.locator("#deleteModal")).not_to_be_visible()

    # Verify the entry still exists
    expect(page.locator("#entriesTable td:has-text('Close X Test')")).to_be_visible()


def test_form_validation(authenticated_page: Page):
    """Test form validation for required fields"""
    page = authenticated_page
    page.click("#entryForm button[type='submit']")
    # HTML5 validation should prevent submission
    expect(page.locator("#name:invalid")).to_be_visible()
