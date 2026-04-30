"""
聊天接口 - SSE 流式输出
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncGenerator, Optional
import json
import asyncio

from utils.agent import get_agent
from models.clothing import ChatRequest

router = APIRouter()


class ChatMessage(BaseModel):
    """聊天请求体"""
    message: str
    session_id: Optional[str] = "default"
    stream: Optional[bool] = True


@router.post("/chat/stream")
async def chat_stream(request: ChatMessage):
    """
    SSE 流式聊天接口
    
    返回 Server-Sent Events 格式的数据流
    """
    import sys
    
    agent = get_agent()
    
    async def generate() -> AsyncGenerator[str, None]:
        """生成 SSE 数据流"""
        try:
            # Agent 自己会发送 start 事件，这里不再重复发送
            # 流式调用 Agent 进行对话
            async for chunk in agent.chat_stream(request.message, request.session_id):
                yield chunk
                # 强制刷新输出缓冲区
                sys.stdout.flush()
                
            # 发送结束标记
            yield f"data: {json.dumps({'type': 'end'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            error_data = {
                "type": "error",
                "data": str(e)
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            "Transfer-Encoding": "chunked",  # 启用分块传输
            "Pragma": "no-cache"
        }
    )


@router.post("/chat")
async def chat(request: ChatMessage):
    """
    非流式聊天接口（备用）
    """
    agent = get_agent()
    
    try:
        result = agent.chat(request.message, request.session_id)
        return {
            "session_id": request.session_id,
            "message": result,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    获取会话历史（待实现）
    """
    return {
        "session_id": session_id,
        "messages": [],
        "note": "会话历史功能待实现"
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    删除会话（待实现）
    """
    return {
        "session_id": session_id,
        "status": "deleted",
        "note": "会话删除功能待实现"
    }
