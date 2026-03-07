import requests
import json
import pytest

def test_api_email_exists():
    response = requests.get("https://jsonplaceholder.typicode.com/comments?postId=1")
    print(response.status_code)
    print(json.dumps(response.json(), indent=4))
    data = response.json()
    email = [item.get("email") for item in data]
    print(email)
    assert response.status_code == 200, f"Förväntade statuskod 200"
    assert "Hayden@althea.biz" in email, f"Förväntade email saknas. Hittade: {email}"

#@pytest.mark.skip(reason="Testet är under utveckling")
def test_api_update_post():
    
    payload = {
        "title": "My test post",
        "body": "This is a test",
        "userId": 1
    }

    response = requests.post("https://jsonplaceholder.typicode.com/posts", json=payload)

    print(response.status_code)
    print(response.json())
