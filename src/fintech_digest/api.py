from fastapi import FastAPI, HTTPException

from .digest_service import build_digest, runtime_clients
from .infrai_pdf import InfraiError
from .models import DigestRequest, DigestResponse


service = FastAPI(title="Overnight payment digest")


@service.post("/digests", response_model=DigestResponse)
async def create_digest(request: DigestRequest) -> DigestResponse:
    ai, pdf = runtime_clients()
    try:
        return await build_digest(request, ai, pdf.generate)
    except InfraiError as error:
        status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=error.detail) from error

