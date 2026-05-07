"""
天气查询工具 - 使用 Open-Meteo 免费 API（无需 API Key）
支持缓存管理，避免重复查询
"""
from langchain.tools import tool
from pydantic import BaseModel, Field
import httpx
import json
from datetime import datetime, timedelta
from typing import Optional

# 导入地理编码工具
from tools.geocoding_tool import _geocode_city_impl
# 导入缓存管理器和日志
from utils.cache import CacheManager
from utils.logger import get_logger

# 初始化缓存管理器和日志
cache_manager = CacheManager()
logger = get_logger(__name__)

# Open-Meteo 免费 API（无需注册，无需 API Key）
# 官方文档：https://open-meteo.com/en/docs
BASE_URL = "https://api.open-meteo.com/v1/forecast"

# WMO 天气代码映射表
WMO_WEATHER_CODES = {
    0: "晴天",
    1: "大部晴朗",
    2: "多云",
    3: "阴天",
    45: "有雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "中毛毛雨",
    55: "大毛毛雨",
    56: "冻毛毛雨",
    57: "冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻小雨",
    67: "冻大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "小阵雨",
    81: "中阵雨",
    82: "大阵雨",
    85: "小阵雪",
    86: "大阵雪",
    95: "雷暴",
    96: "雷暴伴小冰雹",
    99: "雷暴伴大冰雹",
}


class WeatherInput(BaseModel):
    """天气查询输入参数"""
    city: str = Field(description="城市名称，例如：北京、上海、广州、London")
    date: str = Field(default="today", description="日期，格式：YYYY-MM-DD 或 today/tomorrow")
    latitude: Optional[float] = Field(default=None, description="纬度（可选，如不提供则自动查询）")
    longitude: Optional[float] = Field(default=None, description="经度（可选，如不提供则自动查询）")


@tool
def get_weather(city: str, date: str = "today", latitude: float = None, longitude: float = None) -> str:
    """
    获取指定城市的天气信息（使用 Open-Meteo 免费 API，无需 API Key）
    
    Args:
        city: 城市名称（中文或英文）
        date: 日期（YYYY-MM-DD 或 today/tomorrow）
        latitude: 纬度（可选，内部会自动查询）
        longitude: 经度（可选，内部会自动查询）
    
    Returns:
        天气信息字符串，包含温度、湿度、降水、风力等
    """
    try:
        # 处理日期：将 today/tomorrow 转换为实际日期
        if date == "today":
            target_date = datetime.now().strftime("%Y-%m-%d")
        elif date == "tomorrow":
            target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            target_date = date

        # ===== 检查缓存 =====
        cached_data = cache_manager.get_weather(city, target_date)
        if cached_data:
            logger.info(f"[缓存命中] 天气查询 - 城市: {city}, 日期: {target_date}")
            return json.dumps(cached_data, ensure_ascii=False, indent=2)
        
        logger.info(f"[缓存未命中] 天气查询 - 城市: {city}, 日期: {target_date}，正在调用 API...")

        # 如果没有提供经纬度，先查询城市坐标
        if latitude is None or longitude is None:
            geo_result = _geocode_city_impl(city)
            if "error" not in geo_result:
                latitude = geo_result.get("latitude")
                longitude = geo_result.get("longitude")
            else:
                return f"无法找到城市「{city}」，请检查城市名称是否正确。"

        if latitude is None or longitude is None:
            return f"无法获取城市「{city}」的坐标信息。"

        # 调用 Open-Meteo API（当前天气 + 今日预报）
        # hourly 参数：获取今日每小时温度，用于更准确地判断天气
        # current 参数：当前实时天气
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m",
                "surface_pressure"
            ],
            "timezone": "auto",
            "forecast_days": 1
        }

        response = httpx.get(BASE_URL, params=params, timeout=15.0)

        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})

            # 解析天气代码
            weather_code = current.get("weather_code", 0)
            weather_desc = WMO_WEATHER_CODES.get(weather_code, f"未知天气(code:{weather_code})")

            # 风向转换
            wind_deg = current.get("wind_direction_10m", 0)
            wind_dir = _degrees_to_direction(wind_deg)

            result = {
                "city": city,
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "timezone": data.get("timezone"),
                "date": target_date,
                "temperature": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "weather": weather_desc,
                "weather_code": weather_code,
                "precipitation": current.get("precipitation", 0),
                "wind_speed": current.get("wind_speed_10m"),
                "wind_direction": wind_dir,
                "wind_deg": wind_deg,
                "pressure": current.get("surface_pressure"),
                "data_source": "Open-Meteo (免费API)",
                "note": "数据更新频率：当前天气约每 15 分钟更新一次"
            }
            
            # ===== 存入缓存 =====
            # 天气缓存 1 小时（3600 秒）
            cache_manager.set_weather(city, target_date, result, ttl=3600)
            logger.info(f"[缓存已存储] 天气查询 - 城市: {city}, 日期: {target_date}")
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            return f"获取天气信息失败: HTTP {response.status_code} - {response.text[:200]}"

    except httpx.TimeoutException:
        return "获取天气信息超时，请检查网络连接后重试。"
    except Exception as e:
        return f"获取天气信息时出错: {str(e)}"


def _degrees_to_direction(degrees: float) -> str:
    """将风向角度转换为方位描述"""
    directions = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
    idx = round(degrees / 45) % 8
    return directions[idx]
