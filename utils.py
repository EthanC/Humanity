import json
from datetime import datetime
from time import sleep
from typing import Any, Dict, List, Optional

import httpx
from httpx import HTTPError, Response, TimeoutException
from loguru import logger
from markdownify import markdownify


class Utility:
    """Utilitarian functions designed for Broadcast."""

    def GET(self: Any, url: str, isRetry: bool = False) -> Optional[Dict[str, Any]]:
        """Perform an HTTP GET request and return its response."""

        logger.debug(f"GET {url}")

        try:
            res: Response = httpx.get(url)
            status: int = res.status_code
            data: str = res.text

            res.raise_for_status()
        except HTTPError as e:
            if isRetry is False:
                logger.debug(f"(HTTP {status}) GET {url} failed, {e}... Retry in 10s")

                sleep(10)

                return Utility.GET(self, url, True)

            logger.error(f"(HTTP {status}) GET {url} failed, {e}")

            return
        except TimeoutException as e:
            if isRetry is False:
                logger.debug(f"GET {url} failed, {e}... Retry in 10s")

                sleep(10)

                return Utility.GET(self, url, True)

            # TimeoutException is common, no need to log as error
            logger.debug(f"GET {url} failed, {e}")

            return
        except Exception as e:
            if isRetry is False:
                logger.debug(f"GET {url} failed, {e}... Retry in 10s")

                sleep(10)

                return Utility.GET(self, url, True)

            logger.error(f"GET {url} failed, {e}")

            return

        logger.trace(data)

        return json.loads(data)

    def POST(self: Any, url: str, payload: Dict[str, Any]) -> bool:
        """Perform an HTTP POST request and return its status."""

        try:
            res: Response = httpx.post(
                url,
                data=json.dumps(payload),
                headers={"content-type": "application/json"},
            )
            status: int = res.status_code
            data: str = res.text

            res.raise_for_status()
        except HTTPError as e:
            logger.error(f"(HTTP {status}) POST {url} failed, {e}")

            return False
        except TimeoutException as e:
            # TimeoutException is common, no need to log as error
            logger.debug(f"POST {url} failed, {e}")

            return False
        except Exception as e:
            logger.error(f"POST {url} failed, {e}")

            return False

        logger.trace(data)

        return True

    def ConvertHTML(
        self: Any, input: str, trim: int = 0, exclude: List[str] = []
    ) -> str:
        """Convert the provided HTML string to markdown format."""

        for entry in exclude:
            input = input.replace(entry, "")

        result: str = markdownify(input, heading_style="ATX", bullets="-")

        if trim > 0:
            result = result[0:trim]

        return result

    def ConvertTimestamp(self: Any, input: str) -> str:
        """Convert the provided ISO timestamp to a Discord markdown timestamp."""

        timestamp: int = int(datetime.fromisoformat(input).timestamp())

        return "<t:" + str(timestamp) + ":R>"
