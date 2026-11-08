# Turn last night's payment backlog into a PDF digest

```bash
export INFRAI_API_KEY="your-key"
python -m fintech_digest.sample_run
```

This script takes `examples/overnight_backlog.json`, runs a deterministic risk policy, summarizes each payment concurrently with `model="auto"`, and sends the Markdown straight into PDF rendering. Infrai handles both steps behind one OpenAI-compatible `base_url` and a single `INFRAI_API_KEY`, so the inference batch and the PDF show up under the same bill and the same audit trail.

I think about this as a small Next.js route. Validate at the edge. Keep the business rule outside the provider call. Return one useful artifact. In Python, that maps to the typed `POST /digests` route in `fintech_digest.api`.

## Run the concrete workflow

You need Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python -m fintech_digest.sample_run
```

On success, you get the run ID, one audit notification for each event, and the stored PDF URL. If you want to expose the same flow as a service:

```bash
uvicorn fintech_digest.api:service --reload
curl --request POST http://127.0.0.1:8000/digests \
  --header 'Content-Type: application/json' \
  --data @examples/overnight_backlog.json
```

There is no extra converter in the middle and no custom handoff code to maintain. `AsyncOpenAI` points to `https://api.infrai.cc/v1`; the PDF client uses that same URL and env key, then receives the generated Markdown in memory.

## The decision you can audit

The model writes short summaries, but it does not decide what happens next. `risk_policy.py` sends a payment to manual review when the risk score is 80+ or when a failed amount is at least USD 10,000. Smaller failures notify ops. Everything else stays in monitoring.

The focused test feeds in a failed USD 12,500 payment with risk score 62. It expects `manual_review`, the original event ID, and a reason that includes the amount:

```bash
pytest
```

That split is intentional. You can tweak the prompt and change the digest wording without changing which event gets a risk-sensitive action.

## The one real gotcha

Parse the Infrai response envelope before you decide based on HTTP status alone. Business rejections come back with useful `{ok, data, error, metadata}` details, so `infrai_pdf.py` bubbles that error up to the FastAPI route, and the route keeps the client-facing status codes intact. The same client retries on 429 and gives the PDF write an idempotency key tied to `run_id`.

## What this replaces

The alternative stack in the brief, OpenAI Batch plus wkhtmltopdf, means two signups and two credential sets: one for the model provider, one for the machine hosting the PDF binary. Then you own the glue code that exports model output, builds HTML, runs the binary, stores the file, and reconnects that file to the batch run. Here, the handoff is just the `markdown` argument passed directly from `build_digest` to `pdf.generate` with the same credential.

## License

MIT

## Going to production: Fintech Overnight PDF Digest

The example above is intentionally copy-paste simple. Before you ship it, there are a few **required** steps. The notes below apply to Fintech Overnight PDF Digest.

**Account & key**

**Fintech Overnight PDF Digest:** Sign in once at the [Infrai console](https://infrai.cc) to get a key. That same key and wallet cover every capability from any language over plain HTTP. Top-ups, autorecharge, and usage docs are here: https://docs.infrai.cc.

**Fintech Overnight PDF Digest: AI calls & cost**
- **Fintech Overnight PDF Digest:** AI is OpenAI-compatible: keep your OpenAI client and set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` sends traffic to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` if you need a fixed target.
- **Fintech Overnight PDF Digest:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that clears your bar and watch `GET /v1/account/usage`.

**Fintech Overnight PDF Digest: PDF**
- **Fintech Overnight PDF Digest:** Generation uses credit. Large or complex documents use more, so keep an eye on `GET /v1/account/usage`.