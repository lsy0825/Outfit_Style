"""
StyleMate Agent - 穿搭推荐核心 Agent
使用 LangChain + qwen3-max 实现

关键功能：
- 非流式对话接口，返回文本和图片
- 文生图功能（使用 wanx-v1）
- 用户偏好存储：使用 SQLite 实现跨会话复用
"""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import json
import requests

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
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model="qwen3-max",
            api_key="sk-9ab6aa9d33cb4596813f1caeeede0903",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            temperature=0.7,
            streaming=False
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

    def _generate_images(self, prompt: str, num_images: int = 3) -> List[str]:
        """
        使用 wanx-v1 文生图模型生成图片
        
        Args:
            prompt: 图片描述提示词
            num_images: 生成图片数量
            
        Returns:
            图片 URL 列表
        """
        try:
            import dashscope
            from dashscope import ImageSynthesis
            import os
            import uuid
            
            dashscope.api_key = "sk-9ab6aa9d33cb4596813f1caeeede0903"
            
            # 创建静态图片目录
            static_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'images')
            os.makedirs(static_dir, exist_ok=True)
            
            image_urls = []
            
            for i in range(num_images):
                print(f"文生图请求 - 模型: wanx-v1")
                print(f"文生图请求 - 提示词长度: {len(prompt)}")
                print(f"文生图请求 - 提示词预览: {prompt[:100]}...")
                
                # 设置轮询参数，减少日志输出
                result = ImageSynthesis.call(
                    model="wanx-v1",
                    prompt=prompt,
                    size="768*1152",
                    seed=i + 42,
                    # 设置轮询参数
                    max_wait_time=120,  # 最大等待时间
                    interval=5  # 轮询间隔（秒）
                )
                
                print(f"文生图响应: {result}")
                
                if hasattr(result, 'output') and result.output is not None:
                    output = result.output
                    if hasattr(output, 'results') and output.results:
                        for res in output.results:
                            if hasattr(res, 'url') and res.url:
                                print(f"生成图片 {i+1}: {res.url}")
                                # 下载图片到本地
                                local_path = self._download_image(res.url, static_dir)
                                if local_path:
                                    # 返回可访问的URL路径
                                    image_urls.append(f"/static/images/{os.path.basename(local_path)}")
                                    print(f"图片 {i+1} 已保存: {local_path}")
                                break
                    elif hasattr(output, 'url') and output.url:
                        print(f"生成图片 {i+1}: {output.url}")
                        local_path = self._download_image(output.url, static_dir)
                        if local_path:
                            image_urls.append(f"/static/images/{os.path.basename(local_path)}")
                            print(f"图片 {i+1} 已保存: {local_path}")
            
            print(f"文生图完成，共生成 {len(image_urls)} 张图片")
            return image_urls
            
        except Exception as e:
            print(f"文生图异常: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _download_image(self, url: str, save_dir: str) -> str:
        """
        下载图片到本地目录
        
        Args:
            url: 图片URL
            save_dir: 保存目录
            
        Returns:
            本地文件路径或空字符串
        """
        try:
            import uuid
            # 生成唯一文件名
            filename = f"{uuid.uuid4()}.png"
            filepath = os.path.join(save_dir, filename)
            
            # 下载图片
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 保存图片
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return filepath
            
        except Exception as e:
            print(f"下载图片失败: {str(e)}")
            return ""

    def _build_image_prompt(self, output: str, advice: Optional[dict] = None) -> str:
        """
        根据对话输出构建文生图提示词
        
        Args:
            output: 对话输出文本
            advice: 结构化穿搭建议
            
        Returns:
            图片生成提示词
        """
        if advice:
            # 使用结构化建议构建更精确的提示词
            style = advice.get("style", "时尚")
            occasion = advice.get("occasion", "日常")
            
            clothing_items = []
            if advice.get("tops"):
                for item in advice["tops"]:
                    clothing_items.append(f"{item.get('color', '')}{item.get('name', '')}")
            if advice.get("bottoms"):
                for item in advice["bottoms"]:
                    clothing_items.append(f"{item.get('color', '')}{item.get('name', '')}")
            if advice.get("outerwear"):
                for item in advice["outerwear"]:
                    clothing_items.append(f"{item.get('color', '')}{item.get('name', '')}")
            
            clothing_str = ", ".join(clothing_items)
            
            return f"时尚穿搭，{style}风格，适合{occasion}场合，穿着{clothing_str}的年轻女性，全身照，高清，时尚杂志风格"
        else:
            # 使用对话文本生成提示词
            return f"时尚穿搭建议，{output[:100]}，高清，时尚风格，全身人像"

    def _extract_structured_advice(self, output: str) -> Optional[dict]:
        """
        尝试从 LLM 输出中提取结构化穿搭建议
        
        Args:
            output: LLM 输出文本
            
        Returns:
            结构化建议字典或 None
        """
        try:
            # 尝试查找 JSON 格式的建议
            if "```json" in output:
                json_start = output.find("```json") + 7
                json_end = output.find("```", json_start)
                if json_end != -1:
                    json_str = output[json_start:json_end].strip()
                    return json.loads(json_str)
            
            # 尝试查找普通 JSON
            if "{" in output and "}" in output:
                json_start = output.find("{")
                json_end = output.rfind("}") + 1
                json_str = output[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"解析结构化建议失败: {str(e)}")
        
        return None

    def chat(self, user_input: str, session_id: str = "default", user_id: str = "default_user") -> Dict[str, Any]:
        """
        非流式对话接口
        
        Args:
            user_input: 用户输入
            session_id: 会话ID
            user_id: 用户ID（用于偏好存储）
            
        Returns:
            包含 message, images, advice 的字典
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
        
        # 尝试提取结构化建议
        advice = self._extract_structured_advice(output)
        
        # 生成图片（如果有穿搭建议）
        images = []
        if advice or "穿搭" in output or "衣服" in output or "搭配" in output:
            image_prompt = self._build_image_prompt(output, advice)
            images = self._generate_images(image_prompt, num_images=3)
        
        # 保存对话历史
        if session_id not in SESSION_HISTORY:
            SESSION_HISTORY[session_id] = []
        SESSION_HISTORY[session_id].append({"role": "human", "content": user_input})
        SESSION_HISTORY[session_id].append({
            "role": "assistant", 
            "content": output,
            "images": images,
            "advice": advice
        })
        SESSION_HISTORY[session_id] = SESSION_HISTORY[session_id][-20:]
        
        return {
            "message": output,
            "images": images,
            "advice": advice
        }

    def get_session_history(self, session_id: str) -> List[Dict]:
        """
        获取会话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            消息列表
        """
        return SESSION_HISTORY.get(session_id, [])

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
