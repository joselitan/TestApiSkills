"""Test Data Factory - Generate realistic test data using Faker"""
from faker import Faker

fake = Faker()

def create_guestbook_entry():
    """Generate a single guestbook entry with realistic data"""
    return {
        "name": fake.name(),
        "email": fake.email(),
        "comment": fake.text(max_nb_chars=200)
    }

def create_multiple_entries(count=5):
    """Generate multiple guestbook entries"""
    return [create_guestbook_entry() for _ in range(count)]

def create_user_credentials():
    """Generate user login credentials"""
    return {
        "username": fake.user_name(),
        "password": fake.password(length=12)
    }

def create_invalid_entry():
    """Generate invalid test data for negative testing"""
    return {
        "name": fake.pyint(),  # Invalid: should be string
        "email": "not-an-email",  # Invalid format
        "comment": None  # Invalid: required field
    }
