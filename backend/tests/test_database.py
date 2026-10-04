from __future__ import annotations

from pathlib import Path

from app.config.settings import settings
from app.database import init_db, load_state, save_state


def test_state_round_trip(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "modelx.db"
    monkeypatch.setattr(settings, "database_path", str(db_path))

    init_db()
    state = {
        "status": "BATCH_COMPLETE",
        "date": "2026-10-04",
        "processed": 100,
        "decision_log": [{"symbol": "TEST", "trade_eligible": False}],
    }
    save_state("automation:test", state)

    assert load_state("automation:test") == state
