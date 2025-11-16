import requests
from requests.exceptions import RequestException, Timeout, HTTPError

from src.infrastructure.logger import setup_logger


logger = setup_logger(__name__)


class HttpClient:
    def __init__(self, timeout: int = 30, user_agent: str = None):
        self._session = requests.Session()
        self._timeout = timeout
        if user_agent:
            self._session.headers["User-Agent"] = user_agent

    def get(self, url: str) -> str:
        try:
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()
            return response.text
        except Timeout:
            logger.warning(f"Timeout fetching {url}")
            raise
        except HTTPError as e:
            logger.warning(f"HTTP error {e.response.status_code} for {url}")
            raise
        except RequestException as e:
            logger.warning(f"Request failed for {url}: {e}")
            raise

    def close(self) -> None:
        self._session.close()
