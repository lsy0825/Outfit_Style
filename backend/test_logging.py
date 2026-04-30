"""
验证日志输出 - 测试在 uvicorn 环境下日志是否正常
"""
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import setup_logging, get_logger

# 配置日志
setup_logging(level="info", log_file=True, log_console=True)

logger = get_logger(__name__)

print("=" * 60)
print("测试日志输出")
print("=" * 60)

# 测试不同级别的日志
logger.debug("这是 DEBUG 日志（默认不显示，因为级别是 INFO）")
logger.info("这是 INFO 日志 ✅ 你应该能看到这条")
logger.warning("这是 WARNING 日志 ⚠️")
logger.error("这是 ERROR 日志 ❌")

print("\n" + "=" * 60)
print("测试缓存功能中的日志")
print("=" * 60)

# 测试工具中的日志
from tools.weather_tool import get_weather
from tools.sunset_tool import get_sunset

print("\n>>> 第一次查询天气（应该显示：[缓存未命中]）")
result1 = get_weather.invoke({"city": "上海", "date": "today"})

print("\n>>> 第二次查询天气（应该显示：[缓存命中]）")
result2 = get_weather.invoke({"city": "上海", "date": "today"})

print("\n" + "=" * 60)
print("✅ 测试完成")
print("=" * 60)
print("\n📝 日志文件位置：backend/logs/stylemate_2026-04-30.log")
print("📺 如果终端看不到日志，请尝试：")
print("   1. 确保使用 python start.py 启动服务")
print("   2. 或者在 main.py 所在目录运行：python -m uvicorn main:app --reload --log-level info")
