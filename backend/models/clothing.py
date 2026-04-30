"""
穿搭建议数据模型
使用 Pydantic 定义结构化输出
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Occasion(str, Enum):
    """场合类型"""
    WORK = "工作"
    CASUAL = "休闲"
    DATE = "约会"
    SPORT = "运动"
    TRAVEL = "旅行"
    FORMAL = "正式"
    PARTY = "聚会"
    OTHER = "其他"


class Season(str, Enum):
    """季节"""
    SPRING = "春季"
    SUMMER = "夏季"
    AUTUMN = "秋季"
    WINTER = "冬季"


class ClothingItem(BaseModel):
    """单件衣物"""
    name: str = Field(description="衣物名称，例如：白色衬衫、牛仔裤")
    category: str = Field(description="类别，例如：上衣、下装、外套、鞋子、配饰")
    color: str = Field(description="颜色")
    material: Optional[str] = Field(default=None, description="材质，例如：棉、羊毛、 polyester")
    reason: Optional[str] = Field(default=None, description="推荐理由")


class ClothingAdvice(BaseModel):
    """穿搭建议（结构化输出）"""
    
    # 基础信息
    city: str = Field(description="推荐适用的城市")
    date: str = Field(description="推荐适用的日期 (YYYY-MM-DD)")
    weather_summary: str = Field(description="天气摘要，例如：晴，22°C，湿度65%")
    
    # 场合和风格
    occasion: Occasion = Field(description="适用场合")
    style: str = Field(description="风格描述，例如：简约、休闲、商务")
    
    # 穿搭详情
    tops: List[ClothingItem] = Field(default_factory=list, description="上衣推荐")
    bottoms: List[ClothingItem] = Field(default_factory=list, description="下装推荐")
    outerwear: Optional[List[ClothingItem]] = Field(default_factory=list, description="外套推荐")
    shoes: Optional[List[ClothingItem]] = Field(default_factory=list, description="鞋子推荐")
    accessories: Optional[List[ClothingItem]] = Field(default_factory=list, description="配饰推荐")
    
    # 建议和提示
    reason: str = Field(description="整体推荐理由")
    tips: Optional[str] = Field(default=None, description="温馨提示，例如：早晚温差大，建议带外套")
    color_scheme: Optional[str] = Field(default=None, description="色系搭配说明")
    
    # 温度相关
    temperature: float = Field(description="温度 (摄氏度)")
    feels_like: Optional[float] = Field(default=None, description="体感温度")
    temperature_advice: Optional[str] = Field(default=None, description="温度相关建议")
    
    class Config:
        use_enum_values = True


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(description="角色：user 或 assistant")
    content: str = Field(description="消息内容")
    timestamp: Optional[str] = Field(default=None, description="时间戳")


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(description="用户消息")
    session_id: Optional[str] = Field(default="default", description="会话ID")
    stream: Optional[bool] = Field(default=True, description="是否使用流式输出")


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str = Field(description="会话ID")
    message: str = Field(description="助手回复")
    advice: Optional[ClothingAdvice] = Field(default=None, description="结构化穿搭建议")
    tools_called: Optional[List[str]] = Field(default_factory=list, description="调用的工具列表")
