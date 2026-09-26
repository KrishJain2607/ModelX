from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    modelx_version: str = "0.5.3-SNAPSHOT"
    app_env: str = "development"
    live_trading_enabled: bool = False
    broker_api_key: str = ""
    broker_api_secret: str = ""
    broker_access_token: str = ""
    market_data_provider: str = "kite"
    upstox_analytics_token: str = ""
    ai_provider: str = "gemini"
    ai_fallback_provider: str = ""
    ai_api_key: str = ""
    gemini_api_key: str = ""
    ai_model: str = "gemini-3.8-flash"
    ai_technical_model: str = "gemini-3.8-flash"
    ai_trend_model: str = "gemini-3.8-flash"
    ai_news_model: str = "gemini-3.8-flash"
    ai_sentiment_model: str = "gemini-3.8-flash"
    ai_reasoning_model: str = "gemini-3.8-flash"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_provider: str = "brevo"
    brevo_api_key: str = ""
    email_sender: str = "krishjain2607@gmail.com"
    alert_from_email: str = "krishjain2607@gmail.com"
    alert_to_email: str = "krishjain2607@gmail.com,sakshigairola65@gmail.com"
    public_base_url: str = "https://modelx-poc.onrender.com"
    approval_secret: str = ""
    approval_ttl_minutes: int = 30
    max_risk_per_trade: float = 0.005
    max_daily_loss: float = 0.02
    max_open_positions: int = 5
    max_total_exposure: float = 0.60
    min_risk_reward: float = 2.0

    # Live execution is deliberately separated from the Render research service.
    # The gateway should live behind a fixed public IP when live trading is enabled.
    execution_gateway_url: str = ""
    execution_gateway_secret: str = ""
    execution_gateway_timeout_seconds: int = 15

    # Autonomous research scheduler / paper-trading controls.
    automation_secret: str = ""
    paper_trading_capital: float = 100000.0
    automation_max_quote_universe: int = 40
    automation_max_historical_candidates: int = 20
    automation_max_ai_candidates: int = 3
    automation_min_technical_score: int = 70
    automation_min_final_rating: int = 70
    # Weekend paper-test mode uses the latest completed daily candle instead of live quotes.
    # It is paper-only and must never enable live broker execution.
    automation_weekend_test_mode: bool = True
    automation_weekend_auto_approve: bool = True
    automation_weekend_scan_workers: int = 4
    automation_weekend_batch_size: int = 100
    # Lower thresholds are isolated to weekend testing; normal automation remains at 70.
    automation_weekend_min_technical_score: int = 40
    automation_weekend_min_final_rating: int = 40
    # Weekend-only: a high-rated WATCH can enter paper testing when technical evidence is also strong.
    automation_weekend_watch_trade_min_rating: int = 70

    def approval_recipients(self) -> list[str]:
        return [item.strip().lower() for item in self.alert_to_email.split(",") if item.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
