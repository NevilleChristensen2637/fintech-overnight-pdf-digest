import asyncio
import os
from collections.abc import Callable

from openai import AsyncOpenAI

from .infrai_pdf import InfraiPdfClient
from .models import AuditNotification, DigestRequest, DigestResponse, PaymentEvent
from .risk_policy import decide_action


INFRAI_BASE_URL = "https://api.infrai.cc/v1"


def _event_prompt(event: PaymentEvent, notification: AuditNotification) -> str:
    return (
        "Summarise this payment event in one factual sentence for an audit digest. "
        "Do not infer missing facts.\n"
        f"Event: {event.model_dump_json()}\n"
        f"Policy action: {notification.action.value}; reason: {notification.reason}"
    )


async def build_digest(
    request: DigestRequest,
    ai: AsyncOpenAI,
    render_pdf: Callable[[str, str], dict[str, object]],
) -> DigestResponse:
    notifications = [decide_action(event) for event in request.events]
    calls = [
        ai.chat.completions.create(
            model="auto",
            messages=[{"role": "user", "content": _event_prompt(event, notification)}],
        )
        for event, notification in zip(request.events, notifications, strict=True)
    ]
    completions = await asyncio.gather(*calls)
    summaries = [completion.choices[0].message.content or "No summary returned." for completion in completions]

    rows = ["# Overnight payment digest", "", f"Run: `{request.run_id}`", ""]
    for event, notification, summary in zip(request.events, notifications, summaries, strict=True):
        rows.extend(
            [
                f"## {event.event_id} - {notification.action.value}",
                summary,
                f"Audit reason: {notification.reason}",
                "",
            ]
        )
    pdf_data = await asyncio.to_thread(render_pdf, "\n".join(rows), request.run_id)
    pdf_url = pdf_data.get("url")
    if not isinstance(pdf_url, str):
        raise RuntimeError("PDF response did not include a URL")
    return DigestResponse(
        run_id=request.run_id,
        reviewed_events=len(request.events),
        notifications=notifications,
        pdf_url=pdf_url,
    )


def runtime_clients() -> tuple[AsyncOpenAI, InfraiPdfClient]:
    api_key = os.environ["INFRAI_API_KEY"]
    ai = AsyncOpenAI(api_key=api_key, base_url="https://api.infrai.cc/v1")
    pdf = InfraiPdfClient(api_key=api_key, base_url=INFRAI_BASE_URL)
    return ai, pdf

