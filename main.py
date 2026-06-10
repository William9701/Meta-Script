"""
main.py
FastAPI application entry point.

Run with:
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

Note: keep --workers 1 for uvicorn; concurrency is handled internally
via ThreadPoolExecutor so MT5 calls don't block the event loop.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from config import settings
from schemas import LoginRequest, AccountDetailsResponse, ErrorResponse
from mt5_client import fetch_account_details

# ------------------------------------------------------------------ #
#  App setup
# ------------------------------------------------------------------ #

app = FastAPI(
    title="MetaTrader 5 Account API",
    description="Fetch complete MT5 account details via a single POST request.",
    version="1.0.0",
)

# Shared thread pool — size controlled by config
_executor = ThreadPoolExecutor(max_workers=settings.max_workers)


# ------------------------------------------------------------------ #
#  Routes
# ------------------------------------------------------------------ #

@app.get("/health", tags=["health"])
async def health():
    """Simple liveness check."""
    return {"status": "ok"}


@app.post(
    "/account/details",
    response_model=AccountDetailsResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad credentials or MT5 error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["account"],
    summary="Fetch all MT5 account details",
)
async def get_account_details(body: LoginRequest):
    """
    Login to a MetaTrader 5 account and return **all** available data:

    - Account info (balance, equity, margin, leverage, …)
    - Open positions
    - Pending orders
    - Deal history (last N days, configurable)
    - Historical orders
    - List of symbols ever traded
    """
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            _executor,
            fetch_account_details,
            body.login,
            body.password,
            body.server,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail={"error": str(exc)})
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": f"Unexpected error: {exc}"})

    return JSONResponse(content=result)


# ------------------------------------------------------------------ #
#  Entry point (optional – you can also use uvicorn CLI)
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=False,          # keep False in production
    )
