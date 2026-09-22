import os
import sys
import requests

BASE_URL = "https://amexgbt-api.cloud.tanium.com"

SESSION_TOKEN = os.getenv("TANIUM_SESSION_TOKEN")

if not SESSION_TOKEN:
    sys.exit("ERROR: TANIUM_SESSION_TOKEN environment variable is not set.")

headers = {
    "Content-Type": "application/json",
    "session": SESSION_TOKEN,
}


def print_response(name, response):
    print(f"\n{'=' * 60}")
    print(name)
    print(f"HTTP {response.status_code}")

    for key, value in response.headers.items():
        print(f"{key}: {value}")

    print("\nResponse:")
    try:
        print(response.json())
    except ValueError:
        print(response.text)


# ------------------------------------------------------------
# 1. Validate API token
# ------------------------------------------------------------

validate_url = f"{BASE_URL}/api/v2/session/validate"

try:
    response = requests.post(
        validate_url,
        headers=headers,
        json={
            "session": SESSION_TOKEN
        },
        timeout=30
    )

    print_response("1. Validate API Token", response)

except requests.RequestException as e:
    print(f"Validation request failed: {e}")
    sys.exit(1)


# ------------------------------------------------------------
# 2. Test GraphQL endpoint
# ------------------------------------------------------------

graphql_url = f"{BASE_URL}/plugin/products/gateway/graphql"

try:
    response = requests.post(
        graphql_url,
        headers=headers,
        json={
            "query": "{now}"
        },
        timeout=30
    )

    print_response("2. GraphQL Test", response)

except requests.RequestException as e:
    print(f"GraphQL request failed: {e}")
    sys.exit(1)
