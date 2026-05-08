"""
聊天接口 - 非流式输出（主接口）
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, AsyncGenerator
from fastapi.responses import StreamingResponse
import json
import sys
import asyncio

from utils.agent import get_agent

router = APIRouter()


class ChatMessage(BaseModel):
    """聊天请求体"""
    message: str
    session_id: Optional[str] = "default"
    user_id: Optional[str] = "default_user"


class ChatResponse(BaseModel):
    """聊天响应体"""
    session_id: str
    user_id: str
    message: str
    images: List[str] = []
    advice: Optional[dict] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatMessage):
    """
    非流式聊天接口（主接口）
    返回包含文本回复和图片列表的响应
    """
    agent = get_agent()
    
    try:
        result = agent.chat(request.message, request.session_id, request.user_id)
        
        # 解析结果（包含文本和图片）
        message = result.get("message", "")
        images = result.get("images", [])
        advice = result.get("advice", None)
        
        return {
            "session_id": request.session_id,
            "user_id": request.user_id,
            "message": message,
            "images": images,
            "advice": advice
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# """
# @router.post("/chat/stream")
# async def chat_stream(request: ChatMessage):
#     """
#     SSE 流式聊天接口（已停用）
#     
#     返回 Server-Sent Events 格式的数据流
#     """
#     agent = get_agent()
#     
#     async def generate() -> AsyncGenerator[str, None]:
#         """生成 SSE 数据流"""
#         try:
#             async for chunk in agent.chat_stream(request.message, request.session_id, request.user_id):
#                 yield chunk
#                 sys.stdout.flush()
#                 
#             yield f"data: {json.dumps({'type': 'end'}, ensure_ascii=False)}\n\n"
#             
#         except Exception as e:
#             error_data = {
#                 "type": "error",
#                 "data": str(e)
#             }
#             yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
#             yield "data: [DONE]\n\n"
#     
#     return StreamingResponse(
#         generate(),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "Connection": "keep-alive",
#             "X-Accel-Buffering": "no",
#             "Transfer-Encoding": "chunked",
#             "Pragma": "no-cache"
#         }
#     )
# """


@router.get("/user/profile")
async def get_user_profile(user_id: str):
    """
    获取用户画像
    """
    agent = get_agent()
    
    try:
        profile = agent.get_user_profile(user_id)
        if profile:
            return profile.model_dump()
        return {"message": "用户画像不存在"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/profile")
async def update_user_profile(user_id: str, profile_data: dict):
    """
    更新用户画像
    """
    agent = get_agent()
    
    try:
        updated_profile = agent.update_user_profile(user_id, profile_data)
        if updated_profile:
            return updated_profile.model_dump()
        return {"message": "更新失败"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    获取会话历史
    """
    agent = get_agent()
    
    try:
        history = agent.get_session_history(session_id)
        return {
            "session_id": session_id,
            "messages": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    删除会话
    """
    agent = get_agent()
    
    try:
        agent.clear_history(session_id)
        return {
            "session_id": session_id,
            "status": "deleted"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
