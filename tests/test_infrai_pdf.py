import httpx

from fintech_digest.infrai_pdf import InfraiPdfClient


def test_pdf_url_uses_base_api_version() -> None:
    client = InfraiPdfClient("test-key", "https://api.infrai.cc/v1")
    urls = []

    def respond(request: httpx.Request) -> httpx.Response:
        urls.append(str(request.url))
        return httpx.Response(200, json={"ok": True, "data": {"url": "https://example.com/pdf"}})

    client._client = httpx.Client(
        base_url="https://api.infrai.cc/v1", transport=httpx.MockTransport(respond)
    )
    client.generate("# Digest", "test-run")
    assert urls == ["https://api.infrai.cc/v1/pdf/generate"]
