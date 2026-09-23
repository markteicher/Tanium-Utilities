import argparse
import sys
import json
import socket
import logging
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from colorama import Fore, Style, init
from tqdm import tqdm


# ============================================================
# INITIALIZE COLORAMA
# ============================================================

init(autoreset=True)


# ============================================================
# ARGUMENTS
# ============================================================

parser = argparse.ArgumentParser(
    description="Tanium API Gateway connectivity test"
)

parser.add_argument(
    "--api-token",
    required=True,
    help="Tanium API token"
)

args = parser.parse_args()

API_KEY = args.api_token


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "https://amexgbt-api.cloud.tanium.com"

GRAPHQL_URL = f"{BASE_URL}/plugin/products/gateway/graphql"

TIMEOUT = 30

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_FILE = SCRIPT_DIR / "tanium_api_test.log"


# ============================================================
# ANSI ESCAPE CODE REMOVER
# ============================================================

ANSI_ESCAPE = re.compile(
    r"\x1B(?:[@-_][0-?]*[ -/]*[@-~]|\[[0-?]*[ -/]*[@-~])"
)


def strip_ansi(text):
    """
    Remove ANSI / Colorama escape sequences from text.
    """
    if text is None:
        return ""

    return ANSI_ESCAPE.sub("", str(text))


# ============================================================
# LOG FORMATTERS
# ============================================================

class CleanFileFormatter(logging.Formatter):
    """
    Formatter used for the .log file.

    Removes ANSI / Colorama escape sequences so the
    log file contains clean plain text.
    """

    def format(self, record):
        formatted = super().format(record)
        return strip_ansi(formatted)


class ColorConsoleFormatter(logging.Formatter):
    """
    Formatter used for the console.
    """

    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.WHITE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record):

        message = super().format(record)

        color = self.COLORS.get(
            record.levelno,
            Fore.WHITE
        )

        return (
            color
            + message
            + Style.RESET_ALL
        )


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "tanium_api_test"
)

logger.setLevel(
    logging.DEBUG
)

logger.propagate = False
logger.handlers.clear()


# ============================================================
# FILE LOGGING
# ============================================================

file_handler = logging.FileHandler(
    LOG_FILE,
    mode="a",
    encoding="utf-8"
)

file_handler.setLevel(
    logging.DEBUG
)

