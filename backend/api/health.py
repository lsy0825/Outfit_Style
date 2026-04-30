"""
健康检查接口
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    健康检查
    
    Returns:
        服务状态信息
    """
    return {
        "status": "ok",
        "service": "StyleMate",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """
    详细健康检查（待实现）
    
    检查：
    - LLM API 连接
    - Redis 连接
    - 外部 API 可用性
    """
    return {
        "status": "ok",
        "checks": {
            "llm_api": "unknown",
            "redis": "unknown",
            "weather_api": "unknown"
        },
        "note": "详细健康检查功能待实现"
    }
