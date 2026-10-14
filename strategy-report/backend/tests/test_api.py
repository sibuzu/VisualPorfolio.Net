from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

from strategy_report.main import app


SAMPLE = Path(__file__).parent / "fixtures" / "BDS_TXF.srp"


def test_health_and_report_api():
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        payload = SAMPLE.read_bytes()
        response = client.post("/api/report", files={"file": ("report.srp", payload)},
                               data={"settings": '{"mode":"backtest"}'})
        assert response.status_code == 200
        report = response.json()
        assert report["source"]["format"] == "srp"
        assert report["compound"]["summary"]["trade_count"] > 0
        assert report["compound"]["periods"]["annual"]
        assert client.post("/api/report", files={"file": ("bad.txt", b"bad")}).status_code == 422


def test_concurrent_requests_are_independent():
    def one(capital: int) -> float:
        body = (
            '<策略回測><參數><策略>Demo</策略></參數><策略交易>'
            '<Trade time_stamp="2024/01/01 09:00:00" bs="B" contract="1" price="100"/>'
            '<Trade time_stamp="2024/01/02 09:00:00" bs="S" contract="1" price="105"/>'
            '</策略交易></策略回測>'
        ).encode()
        with TestClient(app) as client:
            response = client.post("/api/report", files={"file": ("demo.srp", body)},
                                   data={"settings": f'{{"mode":"fixed_quantity","initial_capital":{capital}}}'})
            assert response.status_code == 200
            return response.json()["compound"]["summary"]["final_capital"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(one, (100_000, 200_000)))
    assert results == [100_005, 200_005]
