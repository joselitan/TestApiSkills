"""Unit Tests for Test Data Factories"""

import pytest

from tests.fixtures.factories import (
    create_guestbook_entry,
    create_invalid_entry,
    create_multiple_entries,
    create_user_credentials,
)


class TestDataFactories:
    """Test the test data factory functions"""

    def test_create_guestbook_entry(self):
        """Test guestbook entry creation"""
        entry = create_guestbook_entry()

        assert "name" in entry
        assert "email" in entry
        assert "comment" in entry

        assert isinstance(entry["name"], str)
        assert isinstance(entry["email"], str)
        assert isinstance(entry["comment"], str)

        assert "@" in entry["email"]
        assert len(entry["name"]) > 0
        assert len(entry["comment"]) <= 200

    def test_create_multiple_entries(self):
        """Test multiple entries creation"""
        entries = create_multiple_entries(3)

        assert len(entries) == 3
        assert all("name" in entry for entry in entries)
        assert all("email" in entry for entry in entries)
        assert all("comment" in entry for entry in entries)

    def test_create_user_credentials(self):
        """Test user credentials creation"""
        creds = create_user_credentials()

        assert "username" in creds
        assert "password" in creds

        assert isinstance(creds["username"], str)
        assert isinstance(creds["password"], str)

        assert len(creds["username"]) > 0
        assert len(creds["password"]) >= 12

    def test_create_invalid_entry(self):
        """Test invalid entry creation for negative testing"""
        entry = create_invalid_entry()

        assert "name" in entry
        assert "email" in entry
        assert "comment" in entry

        # Should contain invalid data types
        assert isinstance(entry["name"], int)  # Should be string
        assert entry["email"] == "not-an-email"  # Invalid format
        assert entry["comment"] is None  # Should not be None

    def test_entries_are_unique(self):
        """Test that generated entries are unique"""
        entries = create_multiple_entries(5)

        # Check that names are different (very likely with Faker)
        names = [entry["name"] for entry in entries]
        assert len(set(names)) > 1  # At least some should be different

        # Check that emails are different
        emails = [entry["email"] for entry in entries]
        assert len(set(emails)) > 1  # At least some should be different
