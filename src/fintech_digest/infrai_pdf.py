import time
from typing import Any

import httpx


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: object, status_code: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiPdfClient:
    def __init__(self, api_key: str, base_url: str, max_attempts: int = 4) -> None:
        self._max_attempts = max_attempts
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0,
        )

    def generate(self, markdown: str, run_id: str) -> dict[str, Any]:
        for attempt in range(self._max_attempts):
            response = self._client.request(
                method="POST",
                url="/pdf/generate",
                headers={"Idempotency-Key": f"digest-{run_id}"},
                json={
                    "markdown": markdown,
                    "page_size": "A4",
                    "orientation": "portrait",
                    "store": True,
                },
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt + 1 < self._max_attempts:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            data = envelope.get("data")
            if not isinstance(data, dict):
                raise RuntimeError("Infrai response data must be an object")
            return data
        raise RuntimeError("Infrai request attempts were exhausted")
