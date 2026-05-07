"""
穿搭建议数据模型
使用 Pydantic 定义结构化输出
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum


class UserFashionProfile(BaseModel):
    """用户穿搭画像"""
    
    user_id: str = Field(description="用户唯一标识")
    
    # 基础信息
    gender: str = Field(default="", description="性别：男/女/其他")
    age_range: str = Field(default="", description="年龄范围：18-25/26-35/36-45/46-55/55+")
    height: str = Field(default="", description="身高，如：165cm")
    weight: str = Field(default="", description="体重，如：55kg")
    
    # 穿搭相关
    preferred_cities: List[str] = Field(default_factory=list, description="常用城市（用于天气穿搭）")
    body_shape: str = Field(default="", description="身材类型：梨形/苹果型/沙漏型/长方形/倒三角")
    preferred_styles: List[str] = Field(default_factory=list, description="风格偏好：日系/简约/轻熟/运动等")
    color_preferences: List[str] = Field(default_factory=list, description="喜欢的色系")
    color_dislikes: List[str] = Field(default_factory=list, description="回避的色系")
    
    # 尺码信息（设计为动态覆盖）
    size_info: Dict[str, str] = Field(default_factory=dict, description="尺码信息，如 {'上衣': 'M', '裤子': '28码', '鞋子': '38'}")
    
    # 场合偏好
    workplace_dress_code: str = Field(default="自由", description="办公着装要求：商务/商务休闲/自由")
    casual_preferences: str = Field(default="", description="日常偏好描述")
    
    # 特殊需求
    sensitive_to_cold: bool = Field(default=False, description="是否怕冷")
    sensitive_to_heat: bool = Field(default=False, description="是否怕热")
    material_preferences: List[str] = Field(default_factory=list, description="材质偏好：棉/羊毛/真丝等")
    avoid_items: List[str] = Field(default_factory=list, description="不喜欢的单品：高领/紧身裤等")
    
    # 其他偏好
    budget_range: str = Field(default="", description="预算范围：低/中/高/不限")
    favorite_brands: List[str] = Field(default_factory=list, description="喜欢的品牌")
    dressing_skill: str = Field(default="", description="穿搭技巧水平：新手/进阶/高手")
    
    def to_dict(self) -> dict:
        """转换为字典用于存储"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "UserFashionProfile":
        """从字典创建对象"""
        return cls(**data)


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
