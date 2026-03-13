import os
import random
import sys

import requests

# Add src to path for database imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

BASE_URL = "http://localhost:8080"


def seed_database():
    # 1. Login to get token
    print("🔑 Logging in...")
    try:
        auth_resp = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": "admin", "password": "password123"},
        )

        if auth_resp.status_code != 200:
            print(f"❌ Login failed: {auth_resp.text}")
            return

        token = auth_resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful!")

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is 'python src/app.py' running?")
        return

    # 2. Create Dummy Entries
    print("\n🌱 Seeding database with guestbook entries...")

    dummy_data = [
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
        ("Uma Thurman", "uma@killbill.com", "Revenge is never a straight line."),
        ("Victor Stone", "victor@titans.org", "Booyah!"),
        ("Wade Wilson", "wade@deadpool.com", "Maximum effort!"),
        ("Xavier Charles", "xavier@xmen.edu", "To me, my X-Men!"),
        ("Yara Greyjoy", "yara@ironislands.com", "What is dead may never die."),
        (
            "Zoe Washburne",
            "zoe@serenity.space",
            "This is something the Captain has to do for himself.",
        ),
    ]

    created_count = 0
    for name, email, comment in dummy_data:
        payload = {"name": name, "email": email, "comment": comment}
        resp = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)

        if resp.status_code == 201:
            created_count += 1
            print(f"   ✅ Created entry for: {name}")
        else:
            print(f"   ❌ Failed to create {name}: {resp.status_code}")

    print(f"\n✨ Done! Created {created_count} entries.")
    print("📊 Refresh your browser to see the entries and test pagination!")


if __name__ == "__main__":
    seed_database()
