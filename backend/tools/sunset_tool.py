"""
日落时间查询工具 - 使用 Open-Meteo 免费 API（无需 API Key）
支持缓存管理，避免重复查询
"""
from langchain.tools import tool
from pydantic import BaseModel, Field
import httpx
import json
from datetime import datetime, timedelta
from typing import Optional

# 导入缓存管理器和日志
from utils.cache import CacheManager
from utils.logger import get_logger

# 初始化缓存管理器和日志
cache_manager = CacheManager()
logger = get_logger(__name__)


class SunsetInput(BaseModel):
    """日落时间查询输入参数"""
    city: str = Field(description="城市名称，例如：北京、上海、广州、London")
    date: str = Field(default="today", description="日期，格式：YYYY-MM-DD 或 today/tomorrow")
    latitude: Optional[float] = Field(default=None, description="纬度（可选，如不提供则自动查询）")
    longitude: Optional[float] = Field(default=None, description="经度（可选，如不提供则自动查询）")


@tool
def get_sunset(city: str, date: str = "today", latitude: float = None, longitude: float = None) -> str:
    """
    获取指定城市的日出和日落时间（使用 Open-Meteo 免费 API）
    
    Args:
        city: 城市名称（中文或英文）
        date: 日期（YYYY-MM-DD 或 today/tomorrow）
        latitude: 纬度（可选，内部会自动查询）
        longitude: 经度（可选，内部会自动查询）
    
    Returns:
        包含日出日落时间的 JSON 字符串（本地时间）
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
        cached_data = cache_manager.get_sunset(city, target_date)
        if cached_data:
            logger.info(f"[缓存命中] 日落查询 - 城市: {city}, 日期: {target_date}")
            return json.dumps(cached_data, ensure_ascii=False, indent=2)
        
        logger.info(f"[缓存未命中] 日落查询 - 城市: {city}, 日期: {target_date}，正在调用 API...")

        # 如果没有提供经纬度，先查询城市坐标
        if latitude is None or longitude is None:
            from tools.geocoding_tool import geocode_city
            geo_result = geocode_city(city)
            try:
                geo_data = json.loads(geo_result)
                if geo_data.get("error"):
                    return json.dumps({
                        "error": True,
                        "message": geo_data.get("message", f"无法找到城市「{city}」")
                    }, ensure_ascii=False)
                latitude = geo_data.get("latitude")
                longitude = geo_data.get("longitude")
            except Exception:
                return json.dumps({
                    "error": True,
                    "message": f"查询城市「{city}」坐标失败"
                }, ensure_ascii=False)

        if latitude is None or longitude is None:
            return json.dumps({
                "error": True,
                "message": f"无法获取城市「{city}」的坐标信息"
            }, ensure_ascii=False)

        # 调用 Open-Meteo API 获取日出日落时间
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": ["sunrise", "sunset"],
            "timezone": "auto",
            "forecast_days": 2  # 获取今天和明天
        }

        response = httpx.get(url, params=params, timeout=15.0)

        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            sunrise_times = daily.get("sunrise", [])
            sunset_times = daily.get("sunset", [])

            # 找到目标日期的索引
            daily_dates = daily.get("time", [])
            target_idx = -1
            for i, d in enumerate(daily_dates):
                if d == target_date:
                    target_idx = i
                    break

            if target_idx >= 0 and target_idx < len(sunrise_times):
                sunrise_iso = sunrise_times[target_idx]
                sunset_iso = sunset_times[target_idx]

                # 提取 HH:MM 格式的时间
                sunrise_time = sunrise_iso.split("T")[1][:5] if "T" in sunrise_iso else sunrise_iso
                sunset_time = sunset_iso.split("T")[1][:5] if "T" in sunset_iso else sunset_iso

                # 计算白天时长
                try:
                    sr = datetime.strptime(sunrise_iso, "%Y-%m-%dT%H:%M")
                    ss = datetime.strptime(sunset_iso, "%Y-%m-%dT%H:%M")
                    day_seconds = (ss - sr).total_seconds()
                    day_hours = int(day_seconds // 3600)
                    day_minutes = int((day_seconds % 3600) // 60)
                    day_length = f"{day_hours}小时{day_minutes}分钟"
                except Exception:
                    day_length = "未知"

                result = {
                    "city": city,
                    "date": target_date,
                    "sunrise": sunrise_time,
                    "sunset": sunset_time,
                    "day_length": day_length,
                    "timezone": data.get("timezone", ""),
                    "note": "时间均为当地时区时间"
                }
                
                # ===== 存入缓存 =====
                # 日落时间缓存 24 小时（86400 秒）
                cache_manager.set_sunset(city, target_date, result, ttl=86400)
                logger.info(f"[缓存已存储] 日落查询 - 城市: {city}, 日期: {target_date}")
                
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return json.dumps({
                    "error": True,
                    "message": f"未找到日期 {target_date} 的日出日落数据"
                }, ensure_ascii=False)
        else:
            return json.dumps({
                "error": True,
                "message": f"获取日出日落时间失败: HTTP {response.status_code}"
            }, ensure_ascii=False)

    except httpx.TimeoutException:
        return json.dumps({
            "error": True,
            "message": "获取日出日落时间超时，请检查网络连接后重试。"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": True,
            "message": f"获取日落时间时出错: {str(e)}"
        }, ensure_ascii=False)
