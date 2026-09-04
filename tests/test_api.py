"""
Tests for the FastAPI layer. Validation tests run fast with no network
calls; the end-to-end tests hit real yfinance data to confirm the full
request-to-response pipeline actually works.
"""

from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_root_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_default_universe_endpoint():
    response = client.get("/universe")
    assert response.status_code == 200
    assert "default_tickers" in response.json()


def test_allocate_rejects_duplicate_tickers():
    response = client.post("/allocate", json={
        "tickers": ["AAPL", "AAPL", "GLD"],
        "method": "equal_weight",
    })
    assert response.status_code == 422


def test_allocate_rejects_too_few_tickers():
    response = client.post("/allocate", json={
        "tickers": ["AAPL"],
        "method": "equal_weight",
    })
    assert response.status_code == 422


def test_allocate_rejects_invalid_method():
    response = client.post("/allocate", json={
        "tickers": ["AAPL", "GLD"],
        "method": "not_a_real_method",
    })
    assert response.status_code == 422


def test_allocate_equal_weight_end_to_end():
    """Integration test: hits real yfinance data, checks the full pipeline."""
    response = client.post("/allocate", json={
        "tickers": ["AAPL", "MSFT", "GLD"],
        "method": "equal_weight",
    })
    assert response.status_code == 200
    data = response.json()
    assert set(data["weights"].keys()) == {"AAPL", "MSFT", "GLD"}
    assert abs(sum(data["weights"].values()) - 1.0) < 0.01


def test_risk_report_end_to_end():
    """Integration test: hits real yfinance data, checks a full risk report comes back."""
    response = client.post("/risk-report", json={
        "tickers": ["AAPL", "GLD"],
        "method": "risk_parity",
    })
    assert response.status_code == 200
    data = response.json()
    assert "sharpe_ratio" in data
    assert data["conditional_value_at_risk"]["historical"] >= data["value_at_risk"]["historical"]