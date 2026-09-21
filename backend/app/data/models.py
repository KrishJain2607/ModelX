from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.data.db import Base


class Instrument(Base):
    __tablename__ = "instruments"
    __table_args__ = (UniqueConstraint("exchange", "tradingsymbol", name="uq_instrument_symbol"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_token: Mapped[int] = mapped_column(BigInteger, index=True)
    exchange: Mapped[str] = mapped_column(String(20), index=True)
    tradingsymbol: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    instrument_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    segment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tick_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    lot_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Candle(Base):
    __tablename__ = "candles"
    __table_args__ = (
        UniqueConstraint("instrument_token", "interval", "timestamp", name="uq_candle"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_token: Mapped[int] = mapped_column(BigInteger, index=True)
    exchange: Mapped[str] = mapped_column(String(20), index=True)
    tradingsymbol: Mapped[str] = mapped_column(String(100), index=True)
    interval: Mapped[str] = mapped_column(String(20), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
