from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    live_trading_enabled: bool = False
    broker_api_key: str = ""
    broker_api_secret: str = ""
    broker_access_token: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    alert_from_email: str = ""
    alert_to_email: str = ""
    max_risk_per_trade: float = 0.005
    max_daily_loss: float = 0.02
    max_open_positions: int = 5
    max_total_exposure: float = 0.60
    min_risk_reward: float = 2.0
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
