"""UI Tests for Delete Modal Functionality"""

import pytest
from playwright.sync_api import Page, expect


def test_delete_modal_opens_correctly(authenticated_page: Page):
    """Test that delete modal opens and displays correct information"""
    page = authenticated_page

    # Create a test entry
    # page.wait_for_selector("#name", state="visible")
    page.fill("#name", "Modal Test User")
    page.fill("#email", "modaltest@example.com")
    page.fill("#comment", "Testing delete modal functionality")
    page.click("#entryForm button[type='submit']")
    page.wait_for_timeout(1000)

    # Click delete button
    delete_button = page.locator("button.delete-btn").first
    delete_button.click()

    # Verify modal is visible
    expect(page.locator("#deleteModal")).to_be_visible()

    # Verify modal title
    expect(page.locator("#deleteModal .modal-title")).to_contain_text("Delete Entry")

    # Verify entry details are displayed
    expect(page.locator("#deleteEntryName")).to_contain_text("Modal Test User")
    expect(page.locator("#deleteEntryEmail")).to_contain_text("modaltest@example.com")
    expect(page.locator("#deleteEntryComment")).to_contain_text(
        "Testing delete modal functionality"
    )

    # Verify warning text is present
    expect(page.locator(".warning-text")).to_contain_text(
        "This action cannot be undone"
    )


def test_delete_modal_cancel_button(authenticated_page: Page):
    """Test that cancel button closes modal without deleting"""
    page = authenticated_page

    # Create a test entry
    page.fill("#name", "Cancel Test User")
    page.fill("#email", "canceltest@example.com")
    page.fill("#comment", "This should not be deleted")
    page.click("#entryForm button[type='submit']")
    page.wait_for_timeout(1000)

    # Click delete button to open modal
    delete_button = page.locator("button.delete-btn").first
    delete_button.click()

    # Verify modal is open
    expect(page.locator("#deleteModal")).to_be_visible()

    # Click cancel button
    page.click("#deleteModal button:has-text('Cancel')")
    page.wait_for_timeout(500)

    # Verify modal is closed
    expect(page.locator("#deleteModal")).not_to_be_visible()

    # Verify entry still exists
    expect(page.locator("#entriesBody td:has-text('Cancel Test User')")).to_be_visible()


def test_delete_modal_x_button(authenticated_page: Page):
    """Test that X button closes modal without deleting"""
    page = authenticated_page

    # Create a test entry
    page.fill("#name", "X Button Test")
    page.fill("#email", "xbuttontest@example.com")
    page.fill("#comment", "Testing X button close")
    page.click("#entryForm button[type='submit']")
    page.wait_for_timeout(1000)

    # Click delete button to open modal
    delete_button = page.locator("button.delete-btn").first
    delete_button.click()

    # Verify modal is open
    expect(page.locator("#deleteModal")).to_be_visible()

    # Click X button
    page.click("#deleteModal .close")
    page.wait_for_timeout(500)

    # Verify modal is closed
    expect(page.locator("#deleteModal")).not_to_be_visible()

    # Verify entry still exists
    # expect(page.locator("text=X Button Test")).to_be_visible()
    expect(page.locator("#entriesBody td:has-text('X Button Test')")).to_be_visible()


def test_delete_modal_click_outside(authenticated_page: Page):
    """Test that clicking outside modal closes it without deleting"""
    page = authenticated_page

    # Create a test entry
    page.fill("#name", "Click Outside Test")
    page.fill("#email", "clickoutside@example.com")
    page.fill("#comment", "Testing click outside")
    page.click("#entryForm button[type='submit']")
    page.wait_for_timeout(1000)

    # Click delete button to open modal
    delete_button = page.locator("button.delete-btn").first
    delete_button.click()

    # Verify modal is open
    expect(page.locator("#deleteModal")).to_be_visible()

    # Click outside modal (on the modal backdrop)
    page.click("#deleteModal", position={"x": 10, "y": 10})
    page.wait_for_timeout(500)

    # Verify modal is closed
    expect(page.locator("#deleteModal")).not_to_be_visible()

    # Verify entry still exists
    # expect(page.locator("text=Click Outside Test")).to_be_visible()
    expect(
        page.locator("#entriesBody td:has-text('Click Outside Test')")
    ).to_be_visible()


