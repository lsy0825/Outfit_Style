"""
StyleMate Agent - 穿搭推荐核心 Agent
使用 LangChain + qwen3-max 实现，支持真正逐 token 流式输出

关键优化：
- Agent 工具调用阶段：立即推送「正在查询天气...」给前端，避免空白等待
- LLM 流式输出阶段：逐 token 推送，实现打字机效果
- 用户偏好存储：使用 SQLite 实现跨会话复用
"""
from typing import AsyncGenerator, List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import json
import re
import asyncio

from tools.weather_tool import get_weather
from tools.sunset_tool import get_sunset
from tools.geocoding_tool import geocode_city
from models.clothing import ClothingAdvice, UserFashionProfile
from utils.cache import CacheManager
from utils.prompt import SYSTEM_PROMPT
from utils.user_profile_store import get_user_profile_store
from rag.retriever_tool import retrieve_knowledge

# 用于存储每个会话的对话历史（简单内存实现）
SESSION_HISTORY: Dict[str, List[Dict]] = {}


class StyleMateAgent:
    """StyleMate 穿搭推荐 Agent"""

    def __init__(self):
        self.llm = None
        self.agent_executor = None
        self.cache = CacheManager()
        self.user_profile_store = get_user_profile_store()

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
        tools = [get_weather, get_sunset, geocode_city, retrieve_knowledge]

        # 创建 Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("system", "{user_profile}"),
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

    def _build_user_profile_prompt(self, user_id: str) -> str:
        """
        构建用户偏好提示词
        
        Args:
            user_id: 用户唯一标识
            
        Returns:
            用户偏好提示词字符串
        """
        profile = self.user_profile_store.get_profile(user_id)
        
        if not profile:
            return ""
        
        parts = []
        
        # 基础信息
        if profile.gender:
            parts.append(f"性别：{profile.gender}")
        
        if profile.age_range:
            parts.append(f"年龄范围：{profile.age_range}")
        
        if profile.height:
            parts.append(f"身高：{profile.height}")
        
        if profile.weight:
            parts.append(f"体重：{profile.weight}")
        
        if profile.preferred_cities:
            parts.append(f"常用城市：{', '.join(profile.preferred_cities)}")
        
        if profile.body_shape:
            parts.append(f"身材类型：{profile.body_shape}")
        
        if profile.preferred_styles:
            parts.append(f"风格偏好：{', '.join(profile.preferred_styles)}")
        
        if profile.color_preferences:
            parts.append(f"喜欢的色系：{', '.join(profile.color_preferences)}")
        
        if profile.color_dislikes:
            parts.append(f"回避的色系：{', '.join(profile.color_dislikes)}")
        
        # 尺码信息
        if profile.size_info:
            size_str = ", ".join([f"{k}: {v}" for k, v in profile.size_info.items()])
            parts.append(f"尺码信息：{size_str}")
        
        # 场合偏好
        if profile.workplace_dress_code:
            parts.append(f"办公着装要求：{profile.workplace_dress_code}")
        
        if profile.casual_preferences:
            parts.append(f"日常偏好：{profile.casual_preferences}")
        
        # 特殊需求
        if profile.sensitive_to_cold:
            parts.append("怕冷：是")
        
        if profile.sensitive_to_heat:
            parts.append("怕热：是")
        
        if profile.material_preferences:
            parts.append(f"材质偏好：{', '.join(profile.material_preferences)}")
        
        if profile.avoid_items:
            parts.append(f"避免单品：{', '.join(profile.avoid_items)}")
        
        # 其他偏好
        if profile.budget_range:
            parts.append(f"预算范围：{profile.budget_range}")
        
        if profile.favorite_brands:
            parts.append(f"喜欢的品牌：{', '.join(profile.favorite_brands)}")
        
        if profile.dressing_skill:
            parts.append(f"穿搭技巧：{profile.dressing_skill}")
        
        if parts:
            return f"\n用户偏好：\n" + "\n".join([f"- {p}" for p in parts])
        
        return ""

    def _extract_preferences_from_input(self, user_input: str, user_id: str):
        """
        使用 LLM 从用户输入中提取偏好信息并更新存储
        
        Args:
            user_input: 用户输入文本
            user_id: 用户唯一标识
        """
        # 构建提取偏好的提示词
        extract_prompt = f"""
你是一个用户偏好提取助手。请从以下用户输入中提取结构化的穿搭偏好信息。

用户输入: {user_input}

请按照以下格式输出 JSON，只输出 JSON，不要输出其他内容：
{{
    "gender": "性别（男/女/其他）或空字符串",
    "age_range": "年龄范围（18-25/26-35/36-45/46-55/55+）或空字符串",
    "height": "身高（如：165cm）或空字符串",
    "weight": "体重（如：55kg）或空字符串",
    "preferred_cities": ["城市1", "城市2", ...],
    "body_shape": "身材类型（梨形/苹果型/沙漏型/长方形/倒三角）或空字符串",
    "preferred_styles": ["风格1", "风格2", ...],
    "color_preferences": ["颜色1", "颜色2", ...],
    "color_dislikes": ["不喜欢的颜色1", "不喜欢的颜色2", ...],
    "material_preferences": ["材质1", "材质2", ...],
    "sensitive_to_cold": true 或 false,
    "sensitive_to_heat": true 或 false,
    "size_info": {{"上衣": "尺码", "裤子": "尺码", ...}},
    "workplace_dress_code": "办公着装要求或空字符串",
    "casual_preferences": "日常偏好描述或空字符串",
    "avoid_items": ["避免的单品1", "避免的单品2", ...],
    "budget_range": "预算范围（低/中/高/不限）或空字符串",
    "favorite_brands": ["品牌1", "品牌2", ...],
    "dressing_skill": "穿搭技巧水平（新手/进阶/高手）或空字符串"
}}

注意事项：
1. 如果没有相关信息，对应字段使用空数组 [] 或空字符串 ""
2. 城市名称使用中文（如：北京、上海）
3. 风格类型包括：日系、简约、轻熟、运动、复古、甜美、通勤、休闲、商务、街头
4. 颜色包括：黑色、白色、灰色、蓝色、红色、黄色、绿色、粉色、紫色、米色等
5. 材质包括：棉、羊毛、真丝、麻、涤纶、针织、牛仔、皮革等
6. sensitive_to_cold 只有在明确提到"怕冷"时才设为 true，否则为 false
7. sensitive_to_heat 只有在明确提到"怕热"或"容易出汗"时才设为 true，否则为 false
8. budget_range 根据用户描述判断：低（100元以下）、中（100-500元）、高（500元以上）
9. dressing_skill 根据用户描述判断：新手（不太会搭配）、进阶（有一定经验）、高手（很会搭配）
"""

        try:
            # 调用 LLM 提取偏好
            response = self.llm.invoke(extract_prompt)
            preferences_str = response.content
            
            # 解析 JSON 结果
            preferences = json.loads(preferences_str)
            
            # 过滤空值，只保留有值的字段
            updates: Dict[str, Any] = {}
            for key, value in preferences.items():
                if value:
                    updates[key] = value
            
            # 如果有更新，保存到存储
            if updates:
                self.user_profile_store.update_profile(user_id, updates)
                print(f"[偏好更新] 用户 {user_id}: {json.dumps(updates, ensure_ascii=False)}")
                
        except Exception as e:
            print(f"提取用户偏好失败: {str(e)}")
            # 降级到简单的关键词匹配
            self._extract_preferences_simple(user_input, user_id)

    def _extract_preferences_simple(self, user_input: str, user_id: str):
        """
        降级方案：使用简单的关键词匹配提取偏好（当 LLM 提取失败时使用）
        
        Args:
            user_input: 用户输入文本
            user_id: 用户唯一标识
        """
        profile = self.user_profile_store.get_profile(user_id)
        if not profile:
            profile = UserFashionProfile(user_id=user_id)
        
        updates: Dict[str, Any] = {}
        
        # 提取城市信息
        city_keywords = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "西安", "南京", "武汉"]
        found_cities = [city for city in city_keywords if city in user_input]
        if found_cities:
            cities = set(profile.preferred_cities + found_cities)
            updates["preferred_cities"] = list(cities)
        
        # 提取风格偏好
        style_keywords = ["日系", "简约", "轻熟", "运动", "复古", "甜美", "通勤", "休闲", "商务", "街头"]
        found_styles = [style for style in style_keywords if style in user_input]
        if found_styles:
            styles = set(profile.preferred_styles + found_styles)
            updates["preferred_styles"] = list(styles)
        
        # 提取颜色偏好
        color_keywords = ["黑色", "白色", "灰色", "蓝色", "红色", "黄色", "绿色", "粉色", "紫色", "米色"]
        found_colors = [color for color in color_keywords if color in user_input]
        if found_colors:
            if "不喜欢" in user_input or "讨厌" in user_input or "回避" in user_input:
                colors = set(profile.color_dislikes + found_colors)
                updates["color_dislikes"] = list(colors)
            else:
                colors = set(profile.color_preferences + found_colors)
                updates["color_preferences"] = list(colors)
        
        # 提取材质偏好
        material_keywords = ["棉", "羊毛", "真丝", "麻", "涤纶", "针织", "牛仔", "皮革"]
        found_materials = [material for material in material_keywords if material in user_input]
        if found_materials:
            materials = set(profile.material_preferences + found_materials)
            updates["material_preferences"] = list(materials)
        
        # 提取身材类型
        body_shape_keywords = ["梨形", "苹果型", "沙漏型", "长方形", "倒三角"]
        for shape in body_shape_keywords:
            if shape in user_input:
                updates["body_shape"] = shape
                break
        
        # 提取怕冷信息
        if "怕冷" in user_input or "怕冷的" in user_input:
            updates["sensitive_to_cold"] = True
        
        # 如果有更新，保存到存储
        if updates:
            self.user_profile_store.update_profile(user_id, updates)

    async def chat_stream(self, user_input: str, session_id: str = "default", user_id: str = "default_user") -> AsyncGenerator[str, None]:
        """
        逐 token 流式对话接口

        使用 AgentExecutor.astream 统一处理所有请求，让 Agent 自己决定是否调用工具。
        无论是否需要工具，都保持一致的流式输出体验。
        
        Args:
            user_input: 用户输入
            session_id: 会话ID
            user_id: 用户ID（用于偏好存储）
        """
        try:
            # 从输入中提取并更新用户偏好
            self._extract_preferences_from_input(user_input, user_id)
            
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
            
            # 获取用户偏好提示词
            user_profile_prompt = self._build_user_profile_prompt(user_id)
            print(f"user_profile: {user_profile_prompt}")
            
            full_output_parts = []
            got_output = False

            # 使用 AgentExecutor.astream 统一处理所有请求
            # Agent 会自动决定是否调用工具
            async for chunk in self.agent_executor.astream(
                {"input": full_input, "user_profile": user_profile_prompt},
                config={"configurable": {"session_id": session_id, "user_id": user_id}}
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
                result = await self.agent_executor.ainvoke(
                    {"input": full_input, "user_profile": user_profile_prompt}
                )
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

    def chat(self, user_input: str, session_id: str = "default", user_id: str = "default_user") -> str:
        """
        非流式对话接口
        
        Args:
            user_input: 用户输入
            session_id: 会话ID
            user_id: 用户ID（用于偏好存储）
            
        Returns:
            回复内容
        """
        # 从输入中提取并更新用户偏好
        self._extract_preferences_from_input(user_input, user_id)
        
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
        
        # 获取用户偏好提示词
        user_profile_prompt = self._build_user_profile_prompt(user_id)
        
        # 调用 Agent
        result = self.agent_executor.invoke(
            {"input": full_input, "user_profile": user_profile_prompt},
            config={"configurable": {"session_id": session_id, "user_id": user_id}}
        )
        
        output = result.get("output", "")
        
        # 保存对话历史
        if session_id not in SESSION_HISTORY:
            SESSION_HISTORY[session_id] = []
        SESSION_HISTORY[session_id].append({"role": "human", "content": user_input})
        SESSION_HISTORY[session_id].append({"role": "assistant", "content": output})
        SESSION_HISTORY[session_id] = SESSION_HISTORY[session_id][-20:]
        
        return output

    def get_user_profile(self, user_id: str) -> Optional[UserFashionProfile]:
        """
        获取用户画像
        
        Args:
            user_id: 用户唯一标识
            
        Returns:
            用户画像对象
        """
        return self.user_profile_store.get_profile(user_id)

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[UserFashionProfile]:
        """
        更新用户画像
        
        Args:
            user_id: 用户唯一标识
            updates: 要更新的字段
            
        Returns:
            更新后的用户画像
        """
        return self.user_profile_store.update_profile(user_id, updates)

    def clear_history(self, session_id: str):
        """
        清除会话历史
        
        Args:
            session_id: 会话ID
        """
        if session_id in SESSION_HISTORY:
            del SESSION_HISTORY[session_id]