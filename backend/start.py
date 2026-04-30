"""
启动脚本 - 确保日志正确输出到终端
"""
import uvicorn
import sys
import os

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import setup_logging, get_logger

# 配置日志（在导入其他模块之前）
setup_logging(level="info", log_file=True, log_console=True)
logger = get_logger(__name__)


if __name__ == "__main__":
    logger.info("🚀 启动 StyleMate 后端服务...")
    logger.info("📝 日志将输出到终端和 logs/ 目录")
    
    # 使用 uvicorn 启动
    # 注意：reload=True 时，子进程可能不会继承日志配置
    # 所以需要确保日志配置在子进程中也能生效
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
        # 使用 asyncio 事件循环（Windows 兼容）
        loop="asyncio",
        # 使用 h11 而不是 httptools（更兼容）
        http="h11"
    )
