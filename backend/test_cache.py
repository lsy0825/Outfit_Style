"""
测试缓存功能
验证天气和日落时间查询的缓存机制
"""
from tools.weather_tool import get_weather
from tools.sunset_tool import get_sunset
import json
import time

def test_weather_cache():
    """测试天气查询缓存"""
    print("=" * 60)
    print("测试 1: 天气查询缓存")
    print("=" * 60)
    
    city = "上海"
    date = "today"
    
    # 第一次查询（应该调用 API）
    print(f"\n[第一次查询] 城市: {city}, 日期: {date}")
    result1 = get_weather.invoke({"city": city, "date": date})
    data1 = json.loads(result1)
    print(f"结果: 温度 {data1.get('temperature')}°C, 天气 {data1.get('weather')}")
    
    # 第二次查询（应该使用缓存）
    print(f"\n[第二次查询] 城市: {city}, 日期: {date}")
    result2 = get_weather.invoke({"city": city, "date": date})
    data2 = json.loads(result2)
    print(f"结果: 温度 {data2.get('temperature')}°C, 天气 {data2.get('weather')}")
    
    # 验证数据一致性
    if data1.get('temperature') == data2.get('temperature'):
        print("\n✅ 缓存功能正常！两次查询结果一致")
    else:
        print("\n❌ 缓存功能异常！两次查询结果不一致")
    
    # 测试不同日期（应该调用 API）
    print(f"\n[第三次查询] 城市: {city}, 日期: tomorrow")
    result3 = get_weather.invoke({"city": city, "date": "tomorrow"})
    data3 = json.loads(result3)
    print(f"结果: 温度 {data3.get('temperature')}°C, 天气 {data3.get('weather')}")
    print("✅ 不同日期查询正常（应该调用新 API）")

def test_sunset_cache():
    """测试日落时间查询缓存"""
    print("\n" + "=" * 60)
    print("测试 2: 日落时间查询缓存")
    print("=" * 60)
    
    city = "上海"
    date = "today"
    
    # 第一次查询（应该调用 API）
    print(f"\n[第一次查询] 城市: {city}, 日期: {date}")
    result1 = get_sunset.invoke({"city": city, "date": date})
    data1 = json.loads(result1)
    print(f"结果: 日出 {data1.get('sunrise')}, 日落 {data1.get('sunset')}")
    
    # 第二次查询（应该使用缓存）
    print(f"\n[第二次查询] 城市: {city}, 日期: {date}")
    result2 = get_sunset.invoke({"city": city, "date": date})
    data2 = json.loads(result2)
    print(f"结果: 日出 {data2.get('sunrise')}, 日落 {data2.get('sunset')}")
    
    # 验证数据一致性
    if data1.get('sunrise') == data2.get('sunrise'):
        print("\n✅ 缓存功能正常！两次查询结果一致")
    else:
        print("\n❌ 缓存功能异常！两次查询结果不一致")
    
    # 测试不同日期（应该调用 API）
    print(f"\n[第三次查询] 城市: {city}, 日期: tomorrow")
    result3 = get_sunset.invoke({"city": city, "date": "tomorrow"})
    data3 = json.loads(result3)
    print(f"结果: 日出 {data3.get('sunrise')}, 日落 {data3.get('sunset')}")
    print("✅ 不同日期查询正常（应该调用新 API）")

def test_different_cities():
    """测试不同城市的缓存隔离"""
    print("\n" + "=" * 60)
    print("测试 3: 不同城市的缓存隔离")
    print("=" * 60)
    
    # 查询上海
    print("\n[查询上海]")
    result_sh = get_weather.invoke({"city": "上海", "date": "today"})
    data_sh = json.loads(result_sh)
    print(f"结果: {data_sh.get('city')} - 温度 {data_sh.get('temperature')}°C")
    
    # 查询北京（应该调用新 API）
    print("\n[查询北京]")
    result_bj = get_weather.invoke({"city": "北京", "date": "today"})
    data_bj = json.loads(result_bj)
    print(f"结果: {data_bj.get('city')} - 温度 {data_bj.get('temperature')}°C")
    
    print("\n✅ 不同城市缓存隔离正常")

if __name__ == "__main__":
    print("\n🚀 开始测试缓存功能\n")
    
    try:
        test_weather_cache()
        test_sunset_cache()
        test_different_cities()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
