"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="Instant Payment Risk Mesh",
    version="0.1.0",
    description="Real-time SCT Inst scoring & case management API",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
