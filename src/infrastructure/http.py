import requests


class HttpClient:
    def __init__(self, timeout: int = 30, user_agent: str = None):
        self._session = requests.Session()
        self._timeout = timeout
        if user_agent:
            self._session.headers["User-Agent"] = user_agent

    def get(self, url: str) -> str:
        response = self._session.get(url, timeout=self._timeout)
        response.raise_for_status()
        return response.text

    def close(self) -> None:
        self._session.close()
