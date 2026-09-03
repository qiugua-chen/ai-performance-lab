import asyncio
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query


app = FastAPI(
    title="AI Performance Lab Demo API",
    description="A deterministic and controllable API target for M0.",
    version="0.0.0",
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    """Return the service health status."""

    return {
        "status": "ok",
    }


@app.get("/api/normal")
async def normal() -> dict[str, str]:
    """Return a deterministic successful response."""

    return {
        "mode": "normal",
        "message": "request completed successfully",
    }


@app.get("/api/slow")
async def slow(
    delay_ms: Annotated[
        int,
        Query(
            ge=0,
            le=5000,
            description="Controlled response delay in milliseconds.",
        ),
    ] = 500,
) -> dict[str, int | str]:
    """Return a successful response after a controlled delay."""

    await asyncio.sleep(delay_ms / 1000)

    return {
        "mode": "slow",
        "delay_ms": delay_ms,
    }


@app.get("/api/error")
async def error(
    status_code: Annotated[
        int,
        Query(
            ge=400,
            le=599,
            description="Controlled HTTP error status code.",
        ),
    ] = 500,
):
    """Return a controlled HTTP error response."""

    raise HTTPException(
        status_code=status_code,
        detail="controlled error response",
    )