import asyncio
import json
from pathlib import Path

from .digest_service import build_digest, runtime_clients
from .models import DigestRequest


def main() -> None:
    sample_path = Path(__file__).parents[2] / "examples" / "overnight_backlog.json"
    request = DigestRequest.model_validate_json(sample_path.read_text(encoding="utf-8"))
    ai, pdf = runtime_clients()
    result = asyncio.run(build_digest(request, ai, pdf.generate))
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()

