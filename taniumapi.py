import os
import sys
import json
import socket
from urllib.parse import urlparse

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
    print()
    print("=" * 80)
    print("ERROR: TANIUM_SESSION_TOKEN is not configured.")
    print("=" * 80)
    print()
    print("In PyCharm:")
    print("Run -> Edit Configurations -> Environment variables")
    print()
    print("Add:")
    print("TANIUM_SESSION_TOKEN=your_api_key")
    print()

    sys.exit(1)


# ============================================================
# PRINT API KEY INFORMATION
# ============================================================

print()
print("=" * 80)
print("TANIUM API TEST")
print("=" * 80)

print("API key loaded: YES")
print(f"API key length: {len(API_KEY)}")
print(f"API key: {API_KEY}")

print("=" * 80)


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
# DNS INFORMATION
# ============================================================

def show_dns_info(url):

    parsed = urlparse(url)
    hostname = parsed.hostname

    print()
    print("TARGET SERVER")
    print("-" * 80)

    print(f"Requested URL:      {url}")
    print(f"Requested hostname: {hostname}")

    try:

        addresses = socket.getaddrinfo(
            hostname,
            443,
            type=socket.SOCK_STREAM
        )

        ip_addresses = []

        for entry in addresses:

            ip = entry[4][0]

            if ip not in ip_addresses:
                ip_addresses.append(ip)

        print("DNS resolved IP(s):")

        for ip in ip_addresses:
            print(f"  {ip}")

    except socket.gaierror as exc:

        print(f"DNS lookup failed: {exc}")


# ============================================================
# ACTUAL NETWORK PEER
# ============================================================

def get_peer_server(response):

    peer_ip = None
    peer_port = None

    try:

        connection = response.raw._connection

        if connection and connection.sock:

            peer_ip, peer_port = connection.sock.getpeername()

    except Exception:
        pass

    if not peer_ip:

        try:

            connection = response.raw.connection

            if connection and connection.sock:

                peer_ip, peer_port = connection.sock.getpeername()

        except Exception:
            pass

    return peer_ip, peer_port


# ============================================================
# DISPLAY RESPONSE
# ============================================================

def show_response(name, response):

    print()
    print("=" * 80)
    print(name)
    print("=" * 80)

    parsed = urlparse(response.url)

    print()
    print("REQUEST DESTINATION")
    print("-" * 80)

    print(f"URL:             {response.url}")
    print(f"Hostname:        {parsed.hostname}")
    print(f"Protocol:        {parsed.scheme}")
    print(f"Port:            {parsed.port or 443}")

    # --------------------------------------------------------
    # DNS
    # --------------------------------------------------------

    try:

        addresses = socket.getaddrinfo(
            parsed.hostname,
            parsed.port or 443,
            type=socket.SOCK_STREAM
        )

        resolved_ips = []

        for address in addresses:

            ip = address[4][0]

            if ip not in resolved_ips:
                resolved_ips.append(ip)

        print()
        print("DNS resolved IP addresses:")

        for ip in resolved_ips:
            print(f"  {ip}")

    except Exception as exc:

        print(f"DNS lookup failed: {exc}")


    # --------------------------------------------------------
    # ACTUAL CONNECTION
    # --------------------------------------------------------

    peer_ip, peer_port = get_peer_server(response)

    print()
    print("SERVER ACTUALLY REACHED")
    print("-" * 80)

    if peer_ip:

        print(f"Connected peer IP:   {peer_ip}")
        print(f"Connected peer port: {peer_port}")

    else:

        print("Connected peer IP:   Not available from requests connection object")


    # --------------------------------------------------------
    # HTTP RESPONSE
    # --------------------------------------------------------

    print()
    print("HTTP RESPONSE")
    print("-" * 80)

    print(f"HTTP Status:       {response.status_code}")
    print(f"Content-Type:      {response.headers.get('Content-Type')}")
    print(f"Server header:     {response.headers.get('Server')}")
    print(f"Via:               {response.headers.get('Via')}")
    print(f"X-Cache:           {response.headers.get('X-Cache')}")
    print(f"X-Served-By:       {response.headers.get('X-Served-By')}")
    print(f"X-Request-ID:      {response.headers.get('X-Request-ID')}")
    print(f"X-Correlation-ID:  {response.headers.get('X-Correlation-ID')}")
    print(f"CF-Ray:            {response.headers.get('CF-Ray')}")


    # --------------------------------------------------------
    # ALL RESPONSE HEADERS
    # --------------------------------------------------------

    print()
    print("ALL RESPONSE HEADERS")
    print("-" * 80)

    for key, value in response.headers.items():
        print(f"{key}: {value}")


    # --------------------------------------------------------
    # RESPONSE BODY
    # --------------------------------------------------------

    print()
    print("RESPONSE BODY")
    print("-" * 80)

    try:

        data = response.json()

        print(
            json.dumps(
                data,
                indent=2
            )
        )

    except ValueError:

        print(response.text[:5000])


    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    print()
    print("RESULT")
    print("-" * 80)

    if response.status_code == 200:

        print("SUCCESS - HTTP 200")


    elif response.status_code == 401:

        print("FAILED - HTTP 401 UNAUTHORIZED")
        print("The API key/session may be invalid or expired.")


    elif response.status_code == 403:

        print("FAILED - HTTP 403 FORBIDDEN")

        print()
        print("The request reached a server, proxy, gateway, or WAF")
        print("but access to the requested resource was denied.")

        print()
        print(f"Requested host: {parsed.hostname}")

        if peer_ip:
            print(f"Network peer reached: {peer_ip}:{peer_port}")

        if response.headers.get("Server"):
            print(
                f"Server software/header: "
                f"{response.headers.get('Server')}"
            )

        if response.headers.get("Via"):
            print(
                f"Via/proxy: "
                f"{response.headers.get('Via')}"
            )


    elif response.status_code == 404:

        print("FAILED - HTTP 404 NOT FOUND")
        print("The requested API endpoint was not found.")


    else:

        print(
            f"FAILED - HTTP {response.status_code}"
        )

    print("=" * 80)