def test_delete_modal_confirm_deletion(authenticated_page: Page):
    """Test that confirm button actually deletes the entry"""
    page = authenticated_page

    # Create a test entry
    page.fill("#name", "Confirm Delete Test")
    page.fill("#email", "confirmdelete@example.com")
    page.fill("#comment", "This will be deleted")
    page.click("#entryForm button[type='submit']")
    page.wait_for_timeout(1000)

    # Click delete button to open modal
    delete_button = page.locator("button.delete-btn").first
    delete_button.click()

    # Verify modal is open
    expect(page.locator("#deleteModal")).to_be_visible()

    # Click delete confirm button
    page.click(".delete-confirm-btn")
    page.wait_for_timeout(1000)

    # Verify modal is closed
    expect(page.locator("#deleteModal")).not_to_be_visible()

    # Verify entry is deleted
    expect(page.locator("text=Confirm Delete Test")).not_to_be_visible()


def test_delete_modal_with_empty_comment(authenticated_page: Page):
    """Test delete modal with entry that has no comment"""
    page = authenticated_page

    # Create entry via API directly (comment is required in UI form)
    token = page.evaluate("() => sessionStorage.getItem('token')")
    page.request.post(
        "http://localhost:8080/api/guestbook",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        data={
            "name": "No Comment User",
            "email": "nocomment@example.com",
            "comment": "",
        },
    )
    page.reload()
    page.wait_for_load_state("networkidle")

    # Click delete button to open modal
    delete_button = page.locator("button.delete-btn").first
    delete_button.click()

    # Verify modal is open
    expect(page.locator("#deleteModal")).to_be_visible()

    # Verify entry details are displayed (comment should show "No comment")
    expect(page.locator("#deleteEntryName")).to_contain_text("No Comment User")
    expect(page.locator("#deleteEntryEmail")).to_contain_text("nocomment@example.com")
    expect(page.locator("#deleteEntryComment")).to_contain_text("No comment")


def test_delete_modal_styling(authenticated_page: Page):
    """Test that delete modal has correct styling"""
    page = authenticated_page

    # Create a test entry
    page.fill("#name", "Style Test User")
    page.fill("#email", "styletest@example.com")
    page.fill("#comment", "Testing modal styling")
    page.click("#entryForm button[type='submit']")
    page.wait_for_timeout(1000)

    # Click delete button to open modal
    delete_button = page.locator("button.delete-btn").first
    delete_button.click()

    # Verify modal elements have correct classes
    expect(page.locator("#deleteModal")).to_have_class("modal")
    expect(page.locator("#deleteModal .modal-content")).to_be_visible()
    expect(page.locator("#deleteModal .modal-header")).to_be_visible()
    expect(page.locator("#deleteModal .modal-body")).to_be_visible()
    expect(page.locator("#deleteModal .modal-buttons")).to_be_visible()
    expect(page.locator("#deleteModal .entry-preview")).to_be_visible()
    expect(page.locator("#deleteModal .delete-confirm-btn")).to_be_visible()


@pytest.mark.skip(reason="Work in progress")
def test_multiple_delete_modals_not_interfering(authenticated_page: Page):
    """Test that multiple entries can be deleted without modal interference"""
    page = authenticated_page

    # Create two test entries
    page.fill("#name", "First Delete User")
    page.fill("#email", "first@example.com")
    page.fill("#comment", "First entry to delete")
    page.click("#entryForm button[type='submit']")
    page.wait_for_timeout(500)

    page.fill("#name", "Second Delete User")
    page.fill("#email", "second@example.com")
    page.fill("#comment", "Second entry to delete")
    page.click("#entryForm button[type='submit']")
    page.wait_for_timeout(1000)

    # Delete first entry
    first_delete_button = page.locator("button.delete-btn").first
    first_delete_button.click()

    expect(page.locator("#deleteModal")).to_be_visible()
    expect(page.locator("#deleteEntryName")).to_contain_text(
        "Second Delete User"
    )  # Should be the most recent

    page.click(".delete-confirm-btn")
    page.wait_for_timeout(1000)

    # Delete second entry
    second_delete_button = page.locator("button.delete-btn").first
    second_delete_button.click()

    expect(page.locator("#deleteModal")).to_be_visible()
    expect(page.locator("#deleteEntryName")).to_contain_text("First Delete User")

    page.click(".delete-confirm-btn")
    page.wait_for_timeout(1000)

    # Verify both entries are deleted
    expect(page.locator("text=First Delete User")).not_to_be_visible()
    expect(page.locator("text=Second Delete User")).not_to_be_visible()
