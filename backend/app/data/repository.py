from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.models import Candle, Instrument


def upsert_instruments(db: Session, rows: Iterable[dict]) -> int:
    count = 0
    for row in rows:
        existing = db.scalar(
            select(Instrument).where(
                Instrument.exchange == row["exchange"],
                Instrument.tradingsymbol == row["tradingsymbol"],
            )
        )
        values = {
            "instrument_token": int(row["instrument_token"]),
            "exchange": row["exchange"],
            "tradingsymbol": row["tradingsymbol"],
            "name": row.get("name"),
            "instrument_type": row.get("instrument_type"),
            "segment": row.get("segment"),
            "tick_size": row.get("tick_size"),
            "lot_size": row.get("lot_size"),
        }
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
        else:
            db.add(Instrument(**values))
        count += 1
    db.commit()
    return count


def insert_candles(db: Session, rows: Iterable[dict]) -> int:
    count = 0
    for row in rows:
        exists = db.scalar(
            select(Candle.id).where(
                Candle.instrument_token == row["instrument_token"],
                Candle.interval == row["interval"],
                Candle.timestamp == row["timestamp"],
            )
        )
        if exists is not None:
            continue
        db.add(Candle(**row))
        count += 1
    db.commit()
    return count
