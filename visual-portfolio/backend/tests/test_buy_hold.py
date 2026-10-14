from __future__ import annotations

import io
import json
from pathlib import Path
import uuid
import zipfile

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.buy_hold import (
    BuyHoldError,
    BuyHoldResult,
    build_buy_hold_sea,
    save_buy_hold_sea,
)
from backend.services.parser import parse_file
from backend.services.project_access import project_dir


class FakeFetcher:
    def __init__(self, *, stock_prices=None, stock_dividends=None, futures_prices=None):
        self._stock_prices = stock_prices or []
        self._stock_dividends = stock_dividends or []
        self._futures_prices = futures_prices or []

    def stock_prices(self, code: str, start_date: str) -> list[dict]:
        return self._stock_prices

    def stock_dividends(self, code: str, start_date: str) -> list[dict]:
        return self._stock_dividends

    def futures_prices(self, code: str, start_date: str) -> list[dict]:
        return self._futures_prices


def _events(payload: bytes) -> list[dict]:
    with zipfile.ZipFile(io.BytesIO(payload), "r") as zf:
        name = next(n for n in zf.namelist() if n.endswith("/events.jsonl"))
        return [json.loads(line) for line in zf.read(name).decode("utf-8").splitlines() if line.strip()]


def _new_user(prefix: str) -> tuple[str, str]:
    token = uuid.uuid4().hex[:10]
    return f"{prefix}_{token}", f"pw_{token}"


def _signup_and_login(client: TestClient, user_id: str, password: str) -> None:
    signup = client.post("/auth/signup", json={"user_id": user_id, "password": password})
    assert signup.status_code == 200
    login = client.post("/auth/login", json={"user_id": user_id, "password": password})
    assert login.status_code == 200


def _create_project(client: TestClient, name: str) -> str:
    resp = client.post("/projects", json={"project_name": name})
    assert resp.status_code == 200
    return resp.json()["project_id"]


def test_stock_buy_hold_uses_bh_name_fractional_quantity_and_reinvests_dividend(tmp_path):
    result = build_buy_hold_sea(
        folder=tmp_path,
        buy_date="2025-01-01",
        amount_wan_text="1",
        product_type="股票",
        code="2330",
        fetcher=FakeFetcher(
            stock_prices=[
                {"date": "2025-01-01", "close": 300},
                {"date": "2025-01-02", "close": 330},
            ],
            stock_dividends=[
                {"date": "2025-01-02", "cash_earnings_distribution": 3},
            ],
        ),
    )

    assert result.display_name == "BH2330_1萬"
    assert result.filename == "BH2330_1萬.sea"
    assert abs(result.quantity - 33.6363636363) < 1e-9

    events = _events(result.payload)
    assert events[0]["data"]["quantity"] == 10000 / 300
    assert events[1]["type"] == "trade"
    assert abs(events[1]["data"]["quantity"] - ((10000 / 300) * 3 / 330)) < 1e-9


def test_stock_buy_hold_adjusts_detected_split_without_loss_spike(tmp_path):
    result = build_buy_hold_sea(
        folder=tmp_path,
        buy_date="2025-06-09",
        amount_wan_text="100",
        product_type="股票",
        code="0050",
        fetcher=FakeFetcher(
            stock_prices=[
                {"date": "2025-06-09", "close": 183.7},
                {"date": "2025-06-10", "close": 188.65},
                {"date": "2025-06-18", "close": 47.57},
                {"date": "2025-06-19", "close": 47.1},
            ],
        ),
    )

    events = _events(result.payload)
    split_sells = [e for e in events if e["type"] == "trade" and e["timestamp"].startswith("2025-06-18") and e["data"]["quantity"] < 0]
    split_buys = [e for e in events if e["type"] == "trade" and e["timestamp"].startswith("2025-06-18") and e["data"]["quantity"] > 0]
    assert split_sells
    assert split_buys
    assert abs(split_buys[0]["data"]["quantity"] - abs(split_sells[0]["data"]["quantity"]) * 4) < 1e-9

    path = tmp_path / result.filename
    path.write_bytes(result.payload)
    rows = parse_file(path, strategy_index=0)
    pnl_by_date = {row.trade_date2.strftime("%Y-%m-%d"): row.net_profit for row in rows}
    assert abs(pnl_by_date["2025-06-18"]) < 1e-6


def test_futures_buy_hold_uses_fractional_quantity_and_rolls_contract(tmp_path):
    result = build_buy_hold_sea(
        folder=tmp_path,
        buy_date="2025-01-01",
        amount_wan_text="100",
        product_type="期貨",
        code="TX",
        leverage_text="5",
        fetcher=FakeFetcher(
            futures_prices=[
                {"date": "2025-01-01", "contract_date": "202501", "close": 3030},
                {"date": "2025-01-02", "contract_date": "202502", "close": 3060},
            ],
        ),
    )

    assert result.display_name == "BHTX_100萬_5X"
    assert result.filename == "BHTX_100萬_5X.sea"
    assert abs(result.quantity - (1_000_000 * 5 / 3030)) < 1e-9
    events = _events(result.payload)
    assert events[0]["data"]["instrument_id"] == "TX_202501"
    assert events[1]["data"]["quantity"] < 0
    assert events[2]["data"]["instrument_id"] == "TX_202502"
    assert events[2]["data"]["quantity"] == result.quantity


