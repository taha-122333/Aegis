"""
Pydantic models: define the exact shape of data the API accepts and
returns. FastAPI uses these for automatic validation (rejecting bad
requests before your code even runs) and to auto-generate the /docs page.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


AllocationMethod = Literal["markowitz", "risk_parity", "kelly", "equal_weight"]


class AllocationRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=2, description="List of ticker symbols, e.g. ['AAPL', 'GLD', 'BTC-USD']")
    method: AllocationMethod = Field(..., description="Allocation method to use")
    target_return: Optional[float] = Field(
        None, description="Optional annual target return for Markowitz only (e.g. 0.15 for 15%)"
    )

    @field_validator("tickers")
    @classmethod
    def tickers_must_be_uppercase_and_unique(cls, v):
        v = [t.strip().upper() for t in v]
        if len(set(v)) != len(v):
            raise ValueError("Duplicate tickers are not allowed")
        return v


class AllocationResponse(BaseModel):
    weights: dict[str, float]
    expected_return: float
    expected_volatility: float


class RiskReportRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=2)
    method: AllocationMethod
    confidence: float = Field(0.95, gt=0.5, lt=1.0, description="VaR/CVaR confidence level, e.g. 0.95")

    @field_validator("tickers")
    @classmethod
    def tickers_must_be_uppercase_and_unique(cls, v):
        v = [t.strip().upper() for t in v]
        if len(set(v)) != len(v):
            raise ValueError("Duplicate tickers are not allowed")
        return v


class RiskReportResponse(BaseModel):
    weights: dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    value_at_risk: dict[str, float]
    conditional_value_at_risk: dict[str, float]
    covid_stress_test: Optional[dict] = None