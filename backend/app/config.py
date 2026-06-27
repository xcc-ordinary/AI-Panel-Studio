"""统一配置入口：所有敏感信息、可变参数都从环境变量读取，绝不硬编码。"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 大模型相关：模型名/地址/Key 全部走环境变量，换模型不改代码
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # 前端地址（逗号分隔多个），用于 CORS 白名单
    frontend_origins: str = "http://localhost:5173,http://localhost:5174"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.frontend_origins.split(",") if o.strip()]

    # 数据库
    database_path: str = "data/apanel.db"

    # 讨论并发上限
    max_concurrent_discussions: int = 10

    # 发言调度：最大轮次兜底
    default_max_rounds: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
