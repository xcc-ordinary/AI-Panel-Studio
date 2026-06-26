"""统一配置入口：所有敏感信息、可变参数都从环境变量读取，绝不硬编码。"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 大模型相关：模型名/地址/Key 全部走环境变量，换模型不改代码
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"  # 实际模型名以你账户可用的为准

    # 前端地址，用于 CORS 白名单
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()  # 全局唯一配置实例
