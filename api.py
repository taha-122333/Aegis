"""
Aegis API: FastAPI layer exposing portfolio allocation and risk analysis
over HTTP. Run with: uvicorn api:app --reload
Then visit http://127.0.0.1:8000/docs for interactive API docs.
"""

from fastapi import FastAPI, HTTPException

from engine.api_models import (
    AllocationRequest,
    AllocationResponse,
    RiskReportRequest,
    RiskReportResponse,
)
from engine.api_service import build_allocation_result, build_risk_report, InsufficientDataError
from engine.config import TICKERS

app = FastAPI(
    title="Aegis API",
    description="Portfolio construction and risk engine. Research/educational tool — not investment advice.",
    version="0.1.0",
)


@app.get("/")
def root():
    """Basic health check / welcome message."""
    return {"status": "ok", "message": "Aegis API is running. Visit /docs for interactive API documentation."}


@app.get("/universe")
def default_universe():
    """Returns the default asset universe used elsewhere in the project (for reference only — /allocate and /risk-report accept any tickers)."""
    return {"default_tickers": TICKERS}


@app.post("/allocate", response_model=AllocationResponse)
def allocate(request: AllocationRequest):
    """Computes portfolio weights for the given tickers and allocation method."""
    try:
        return build_allocation_result(request.tickers, request.method, request.target_return)
    except InsufficientDataError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not compute allocation: {e}")


@app.post("/risk-report", response_model=RiskReportResponse)
def risk_report(request: RiskReportRequest):
    """Computes portfolio weights AND a full risk report (VaR, CVaR, drawdown, Sharpe, Sortino, COVID stress test)."""
    try:
        return build_risk_report(request.tickers, request.method, request.confidence)
    except InsufficientDataError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not compute risk report: {e}")