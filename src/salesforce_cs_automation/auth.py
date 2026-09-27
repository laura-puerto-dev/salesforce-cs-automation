import base64
import hashlib
import os
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ["SALESFORCE_CLIENT_ID"]
LOGIN_URL = os.getenv(
    "SALESFORCE_LOGIN_URL",
    "https://login.salesforce.com",
).rstrip("/")
REDIRECT_URI = os.getenv(
    "SALESFORCE_REDIRECT_URI",
    "http://localhost:8765/callback",
)

CALLBACK = urlparse(REDIRECT_URI)

if CALLBACK.hostname is None:
    raise ValueError("SALESFORCE_REDIRECT_URI must contain a valid hostname")

if CALLBACK.port is None:
    raise ValueError("SALESFORCE_REDIRECT_URI must contain an explicit port")

if CALLBACK.scheme != "http":
    raise ValueError("The local OAuth callback must use HTTP")

if CALLBACK.path != "/callback":
    raise ValueError("The OAuth callback path must be /callback")

CALLBACK_HOST: str = CALLBACK.hostname
CALLBACK_PORT: int = CALLBACK.port


def generate_pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()

    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    return verifier, challenge


def authenticate() -> dict:
    verifier, challenge = generate_pkce()
    state = secrets.token_urlsafe(32)
    result = {}

    class OAuthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)

            if parsed.path != CALLBACK.path:
                self.send_error(404)
                return

            params = parse_qs(parsed.query)

            if params.get("state", [None])[0] != state:
                result["error"] = "OAuth state mismatch"
            elif "error" in params:
                result["error"] = params["error"][0]
                result["description"] = params.get("error_description", [""])[0]
            else:
                result["code"] = params.get("code", [None])[0]

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            self.wfile.write(
                b"<h2>Authorization received.</h2>"
                b"<p>You can return to your terminal.</p>"
            )

        def log_message(self, *args):
            pass

    server = HTTPServer(
        (CALLBACK_HOST, CALLBACK_PORT),
        OAuthHandler,
    )
    server.timeout = 120

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "api",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }

    authorization_url = f"{LOGIN_URL}/services/oauth2/authorize?{urlencode(params)}"

    print("Opening Salesforce authorization...")
    webbrowser.open(authorization_url)

    try:
        server.handle_request()
    finally:
        server.server_close()

    if "error" in result:
        raise RuntimeError(
            f"Authorization failed: {result['error']} {result.get('description', '')}"
        )

    if not result.get("code"):
        raise TimeoutError("No authorization code received within 120 seconds.")

    response = requests.post(
        f"{LOGIN_URL}/services/oauth2/token",
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code": result["code"],
            "code_verifier": verifier,
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Token exchange failed ({response.status_code}): {response.text}"
        )

    return response.json()


def authenticate_service() -> dict[str, str]:
    """Authenticate with Salesforce using Client Credentials."""
    load_dotenv()

    client_id = os.environ["SALESFORCE_CLIENT_ID"]
    client_secret = os.environ["SALESFORCE_CLIENT_SECRET"]
    instance_url = os.environ["SALESFORCE_INSTANCE_URL"].rstrip("/")

    response = requests.post(
        f"{instance_url}/services/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    response.raise_for_status()

    credentials = response.json()
    access_token = credentials.get("access_token")

    if not isinstance(access_token, str) or not access_token:
        raise RuntimeError("Salesforce did not return an access token.")

    return {
        "access_token": access_token,
        "instance_url": credentials.get("instance_url", instance_url),
    }
