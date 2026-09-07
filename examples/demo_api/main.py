import asyncio
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query


app = FastAPI(
    title="AI Performance Lab Demo API",
    description="用于 M0 验证、行为可控的被测 API 服务。",
    version="0.0.0",
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    """返回服务健康状态。"""

    return {
        "status": "ok",
    }


@app.get("/api/normal")
async def normal() -> dict[str, str]:
    """返回确定的成功响应。"""

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
            description="响应延迟，单位为毫秒。",
        ),
    ] = 500,
) -> dict[str, int | str]:
    """经过指定延迟后返回成功响应。"""

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
            description="指定返回的 HTTP 错误状态码。",
        ),
    ] = 500,
):
    """返回可控的 HTTP 错误响应。"""

    raise HTTPException(
        status_code=status_code,
        detail="controlled error response",
    )