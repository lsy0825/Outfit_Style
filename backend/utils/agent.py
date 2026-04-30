"""
Agent 全局实例管理
避免循环导入
"""
from typing import Optional
from agents.stylemate_agent import StyleMateAgent

_agent_instance: Optional[StyleMateAgent] = None


def set_agent(instance: StyleMateAgent) -> None:
    """设置全局 Agent 实例（在 lifespan 中调用）"""
    global _agent_instance
    _agent_instance = instance


def get_agent() -> StyleMateAgent:
    """获取全局 Agent 实例"""
    if _agent_instance is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Agent 未初始化")
    return _agent_instance
