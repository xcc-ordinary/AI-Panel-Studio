"""FastAPI 应用入口：本阶段只做最小骨架——CORS + 一个健康检查接口。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="AI Panel Studio API")

# 配置 CORS：只允许我们的前端地址访问，避免开发时跨域被浏览器拦截
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    """健康检查：用于验证后端是否正常启动，也方便 Phase 5 的 E2E 探活。"""
    return {"status": "ok", "model": settings.deepseek_model}