# ============================================================
# SHOW TARGET SERVER BEFORE REQUEST
# ============================================================

show_dns_info(VALIDATE_URL)


# ============================================================
# 1. VALIDATE TANIUM SESSION
# ============================================================

print()
print("=" * 80)
print("TESTING TANIIUM SESSION VALIDATION")
print("=" * 80)


try:

    validate_payload = {
        "session": API_KEY
    }

    response = http.post(
        VALIDATE_URL,
        json=validate_payload,
        timeout=30,
        stream=True
    )

    show_response(
        "1. SESSION VALIDATION",
        response
    )


except requests.exceptions.SSLError as exc:

    print()
    print("SSL ERROR")
    print("-" * 80)
    print(exc)

    sys.exit(1)


except requests.exceptions.ProxyError as exc:

    print()
    print("PROXY ERROR")
    print("-" * 80)
    print(exc)

    sys.exit(1)


except requests.exceptions.ConnectionError as exc:

    print()
    print("CONNECTION ERROR")
    print("-" * 80)
    print(exc)

    sys.exit(1)


except requests.exceptions.Timeout as exc:

    print()
    print("REQUEST TIMED OUT")
    print("-" * 80)
    print(exc)

    sys.exit(1)


except requests.exceptions.RequestException as exc:

    print()
    print("REQUEST ERROR")
    print("-" * 80)
    print(exc)

    sys.exit(1)


# ============================================================
# STOP IF SESSION VALIDATION FAILED
# ============================================================

if response.status_code != 200:

    print()
    print("=" * 80)
    print("SESSION VALIDATION FAILED")
    print("=" * 80)

    print(f"API key:       {API_KEY}")
    print(f"HTTP status:   {response.status_code}")
    print(f"Server header: {response.headers.get('Server')}")
    print(f"Via:           {response.headers.get('Via')}")

    peer_ip, peer_port = get_peer_server(response)

    if peer_ip:

        print(f"Peer reached:  {peer_ip}:{peer_port}")

    print()
    print(
        "GraphQL test will not run because session validation "
        "did not return HTTP 200."
    )

    print("=" * 80)

    response.close()

    sys.exit(1)


response.close()


# ============================================================
# 2. GRAPHQL TEST
# ============================================================

print()
print("=" * 80)
print("SESSION VALIDATION SUCCEEDED")
print("=" * 80)

print()
print("Testing Tanium GraphQL endpoint...")


graphql_payload = {
    "query": "{ now }"
}


try:

    response = http.post(
        GRAPHQL_URL,
        json=graphql_payload,
        timeout=30,
        stream=True
    )

    show_response(
        "2. GRAPHQL TEST",
        response
    )


except requests.exceptions.SSLError as exc:

    print()
    print("SSL ERROR")
    print("-" * 80)
    print(exc)

    sys.exit(1)


except requests.exceptions.ProxyError as exc:

    print()
    print("PROXY ERROR")
    print("-" * 80)
    print(exc)

    sys.exit(1)


except requests.exceptions.ConnectionError as exc:

    print()
    print("CONNECTION ERROR")
    print("-" * 80)
    print(exc)

    sys.exit(1)


except requests.exceptions.Timeout as exc:

    print()
    print("REQUEST TIMED OUT")
    print("-" * 80)
    print(exc)

    sys.exit(1)


except requests.exceptions.RequestException as exc:

    print()
    print("REQUEST ERROR")
    print("-" * 80)
    print(exc)

    sys.exit(1)


# ============================================================
# FINAL SUMMARY
# ============================================================

peer_ip, peer_port = get_peer_server(response)

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)

print(f"API key used:       {API_KEY}")
print(f"GraphQL status:     {response.status_code}")
print(f"Requested server:   {urlparse(response.url).hostname}")

if peer_ip:
    print(f"Server/peer reached: {peer_ip}:{peer_port}")

print(
    f"HTTP Server header: "
    f"{response.headers.get('Server')}"
)

print(
    f"Via/proxy header:   "
    f"{response.headers.get('Via')}"
)

print("=" * 80)

response.close()