def test_generated_filename_collision_overwrites_same_name(tmp_path):
    (tmp_path / "BH2330_100萬.sea").write_bytes(b"existing")
    result = build_buy_hold_sea(
        folder=tmp_path,
        buy_date="2025-01-01",
        amount_wan_text="100",
        product_type="股票",
        code="2330",
        fetcher=FakeFetcher(stock_prices=[{"date": "2025-01-01", "close": 100}]),
    )

    assert result.filename == "BH2330_100萬.sea"
    save_buy_hold_sea(tmp_path, result)
    assert (tmp_path / "BH2330_100萬.sea").read_bytes() != b"existing"


def test_buy_hold_api_owner_only_and_no_file_on_error(monkeypatch):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("demo/strategy.toml", "[params]\n")
        zf.writestr(
            "demo/events.jsonl",
            '{"timestamp":"2025-01-01T00:00:00Z","type":"trade","data":{"instrument_id":"2330","price":100,"quantity":1}}\n',
        )

    def fake_build(**kwargs):
        return BuyHoldResult(
            display_name="BH2330_100萬",
            filename="BH2330_100萬.sea",
            payload=payload.getvalue(),
            quantity=1.0,
            points=[],
        )

    monkeypatch.setattr("backend.routers.buy_hold.build_buy_hold_sea", fake_build)

    with TestClient(app) as owner_client:
        owner, pw = _new_user("bh_owner")
        _signup_and_login(owner_client, owner, pw)
        project_id = _create_project(owner_client, "buy-hold-api")
        resp = owner_client.post(
            f"/projects/{project_id}/buy-hold",
            json={"date": "2025-01-01", "amount_wan": "100", "product_type": "股票", "code": "2330"},
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "BH2330_100萬"
        assert (project_dir(project_id) / "BH2330_100萬.sea").exists()

    with TestClient(app) as stranger_client:
        stranger, pw = _new_user("bh_stranger")
        _signup_and_login(stranger_client, stranger, pw)
        forbidden = stranger_client.post(
            f"/projects/{project_id}/buy-hold",
            json={"date": "2025-01-01", "amount_wan": "100", "product_type": "股票", "code": "2330"},
        )
        assert forbidden.status_code == 403


def test_buy_hold_api_does_not_create_file_when_generation_fails(monkeypatch):
    def fail_build(**kwargs):
        raise BuyHoldError("FinMind has no usable stock price data")

    monkeypatch.setattr("backend.routers.buy_hold.build_buy_hold_sea", fail_build)

    with TestClient(app) as client:
        user, pw = _new_user("bh_fail")
        _signup_and_login(client, user, pw)
        project_id = _create_project(client, "buy-hold-fail")
        before = set(p.name for p in project_dir(project_id).glob("*.sea"))
        resp = client.post(
            f"/projects/{project_id}/buy-hold",
            json={"date": "2025-01-01", "amount_wan": "100", "product_type": "股票", "code": "2330"},
        )
        after = set(p.name for p in project_dir(project_id).glob("*.sea"))

    assert resp.status_code == 400
    assert "FinMind has no usable stock price data" in resp.json()["detail"]
    assert after == before


def test_generated_buy_hold_sea_parses_with_naive_datetimes(tmp_path):
    result = build_buy_hold_sea(
        folder=tmp_path,
        buy_date="2025-01-01",
        amount_wan_text="100",
        product_type="股票",
        code="0050",
        fetcher=FakeFetcher(
            stock_prices=[
                {"date": "2025-01-01", "close": 100},
                {"date": "2025-01-02", "close": 101},
            ],
        ),
    )
    path = tmp_path / result.filename
    path.write_bytes(result.payload)

    rows = parse_file(path, strategy_index=0)

    assert rows
    assert all(row.trade_date2.tzinfo is None for row in rows)


def test_generated_buy_hold_file_runs_analysis_with_date_range(monkeypatch):
    def fake_build(**kwargs):
        result = build_buy_hold_sea(
            folder=kwargs["folder"],
            buy_date="2025-01-01",
            amount_wan_text="100",
            product_type="股票",
            code="0050",
            fetcher=FakeFetcher(
                stock_prices=[
                    {"date": "2025-01-01", "close": 100},
                    {"date": "2025-01-02", "close": 101},
                    {"date": "2025-01-03", "close": 102},
                ],
            ),
        )
        return result

    monkeypatch.setattr("backend.routers.buy_hold.build_buy_hold_sea", fake_build)

    with TestClient(app) as client:
        user, pw = _new_user("bh_analysis")
        _signup_and_login(client, user, pw)
        project_id = _create_project(client, "buy-hold-analysis")
        create = client.post(
            f"/projects/{project_id}/buy-hold",
            json={"date": "2025-01-01", "amount_wan": "100", "product_type": "股票", "code": "0050"},
        )
        assert create.status_code == 200
        filename = create.json()["filename"]

        analysis = client.post(
            f"/projects/{project_id}/analysis",
            json={
                "equities": [
                    {
                        "filename": filename,
                        "active": True,
                        "contract": 1,
                        "weight": 1,
                        "color": "#0a9396",
                        "name": "BH0050_100萬",
                    }
                ],
                "date_range": {"all": False, "start": "2025-01-01", "end": "2025-01-03"},
                "options": {"risk_free_rate": 0, "mdd_count": 5, "commission_per_trade": 0},
            },
        )

    assert analysis.status_code == 200
    assert analysis.json()["summary"]["trade_count"] > 0
