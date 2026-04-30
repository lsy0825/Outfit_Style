"""
StyleMate Agent - 穿搭推荐核心 Agent
使用 LangChain + qwen3-max 实现，支持真正逐 token 流式输出

关键优化：
- Agent 工具调用阶段：立即推送「正在查询天气...」给前端，避免空白等待
- LLM 流式输出阶段：逐 token 推送，实现打字机效果
"""
from typing import AsyncGenerator, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
import json
import re
import asyncio

from tools.weather_tool import get_weather
from tools.sunset_tool import get_sunset
from tools.geocoding_tool import geocode_city
from models.clothing import ClothingAdvice
from utils.cache import CacheManager
from utils.prompt import SYSTEM_PROMPT

# 用于存储每个会话的对话历史（简单内存实现）
SESSION_HISTORY: Dict[str, List[Dict]] = {}


class StyleMateAgent:
    """StyleMate 穿搭推荐 Agent"""

    def __init__(self):
        self.llm = None
        self.agent_executor = None
        self.cache = CacheManager()

    async def initialize(self):
        """初始化 Agent"""
        # 初始化 LLM（streaming=True 才能逐 token 输出）
        self.llm = ChatOpenAI(
            model="qwen3-max",
            api_key="sk-9ab6aa9d33cb4596813f1caeeede0903",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            temperature=0.7,
            streaming=True
        )

        # 定义工具
        tools = [get_weather, get_sunset, geocode_city]

        # 创建 Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 创建 Agent
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            early_stopping_method="generate"
        )

    async def chat_stream(self, user_input: str, session_id: str = "default") -> AsyncGenerator[str, None]:
        """
        逐 token 流式对话接口

        使用 AgentExecutor.astream 统一处理所有请求，让 Agent 自己决定是否调用工具。
        无论是否需要工具，都保持一致的流式输出体验。
        """
        try:
            # 获取对话历史
            history = SESSION_HISTORY.get(session_id, [])
            history_str = ""
            if history:
                for msg in history[-6:]:
                    role = msg.get("role", "human")
                    content = msg.get("content", "")
                    if role == "human":
                        history_str += f"用户：{content}\n"
                    else:
                        history_str += f"助手：{content}\n"

            full_input = f"{history_str}用户：{user_input}" if history_str else user_input
            print(f"full_input: {full_input}")
            
            full_output_parts = []
            got_output = False

            # 使用 AgentExecutor.astream 统一处理所有请求
            # Agent 会自动决定是否调用工具
            async for chunk in self.agent_executor.astream(
                {"input": full_input},
                config={"configurable": {"session_id": session_id}}
            ):
                if isinstance(chunk, dict):
                    # LLM 输出阶段：逐 token 推送
                    if "output" in chunk:
                        token = chunk["output"]
                        if token:
                            got_output = True
                            full_output_parts.append(token)
                            # 逐字符发送，确保流式效果
                            for char in token:
                                data = json.dumps(
                                    {"type": "text_chunk", "data": char},
                                    ensure_ascii=False
                                )
                                yield f"data: {data}\n\n"
                                await asyncio.sleep(0.02)

            # 如果 astream 没有流式输出（某些情况下降级）
            if not got_output:
                result = await self.agent_executor.ainvoke({"input": full_input})
                output = result.get("output", "")
                full_output_parts = [output]
                # 逐字符输出（降级方案）
                for char in output:
                    data = json.dumps(
                        {"type": "text_chunk", "data": char},
                        ensure_ascii=False
                    )
                    yield f"data: {data}\n\n"
                    await asyncio.sleep(0.02)

            # 保存对话历史
            full_output = "".join(full_output_parts)
            if session_id not in SESSION_HISTORY:
                SESSION_HISTORY[session_id] = []
            SESSION_HISTORY[session_id].append({"role": "human", "content": user_input})
            SESSION_HISTORY[session_id].append({"role": "assistant", "content": full_output})
            SESSION_HISTORY[session_id] = SESSION_HISTORY[session_id][-20:]

            # 发送结束标记
            yield "data: [DONE]\n\n"

        except Exception as e:
            error_msg = f"处理请求时出错: {str(e)}"
            data = json.dumps({"type": "error", "data": error_msg}, ensure_ascii=False)
            yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"

    def chat(self, user_input: str, session_id: str = "default") -> str:
        """非流式对话接口"""
        try:
            result = self.agent_executor.invoke({"input": user_input})
            return result.get("output", "抱歉，我无法处理您的请求。")
        except Exception as e:
            return f"处理请求时出错: {str(e)}"

    def clear_history(self, session_id: str = "default"):
        """清除指定会话的历史"""
        if session_id in SESSION_HISTORY:
            del SESSION_HISTORY[session_id]
