"""Performance Testing - Load testing with Locust"""

import json

from locust import HttpUser, between, task


class GuestbookUser(HttpUser):
    """Simulate a user interacting with the Guestbook API"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    token = None

    def on_start(self):
        """Login and get token when user starts"""
        response = self.client.post(
            "/api/login", json={"username": "admin", "password": "password123"}
        )
        if response.status_code == 200:
            self.token = response.json()["token"]

    @task(5)
    def read_all_entries(self):
        """Read all guestbook entries (most common operation)"""
        if self.token:
            self.client.get(
                "/api/guestbook", headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(3)
    def read_with_pagination(self):
        """Read entries with pagination"""
        if self.token:
            self.client.get(
                "/api/guestbook?page=1&limit=10",
                headers={"Authorization": f"Bearer {self.token}"},
            )

    @task(2)
    def search_entries(self):
        """Search for entries"""
        if self.token:
            self.client.get(
                "/api/guestbook?search=test",
                headers={"Authorization": f"Bearer {self.token}"},
            )

    @task(1)
    def create_entry(self):
        """Create a new entry (less common)"""
        if self.token:
            self.client.post(
                "/api/guestbook",
                json={
                    "name": "Load Test User",
                    "email": "loadtest@example.com",
                    "comment": "Performance testing entry",
                },
                headers={"Authorization": f"Bearer {self.token}"},
            )

    @task(1)
    def read_single_entry(self):
        """Read a single entry"""
        if self.token:
            # Try to read entry with ID 1
            self.client.get(
                "/api/guestbook/1", headers={"Authorization": f"Bearer {self.token}"}
            )
