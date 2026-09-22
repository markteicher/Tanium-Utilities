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

API_KEY = os.getenv("TANIUM_SESSION_TOKEN")


# ============================================================
# CHECK API KEY
# ============================================================

if not API_KEY:
    print("ERROR: TANIUM_SESSION_TOKEN is not configured.")
    print()
    print("In PyCharm:")
    print("Run -> Edit Configurations -> Environment variables")
    print()
    print("Add:")
    print("TANIUM_SESSION_TOKEN=your_api_key")
    sys.exit(1)


# ============================================================
# PRINT API KEY INFORMATION
# ============================================================

print()
print("=" * 70)
print("TANIUM API TEST")
print("=" * 70)
print(f"API key loaded: YES")
print(f"API key length: {len(API_KEY)}")
print(f"API key: {API_KEY}")
print("=" * 70)


# ============================================================
# CREATE HTTP SESSION
# ============================================================

http = requests.Session()

http.headers.update(
    {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "session": API_KEY,
    }
)


# ============================================================
# FUNCTION TO DISPLAY RESPONSE
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
    print("Response Headers")
    print("-" * 70)

    for key, value in response.headers.items():
        print(f"{key}: {value}")

    print()
    print("Response Body")
    print("-" * 70)

    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except ValueError:
        print(response.text[:5000])

    print()
    print("Result")
    print("-" * 70)

    if response.status_code == 200:
        print("SUCCESS - HTTP 200")

    elif response.status_code == 401:
        print("FAILED - HTTP 401 UNAUTHORIZED")
        print("The API key/session may be invalid or expired.")

    elif response.status_code == 403:
        print("FAILED - HTTP 403 FORBIDDEN")
        print("The request reached the server, but access was denied.")

    elif response.status_code == 404:
        print("FAILED - HTTP 404 NOT FOUND")
        print("The API endpoint was not found.")

    else:
        print(f"FAILED - HTTP {response.status_code}")

    print("=" * 70)


# ============================================================
# 1. VALIDATE TANIIUM SESSION / API KEY
# ============================================================

print()
print("Testing Tanium session validation...")

try:

    validate_payload = {
        "session": API_KEY
    }

    response = http.post(
        VALIDATE_URL,
        json=validate_payload,
        timeout=30,
    )

    show_response(
        "1. SESSION VALIDATION",
        response
    )

except requests.exceptions.SSLError as exc:

    print()
    print("SSL ERROR")
    print(exc)
    sys.exit(1)

except requests.exceptions.ProxyError as exc:

    print()
    print("PROXY ERROR")
    print(exc)
    sys.exit(1)

except requests.exceptions.ConnectionError as exc:

    print()
    print("CONNECTION ERROR")
    print(exc)
    sys.exit(1)

except requests.exceptions.Timeout as exc:

    print()
    print("REQUEST TIMED OUT")
    print(exc)
    sys.exit(1)

except requests.exceptions.RequestException as exc:

    print()
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

    print(f"API key: {API_KEY}")
    print(f"HTTP status: {response.status_code}")

    print()
    print(
        "GraphQL test will not run because session validation "
        "did not return HTTP 200."
    )

    sys.exit(1)


# ============================================================
# 2. GRAPHQL TEST
# ============================================================

print()
print("Session validation succeeded.")
print("Testing Tanium GraphQL endpoint...")


graphql_payload = {
    "query": "{ now }"
}


try:

    response = http.post(
        GRAPHQL_URL,
        json=graphql_payload,
        timeout=30,
    )

    show_response(
        "2. GRAPHQL TEST",
        response
    )

except requests.exceptions.SSLError as exc:

    print()
    print("SSL ERROR")
    print(exc)
    sys.exit(1)

except requests.exceptions.ProxyError as exc:

    print()
    print("PROXY ERROR")
    print(exc)
    sys.exit(1)

except requests.exceptions.ConnectionError as exc:

    print()
    print("CONNECTION ERROR")
    print(exc)
    sys.exit(1)

except requests.exceptions.Timeout as exc:

    print()
    print("REQUEST TIMED OUT")
    print(exc)
    sys.exit(1)

except requests.exceptions.RequestException as exc:

    print()
    print("REQUEST ERROR")
    print(exc)
    sys.exit(1)


# ============================================================
# FINISHED
# ============================================================

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print(f"API key used: {API_KEY}")
print(f"GraphQL HTTP status: {response.status_code}")
print("=" * 70)
