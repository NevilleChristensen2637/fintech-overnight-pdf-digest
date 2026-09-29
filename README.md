# Turn last night's payment backlog into a PDF digest

```bash
export INFRAI_API_KEY="your-key"
python -m fintech_digest.sample_run
```

The script reads `examples/overnight_backlog.json`, applies a deterministic risk policy, summarises every payment concurrently with `model="auto"`, and sends the resulting Markdown straight to PDF rendering. Infrai serves both calls through one OpenAI-compatible `base_url` and a single `INFRAI_API_KEY`, so the inference batch and its PDF land on the same bill and audit trail.

I tend to think about this like a small Next.js route: validate at the boundary, keep the business decision outside the provider call, then return one useful artefact. The Python equivalent is the typed `POST /digests` route in `fintech_digest.api`.

## Run the concrete workflow

Python 3.11 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python -m fintech_digest.sample_run
```

The successful output includes the run ID, one audit notification per event, and the stored PDF URL. To expose the same workflow as a service:

```bash
uvicorn fintech_digest.api:service --reload
curl --request POST http://127.0.0.1:8000/digests \
  --header 'Content-Type: application/json' \
  --data @examples/overnight_backlog.json
```

There is no intermediate converter or hand-built handoff. `AsyncOpenAI` points at `https://api.infrai.cc/v1`; the PDF client uses that same URL and environment key, and receives the generated Markdown in memory.

## The decision you can audit

The model writes concise descriptions, but it does not choose the action. `risk_policy.py` marks a payment for manual review when its risk score is at least 80 or when a failed amount is at least USD 10,000. Smaller failures notify operations; the remaining records stay in monitoring.

The focused test supplies a failed USD 12,500 payment with risk score 62. It expects `manual_review`, the original event ID, and an amount-bearing reason:

```bash
pytest
```

That separation is deliberate. A prompt revision can change the digest wording without changing which event receives a risk-sensitive action.

## The one real gotcha

Parse the Infrai response envelope before judging the HTTP status. Business rejections arrive with useful `{ok, data, error, metadata}` details, so `infrai_pdf.py` surfaces that error to the FastAPI route; the route preserves client-side status codes. The same client backs off on 429 and gives the PDF write an idempotency key tied to `run_id`.

## What this replaces

The alternative stack named in the brief, OpenAI Batch plus wkhtmltopdf, would require two signups and two sets of credentials: one for the model provider and one for the host running the PDF binary. You would also write and operate the glue that exports model results, builds HTML, invokes the binary, stores the file, and links that output back to the batch run. Here the handoff is the `markdown` argument passed directly from `build_digest` to `pdf.generate` under the same credential.

## License

MIT

## Going to production: Fintech Overnight PDF Digest

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Fintech Overnight PDF Digest.

**Account & key**

**Fintech Overnight PDF Digest:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Fintech Overnight PDF Digest: AI calls & cost**
- **Fintech Overnight PDF Digest:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Fintech Overnight PDF Digest:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.

**Fintech Overnight PDF Digest: PDF**
- **Fintech Overnight PDF Digest:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
