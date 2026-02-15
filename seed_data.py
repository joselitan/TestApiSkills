import requests
import random

BASE_URL = "http://localhost:8080"

def seed_database():
    # 1. Login to get token
    print("🔑 Logging in...")
    try:
        auth_resp = requests.post(f"{BASE_URL}/api/login", json={
            "username": "admin",
            "password": "password123"
        })
        
        if auth_resp.status_code != 200:
            print(f"❌ Login failed: {auth_resp.text}")
            return

        token = auth_resp.json()['token']
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful!")

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is 'python app.py' running?")
        return

    # 2. Create Dummy Entries
    print("\n🌱 Seeding database with guestbook entries...")
    
    dummy_data = [
        ("Alice Smith", "alice@example.com", "Just checking out the site!"),
        ("Bob Jones", "bob@test.co", "Great API documentation."),
        ("Charlie Day", "charlie@mail.com", "I found a bug in the matrix."),
        ("Dana White", "dana@ufc.com", "Testing the pagination feature."),
        ("Eve Polastri", "eve@mi6.gov.uk", "Has anyone seen Villanelle?")
    ]

    for name, email, comment in dummy_data:
        payload = {
            "name": name,
            "email": email,
            "comment": comment
        }
        resp = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)
        
        if resp.status_code == 201:
            print(f"   Created entry for: {name}")
        else:
            print(f"   Failed to create {name}: {resp.status_code}")

    print("\n✨ Done! Refresh your browser to see the entries.")

if __name__ == "__main__":
    seed_database()
