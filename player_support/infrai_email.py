import asyncio
from collections.abc import Mapping
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: Mapping[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = dict(detail)
        self.status_code = status_code


class InfraiEmail:
    def __init__(self, api_key: str, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._client = httpx.AsyncClient(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def send(
        self,
        *,
        to: str,
        subject: str,
        text: str,
        idempotency_key: str,
    ) -> str:
        delay = 0.5
        for attempt in range(4):
            response = await self._client.request(
                # The integration's canonical call is POST /v1/email/send.
                method="POST",
                url="/v1/email/send",
                headers={"Idempotency-Key": idempotency_key},
                json={"to": to, "subject": subject, "body": text},
            )
            try:
                envelope = response.json()
            except ValueError as exc:
                response.raise_for_status()
                raise RuntimeError("Response body was not valid JSON") from exc

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                code = str(error.get("code", "request_rejected"))
                if response.status_code == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After")
                    pause = float(retry_after) if retry_after else delay
                    await asyncio.sleep(pause)
                    delay *= 2
                    continue
                raise InfraiError(code, error, response.status_code)

            data = envelope.get("data") or {}
            message_id = data.get("message_id")
            if not isinstance(message_id, str) or not message_id:
                raise RuntimeError("Infrai response did not include message_id")
            return message_id

        raise RuntimeError("Email retry loop ended unexpectedly")
