"""
地理编码工具 - 使用 Open-Meteo 免费地理编码 API（无需 API Key）
支持中/英文城市名，并通过多种策略提高匹配准确度。
"""
from langchain.tools import tool
from pydantic import BaseModel, Field
import httpx
import json
from typing import Optional


class GeocodeInput(BaseModel):
    """地理编码输入参数"""
    city: str = Field(description="城市名称，例如：北京、上海、London、New York")


# 中国主要城市坐标映射表（备用，提高准确率）
CHINA_CITY_COORDS = {
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644),
    "深圳": (22.5431, 114.0579),
    "杭州": (30.2741, 120.1551),
    "南京": (32.0603, 118.7969),
    "成都": (30.5728, 104.0668),
    "重庆": (29.4316, 106.9123),
    "武汉": (30.5928, 114.3055),
    "西安": (34.3416, 108.9398),
    "天津": (39.3434, 117.3616),
    "苏州": (31.2990, 120.5853),
    "厦门": (24.4798, 118.0894),
    "大连": (38.9140, 121.6147),
    "青岛": (36.0671, 120.3826),
    "昆明": (25.0389, 102.7183),
    "长沙": (28.2282, 112.9388),
    "郑州": (34.7466, 113.6254),
    "沈阳": (41.8057, 123.4315),
    "哈尔滨": (45.8038, 126.5340),
    "长春": (43.8171, 125.3235),
    "济南": (36.6512, 116.9972),
    "福州": (26.0745, 119.2965),
    "合肥": (31.8206, 117.2272),
    "南昌": (28.6820, 115.8579),
    "贵阳": (26.6470, 106.6302),
    "南宁": (22.8170, 108.3665),
    "海口": (20.0174, 110.3492),
    "兰州": (36.0611, 103.8343),
    "银川": (38.4872, 106.2309),
    "西宁": (36.6171, 101.7782),
    "乌鲁木齐": (43.8256, 87.6168),
    "拉萨": (29.6500, 91.1000),
    "呼和浩特": (40.8414, 111.7519),
    "石家庄": (38.0428, 114.5149),
    "太原": (37.8706, 112.5489),
    "昆明": (25.0389, 102.7183),
}

# 检测是否为中文字符
def _contains_chinese(text: str) -> bool:
    return any('\u4e00' <= ch <= '\u9fff' for ch in text)


@tool
def geocode_city(city: str) -> str:
    """
    将城市名称转换为经纬度坐标（使用 Open-Meteo 免费地理编码 API）
    
    Args:
        city: 城市名称（支持中文、英文等多种语言）
    
    Returns:
        包含经纬度信息的 JSON 字符串
    """
    try:
        # 优先使用内置坐标表（对中国城市准确率更高）
        if city in CHINA_CITY_COORDS:
            lat, lon = CHINA_CITY_COORDS[city]
            result = {
                "city": city,
                "matched_name": city,
                "latitude": lat,
                "longitude": lon,
                "country": "中国",
                "data_source": "内置坐标库（中国主要城市）"
            }
            return json.dumps(result, ensure_ascii=False, indent=2)

        # 使用 Open-Meteo Geocoding API（免费，无需 API Key）
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": city,
            "count": 5,           # 取前5个结果，选择最佳匹配
            "language": "zh",
            "format": "json"
        }

        # 对中文查询附加中国过滤，提升准确率
        if _contains_chinese(city):
            params["country"] = "CN"

        response = httpx.get(url, params=params, timeout=10.0)

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])

            if results and len(results) > 0:
                # 智能选择最佳结果
                r = results[0]
                # 如果输入是中文但结果不在国内，尝试找国内的结果
                if _contains_chinese(city):
                    for candidate in results:
                        if candidate.get("country") == "中国" or candidate.get("country_code", "").upper() == "CN":
                            r = candidate
                            break

                result = {
                    "city": city,
                    "matched_name": r.get("name", city),
                    "latitude": float(r.get("latitude")),
                    "longitude": float(r.get("longitude")),
                    "country": r.get("country", ""),
                    "admin1": r.get("admin1", ""),
                    "timezone": r.get("timezone", ""),
                    "population": r.get("population"),
                    "data_source": "Open-Meteo Geocoding API (免费)"
                }
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                # 回退：尝试用英文再查一次
                params2 = {
                    "name": city,
                    "count": 1,
                    "language": "en",
                    "format": "json"
                }
                response2 = httpx.get(url, params=params2, timeout=10.0)
                if response2.status_code == 200:
                    data2 = response2.json()
                    results2 = data2.get("results", [])
                    if results2 and len(results2) > 0:
                        r = results2[0]
                        result = {
                            "city": city,
                            "matched_name": r.get("name", city),
                            "latitude": float(r.get("latitude")),
                            "longitude": float(r.get("longitude")),
                            "country": r.get("country", ""),
                            "admin1": r.get("admin1", ""),
                            "data_source": "Open-Meteo Geocoding API (英文回退)"
                        }
                        return json.dumps(result, ensure_ascii=False, indent=2)

                return json.dumps({
                    "error": True,
                    "message": f"未找到城市「{city}」，请检查名称是否正确，或尝试使用英文名称。"
                }, ensure_ascii=False)
        else:
            return json.dumps({
                "error": True,
                "message": f"地理编码查询失败: HTTP {response.status_code}"
            }, ensure_ascii=False)

    except httpx.TimeoutException:
        return json.dumps({
            "error": True,
            "message": "地理编码查询超时，请检查网络连接后重试。"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": True,
            "message": f"地理编码时出错: {str(e)}"
        }, ensure_ascii=False)


@tool
def get_coordinates(city: str) -> dict:
    """
    获取城市的经纬度坐标（返回字典格式，供内部调用）
    
    Args:
        city: 城市名称
    
    Returns:
        包含 latitude 和 longitude 的字典；若查询失败则返回默认值（北京）
    """
    # 优先使用内置坐标表
    if city in CHINA_CITY_COORDS:
        lat, lon = CHINA_CITY_COORDS[city]
        return {"latitude": lat, "longitude": lon}

    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": city,
            "count": 1,
            "language": "zh"
        }
        if _contains_chinese(city):
            params["country"] = "CN"

        response = httpx.get(url, params=params, timeout=10.0)

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results and len(results) > 0:
                r = results[0]
                return {
                    "latitude": float(r.get("latitude")),
                    "longitude": float(r.get("longitude"))
                }

        # 查询失败，返回默认值（北京）
        print(f"[get_coordinates] 未找到城市「{city}」，使用默认坐标（北京）")
        return {"latitude": 39.9042, "longitude": 116.4074}

    except Exception as e:
        print(f"[get_coordinates] 查询失败: {e}，使用默认坐标（北京）")
        return {"latitude": 39.9042, "longitude": 116.4074}
