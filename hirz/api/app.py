"""Liveness only; dependency readiness belongs to a later roadmap item."""

from fastapi import FastAPI

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
