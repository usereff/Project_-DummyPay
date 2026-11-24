import requests

from utilities.config import DUMMYPAY_ANON_KEY


API_BASE_URL = "https://vtimmqlnyoyxiwczfdwf.supabase.co"
REQUEST_TIMEOUT = 15


class ApiError(Exception):
    """Raised when the DummyPay API returns a non-success response."""

    def __init__(self, status_code: int, body):
        self.status_code = status_code
        self.body = body
        message = ""
        if isinstance(body, dict):
            message = (
                body.get("message")
                or body.get("error")
                or body.get("error_code")
                or body.get("msg")
                or ""
            )
        self.code = message.split(":", 1)[0].strip()
        super().__init__(f"{status_code} {self.code}: {body}")


class BackendBase:
    """Small authenticated client for the documented DummyPay REST API."""

    def __init__(self):
        if not DUMMYPAY_ANON_KEY:
            raise ValueError(
                "Set DUMMYPAY_ANON_KEY to the Supabase publishable key."
            )

        self.base_url = API_BASE_URL
        self.http = requests.Session()
        self.http.headers["apikey"] = DUMMYPAY_ANON_KEY

    def close(self):
        self.http.close()

    def sign_in(self, email: str, password: str) -> dict:
        response = self.http.post(
            f"{self.base_url}/auth/v1/token",
            params={"grant_type": "password"},
            json={"email": email, "password": password},
            timeout=REQUEST_TIMEOUT,
        )
        session = self._check(response)
        self.http.headers["Authorization"] = (
            f"Bearer {session['access_token']}"
        )
        return session

    def rpc(self, function: str, **params):
        response = self.http.post(
            f"{self.base_url}/rest/v1/rpc/{function}",
            json=params,
            timeout=REQUEST_TIMEOUT,
        )
        return self._check(response)

    def select(self, table: str, **query):
        response = self.http.get(
            f"{self.base_url}/rest/v1/{table}",
            params=query,
            timeout=REQUEST_TIMEOUT,
        )
        return self._check(response)

    @staticmethod
    def _check(response):
        body = response.json() if response.content else None
        if not response.ok:
            raise ApiError(response.status_code, body)
        return body
