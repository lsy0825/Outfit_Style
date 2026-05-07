"""
StyleMate - 基于实时天气与场景的穿搭推荐助手
后端主程序
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from agents.stylemate_agent import StyleMateAgent
from api.health import router as health_router
from utils.cache import CacheManager
from utils.agent import set_agent
from utils.logger import setup_logging, get_logger

# 延迟导入以避免循环导入
from api.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 配置日志（确保在每个进程中都执行）
    setup_logging(level="info", log_file=True, log_console=True)
    
    # 获取 logger
    logger = get_logger(__name__)
    
    # 启动时初始化
    logger.info("🚀 StyleMate 后端服务启动中...")
    
    # 初始化 Agent
    agent = StyleMateAgent()
    await agent.initialize()
    set_agent(agent)
    logger.info("✅ Agent 初始化完成")
    
    # 初始化 RAG 知识库（延迟初始化，避免阻塞启动）
    logger.info("📚 正在初始化 RAG 知识库...")
    try:
        from rag.retriever_tool import setup_knowledge_base
        docx_path = r"C:\Users\12629\Desktop\穿搭核心原则.docx"
        result = setup_knowledge_base(docx_path)
        if result["success"]:
            logger.info(f"✅ RAG 知识库初始化完成，已加载 {result['document_count']} 个文档块")
        else:
            logger.warning(f"⚠️ RAG 知识库初始化失败：{result.get('error', '未知错误')}")
    except Exception as e:
        logger.warning(f"⚠️ RAG 知识库初始化失败：{str(e)}")
    
    yield
    
    # 关闭时清理
    logger.info("👋 StyleMate 后端服务关闭")


app = FastAPI(
    title="StyleMate API",
    description="穿搭推荐 AI Agent API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router, prefix="/v1")
app.include_router(health_router, prefix="/v1")

@app.get("/")
async def root():
    """根路径欢迎页"""
    return {
        "service": "StyleMate",
        "description": "基于实时天气与场景的穿搭推荐助手",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/v1/chat/stream (SSE)",
            "health": "/v1/health"
        }
    }


if __name__ == "__main__":
    # 配置日志（主进程）
    setup_logging(level="info", log_file=True, log_console=True)
    logger = get_logger(__name__)
    
    logger.info("🚀 启动 StyleMate 后端服务...")
    logger.info("📝 日志将输出到终端和 logs/ 目录")
    logger.info("🔄 已禁用 reload 模式，避免日志文件触发重新加载")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 关闭 reload，避免日志文件触发 reload
        log_level="info",
        access_log=True,
        http="h11",  # 使用不缓冲的 HTTP 服务器
        loop="asyncio"  # Windows 兼容：使用标准 asyncio 事件循环
    )
