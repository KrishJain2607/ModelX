from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    live_trading_enabled: bool = False
    broker_api_key: str = ""
    broker_api_secret: str = ""
    broker_access_token: str = ""
    market_data_provider: str = "kite"
    upstox_analytics_token: str = ""
    ai_provider: str = "cerebras"
    ai_fallback_provider: str = ""
    cerebras_api_key: str = ""
    ai_api_key: str = ""
    gemini_api_key: str = ""
    ai_model: str = "gpt-oss-120b"
    ai_technical_model: str = "gemini-3-flash-preview"
    ai_trend_model: str = "gemini-3-flash-preview"
    ai_news_model: str = "gemini-3-flash-preview"
    ai_sentiment_model: str = "gemini-3-flash-preview"
    ai_reasoning_model: str = "gemini-3-flash-preview"
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

    def approval_recipients(self) -> list[str]:
        return [item.strip().lower() for item in self.alert_to_email.split(",") if item.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
