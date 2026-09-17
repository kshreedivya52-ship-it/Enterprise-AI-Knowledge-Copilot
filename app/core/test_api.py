# test_api.py — Auto-fetches a fresh Auth0 token and calls your API
import httpx
import sys

# Auth0 credentials
AUTH0_DOMAIN = "enterprise-copilot.jp.auth0.com"
CLIENT_ID = "S5Yi1n7vaAO7dBjmqLSp89WsWYDGgJL8"
CLIENT_SECRET = "JhYUR232waEae4Zo_7S6Oae3epa6FwYy0wR02vnik_u65EwMYT2JKofng433Mx74"
AUDIENCE = "https://enterprise-copilot.jp.auth0.com/api/v2/"

def get_token():
    response = httpx.post(
        f"https://{AUTH0_DOMAIN}/oauth/token",
        json={
            "client_id": "8EVpojE4TOgDU5Bobcau2CfZ3WC6M3zn",
            "client_secret": "VOcHYcgtvEEELuVWqNDwqD8d7jrfWHak-i-VltyxEEXEyF_z82SU7hMqclDwYoQG",
            "audience": AUDIENCE,
            "grant_type": "client_credentials"
        }
    )
    data = response.json()
    if "access_token" not in data:
        print("Auth0 error:", data)
        sys.exit(1)
    return data["access_token"]

def search(query):
    token = get_token()
    response = httpx.get(
        f"http://localhost:8000/search?q={query}",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(response.json())

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "test"
    search(query)