file_formatter = CleanFileFormatter(
    "[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

file_handler.setFormatter(
    file_formatter
)

logger.addHandler(
    file_handler
)


# ============================================================
# CONSOLE LOGGING
# ============================================================

console_handler = logging.StreamHandler(
    sys.stdout
)

console_handler.setLevel(
    logging.INFO
)

console_formatter = ColorConsoleFormatter(
    "[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

console_handler.setFormatter(
    console_formatter
)

logger.addHandler(
    console_handler
)


# ============================================================
# LOGGING HELPERS
# ============================================================

def separator(title=None):

    line = "=" * 90

    logger.info(line)

    if title:
        logger.info(title)
        logger.info(line)


def subsection(title):

    logger.info("")
    logger.info("-" * 90)
    logger.info(title)
    logger.info("-" * 90)


def success(message):

    logger.info(
        Fore.GREEN
        + Style.BRIGHT
        + message
        + Style.RESET_ALL
    )


def warning(message):

    logger.warning(
        Fore.YELLOW
        + message
        + Style.RESET_ALL
    )


def failure(message):

    logger.error(
        Fore.RED
        + Style.BRIGHT
        + message
        + Style.RESET_ALL
    )


# ============================================================
# CHECK API KEY
# ============================================================

if not API_KEY.strip():

    separator(
        "TANIUM API TEST"
    )

    failure(
        "--api-token cannot be empty."
    )

    logger.info("")
    logger.info(
        'Usage: python3 tanium_api_test.py --api-token "YOUR_API_TOKEN"'
    )

    sys.exit(1)


# ============================================================
# DNS LOOKUP
# ============================================================

def get_dns_addresses(
    hostname,
    port=443
):

    addresses = []

    try:

        results = socket.getaddrinfo(
            hostname,
            port,
            type=socket.SOCK_STREAM
        )

        for result in results:

            ip = result[4][0]

            if ip not in addresses:
                addresses.append(ip)

    except socket.gaierror as exc:

        logger.exception(
            f"DNS lookup failed for {hostname}: {exc}"
        )

    return addresses


# ============================================================
# DISPLAY TARGET SERVER
# ============================================================

def show_target_server(url):

    parsed = urlparse(url)

    hostname = parsed.hostname
    port = parsed.port or 443

    subsection(
        "TARGET SERVER"
    )

    logger.info(
        f"Requested URL:      {url}"
    )

    logger.info(
        f"Requested hostname: {hostname}"
    )

    logger.info(
        f"Requested port:     {port}"
    )

    addresses = get_dns_addresses(
        hostname,
        port
    )

    if addresses:

        logger.info(
            "DNS resolved IP address(es):"
        )

        for ip in addresses:

            logger.info(
                f"    {ip}"
            )

    else:

        warning(
            "No DNS IP addresses were returned."
        )


# ============================================================
# GET ACTUAL CONNECTED PEER
# ============================================================

def get_peer_server(response):

    socket_paths = [

        lambda:
        response.raw._connection.sock,

        lambda:
        response.raw.connection.sock,

        lambda:
        response.raw._fp.fp.raw._sock,
    ]

    for getter in socket_paths:

        try:

            sock = getter()

            if sock:

                peer = sock.getpeername()

                if peer:

                    return (
                        peer[0],
                        peer[1]
                    )

        except Exception:
            pass

    return (
        None,
        None
    )


# ============================================================
# DISPLAY HTTP RESPONSE
# ============================================================

def show_response(
    name,
    response
):

    parsed = urlparse(
        response.url
    )

    hostname = parsed.hostname
    port = parsed.port or 443

    peer_ip, peer_port = get_peer_server(
        response
    )

    separator(
        name
    )


    # ========================================================
    # REQUEST DESTINATION
    # ========================================================

    subsection(
        "REQUEST DESTINATION"
    )

    logger.info(
        f"URL:             {response.url}"
    )

    logger.info(
        f"Hostname:        {hostname}"
    )

    logger.info(
        f"Protocol:        {parsed.scheme}"
    )

    logger.info(
        f"Port:            {port}"
    )


    # ========================================================
    # DNS RESOLUTION
    # ========================================================

    subsection(
        "DNS RESOLUTION"
    )

    addresses = get_dns_addresses(
        hostname,
        port
    )

    if addresses:

        for ip in addresses:

            logger.info(
                f"Resolved IP:     {ip}"
            )

    else:

        warning(
            "DNS resolution returned no addresses."
        )


    # ========================================================
    # ACTUAL SERVER
    # ========================================================

    subsection(
        "SERVER ACTUALLY REACHED"
    )

    if peer_ip:

        success(
            f"Connected peer IP:   {peer_ip}"
        )

        logger.info(
            f"Connected peer port: {peer_port}"
        )

    else:

        warning(
            "Connected peer IP was not available "
            "from the requests socket."
        )


    # ========================================================
    # HTTP RESPONSE
    # ========================================================

    subsection(
        "HTTP RESPONSE"
    )

    logger.info(
        f"HTTP Status:      {response.status_code}"
    )

    logger.info(
        f"Reason:           {response.reason}"
    )

    logger.info(
        f"Content-Type:     "
        f"{response.headers.get('Content-Type')}"
    )

    logger.info(
        f"Content-Length:   "
        f"{response.headers.get('Content-Length')}"
    )

    logger.info(
        f"Server:           "
        f"{response.headers.get('Server')}"
    )

    logger.info(
        f"Via:              "
        f"{response.headers.get('Via')}"
    )

    logger.info(
        f"X-Cache:          "
        f"{response.headers.get('X-Cache')}"
    )

    logger.info(
        f"X-Served-By:      "
        f"{response.headers.get('X-Served-By')}"
    )

    logger.info(
        f"X-Request-ID:     "
        f"{response.headers.get('X-Request-ID')}"
    )

    logger.info(
        f"X-Correlation-ID: "
        f"{response.headers.get('X-Correlation-ID')}"
    )

    logger.info(
        f"CF-Ray:           "
        f"{response.headers.get('CF-Ray')}"
    )


    # ========================================================
    # ALL HEADERS
    # ========================================================

    subsection(
        "ALL RESPONSE HEADERS"
    )

    for key, value in response.headers.items():

        logger.info(
            f"{key}: {value}"
        )


    # ========================================================
    # RESPONSE BODY
    # ========================================================

    subsection(
        "RESPONSE BODY"
    )

    try:

        data = response.json()

        formatted_body = json.dumps(
            data,
            indent=2
        )

        for line in formatted_body.splitlines():

            logger.info(
                line
            )

    except ValueError:

        body = response.text[:10000]

        if body:

            for line in body.splitlines():

                logger.info(
                    line
                )

        else:

            logger.info(
                "<empty response body>"
            )


    # ========================================================
    # RESULT
    # ========================================================

    subsection(
        "RESULT"
    )

    status = response.status_code

    if 200 <= status < 300:

        success(
            f"SUCCESS - HTTP {status}"
        )

        try:

            data = response.json()

            if "errors" in data:

                warning(
                    "GraphQL returned one or more errors."
                )

            elif "data" in data:

                success(
                    "GraphQL API Gateway request succeeded."
                )

        except ValueError:
            pass


    elif status == 401:

        failure(
            "FAILED - HTTP 401 UNAUTHORIZED"
        )

        logger.error(
            "The API token may be invalid or expired."
        )


    elif status == 403:

        failure(
            "FAILED - HTTP 403 FORBIDDEN"
        )

        logger.error(
            "The request reached a server, gateway, proxy, "
            "CDN, load balancer, or WAF, but access was denied."
        )

        logger.error(
            f"Requested hostname: {hostname}"
        )

        if peer_ip:

            logger.error(
                f"Network peer reached: "
                f"{peer_ip}:{peer_port}"
            )

        server = response.headers.get(
            "Server"
        )

        if server:

            logger.error(
                f"Server header: {server}"
            )

        via = response.headers.get(
            "Via"
        )

        if via:

            logger.error(
                f"Via/proxy header: {via}"
            )


    elif status == 404:

        failure(
            "FAILED - HTTP 404 NOT FOUND"
        )

        logger.error(
            "The GraphQL API Gateway endpoint was not found."
        )


    else:

        failure(
            f"FAILED - HTTP {status}"
        )


    separator()

    return (
        peer_ip,
        peer_port
    )


# ============================================================
# REQUEST ERROR HANDLER
# ============================================================

def handle_request_exception(exc):

    if isinstance(
        exc,
        requests.exceptions.SSLError
    ):

        failure(
            "SSL ERROR"
        )

    elif isinstance(
        exc,
        requests.exceptions.ProxyError
    ):

        failure(
            "PROXY ERROR"
        )

    elif isinstance(
        exc,
        requests.exceptions.ConnectionError
    ):

        failure(
            "CONNECTION ERROR"
        )

    elif isinstance(
        exc,
        requests.exceptions.Timeout
    ):

        failure(
            "REQUEST TIMED OUT"
        )

    else:

        failure(
            "REQUEST ERROR"
        )

    logger.exception(
        exc
    )


# ============================================================
# START
# ============================================================

separator(
    "TANIUM API GATEWAY TEST"
)

logger.info(
    f"Log file: {LOG_FILE}"
)

logger.info(
    "API key loaded: YES"
)

logger.info(
    f"API key length: {len(API_KEY)}"
)

logger.info(
    f"API key: {API_KEY}"
)

logger.info(
    f"Base URL: {BASE_URL}"
)

logger.info(
    f"GraphQL URL: {GRAPHQL_URL}"
)


# ============================================================
# HTTP SESSION
# ============================================================

http = requests.Session()

http.headers.update(
    {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "session": API_KEY,
        "User-Agent": "Tanium-Python-API-Test/1.0",
    }
)


# ============================================================
# SHOW INITIAL TARGET
# ============================================================

show_target_server(
    GRAPHQL_URL
)


# ============================================================
# PROGRESS BAR
# ============================================================

progress = tqdm(
    total=1,
    desc="Tanium API test",
    unit="test",
    dynamic_ncols=True,
    colour="green"
)


# ============================================================
# GRAPHQL API GATEWAY TEST
# ============================================================

separator(
    "1. TESTING TANIUM GRAPHQL API GATEWAY"
)

graphql_payload = {
    "query": "{ now }"
}

try:

    response = http.post(
        GRAPHQL_URL,
        json=graphql_payload,
        timeout=TIMEOUT,
        stream=True
    )

    peer_ip, peer_port = show_response(
        "1. GRAPHQL API GATEWAY TEST",
        response
    )

    progress.update(1)

except requests.exceptions.RequestException as exc:

    progress.close()

    handle_request_exception(
        exc
    )

    logger.info(
        f"Log file: {LOG_FILE}"
    )

    http.close()
    logging.shutdown()

    sys.exit(1)


# ============================================================
# FINISH PROGRESS
# ============================================================

progress.close()


# ============================================================
# FINAL SUMMARY
# ============================================================

separator(
    "TEST COMPLETE"
)

logger.info(
    f"API key used:        {API_KEY}"
)

logger.info(
    f"GraphQL status:      "
    f"{response.status_code}"
)

logger.info(
    f"GraphQL reason:      "
    f"{response.reason}"
)

logger.info(
    f"Requested server:    "
    f"{urlparse(response.url).hostname}"
)

if peer_ip:

    logger.info(
        f"Server/peer reached: "
        f"{peer_ip}:{peer_port}"
    )

logger.info(
    f"HTTP Server header:  "
    f"{response.headers.get('Server')}"
)

logger.info(
    f"Via/proxy header:    "
    f"{response.headers.get('Via')}"
)

logger.info(
    f"Log file:            {LOG_FILE}"
)


if 200 <= response.status_code < 300:

    success(
        "TANIUM GRAPHQL API GATEWAY TEST COMPLETED SUCCESSFULLY"
    )

else:

    failure(
        "TANIUM GRAPHQL API GATEWAY TEST COMPLETED WITH ERRORS"
    )


separator()


# ============================================================
# CLEANUP
# ============================================================

response.close()

http.close()

logging.shutdown()
