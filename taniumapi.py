import os
import sys
import json
import requests


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "https://amexgbt-api.cloud.tanium.com"

VALIDATE_URL = f"{BASE_URL}/api/v2/session/validate"
GRAPHQL_URL = f"{BASE_URL}/plugin/products/gateway/graphql"

TOKEN = os.getenv("TANIUM_SESSION_TOKEN")


# ============================================================
# CHECK TOKEN
# ============================================================

if not TOKEN:
    print("ERROR: TANIUM_SESSION_TOKEN is not configured.")
    print()
    print("In PyCharm:")
    print("Run -> Edit Configurations -> Environment variables")
    print()
    print("Add:")
    print("TANIUM_SESSION_TOKEN=your_token")
    sys.exit(1)

print("Tanium API Test")
print("=" * 70)
print(f"Token loaded: YES")
print(f"Token length: {len(TOKEN)}")
print()


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update(
    {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "session": TOKEN,
    }
)


# ============================================================
# DISPLAY RESPONSE
# ============================================================

def show_response(name, response):

    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    print(f"URL:          {response.url}")
    print(f"HTTP Status:  {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Server:       {response.headers.get('Server')}")

    print()
    print("Response headers:")
    print("-" * 70)

    for key, value in response.headers.items():
        print(f"{key}: {value}")

    print()
    print("Response body:")
    print("-" * 70)

    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except ValueError:
        print(response.text[:5000])

    print()

    if response.status_code == 200:
        print("RESULT: SUCCESS")

    elif response.status_code == 401:
        print("RESULT: 401 UNAUTHORIZED")
        print("Possible token/authentication problem.")

    elif response.status_code == 403:
        print("RESULT: 403 FORBIDDEN")
        print("The server received the request but refused access.")

    else:
        print(f"RESULT: HTTP {response.status_code}")


# ============================================================
# 1. VALIDATE TANIIUM SESSION
# ============================================================

print("Testing session validation...")

try:

    response = session.post(
        VALIDATE_URL,
        json={
            "session": TOKEN
        },
        timeout=30,
    )

    show_response(
        "1. SESSION VALIDATION",
        response
    )

except requests.exceptions.SSLError as exc:

    print("SSL ERROR")
    print(exc)
    sys.exit(1)

except requests.exceptions.ProxyError as exc:

    print("PROXY ERROR")
    print(exc)
    sys.exit(1)

except requests.exceptions.ConnectionError as exc:

    print("CONNECTION ERROR")
    print(exc)
    sys.exit(1)

except requests.exceptions.Timeout:

    print("REQUEST TIMED OUT")
    sys.exit(1)

except requests.exceptions.RequestException as exc:

    print("REQUEST ERROR")
    print(exc)
    sys.exit(1)


# ============================================================
# STOP IF SESSION VALIDATION FAILED
# ============================================================

if response.status_code != 200:

    print()
    print("=" * 70)
    print("SESSION VALIDATION FAILED")
    print("=" * 70)

    print(
        "GraphQL test will not run because the session validation "
        "did not return HTTP 200."
    )

    sys.exit(1)


# ============================================================
# 2. TEST GRAPHQL
# ============================================================

print()
print("Session validated.")
print("Testing GraphQL endpoint...")

graphql_payload = {
    "query": "{now}"
}

try:

    response = session.post(
        GRAPHQL_URL,
        json=graphql_payload,
        timeout=30,
    )

    show_response(
        "2. GRAPHQL TEST",
        response
    )

except requests.exceptions.SSLError as exc:

    print("SSL ERROR")
    print(exc)

except requests.exceptions.ProxyError as exc:

    print("PROXY ERROR")
    print(exc)

except requests.exceptions.ConnectionError as exc:

    print("CONNECTION ERROR")
    print(exc)

except requests.exceptions.Timeout:

    print("REQUEST TIMED OUT")

except requests.exceptions.RequestException as exc:

    print("REQUEST ERROR")
    print(exc)
