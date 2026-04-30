"""
缓存管理
支持 Redis 和内存 LRU 缓存
"""
import json
import time
from typing import Any, Optional
from datetime import datetime, timedelta
import hashlib


class MemoryCache:
    """内存 LRU 缓存（简单实现）"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = {}
        self.access_order = []
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self.cache:
            # 更新访问顺序
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]["value"]
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """设置缓存值"""
        # 检查容量
        if len(self.cache) >= self.max_size and key not in self.cache:
            # 删除最久未访问的键
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
        
        self.cache[key] = {
            "value": value,
            "expire_at": time.time() + ttl_seconds
        }
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def is_expired(self, key: str) -> bool:
        """检查是否过期"""
        if key not in self.cache:
            return True
        return time.time() > self.cache[key]["expire_at"]
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
            self.access_order.remove(key)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_order.clear()


class CacheManager:
    """缓存管理器（支持 Redis 和内存缓存）"""
    
    def __init__(self, use_redis: bool = False):
        self.use_redis = use_redis
        self.memory_cache = MemoryCache()
        self.redis_client = None
        
        if use_redis:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host="localhost",
                    port=6379,
                    db=0,
                    decode_responses=True
                )
                self.redis_client.ping()
            except Exception as e:
                print(f"Redis 连接失败，降级到内存缓存: {e}")
                self.use_redis = False
    
    def _make_key(self, *args) -> str:
        """生成缓存键"""
        key_str = ":".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_weather(self, city: str, date: str) -> Optional[dict]:
        """获取天气缓存"""
        key = f"weather:{city}:{date}"
        return self._get(key)
    
    def set_weather(self, city: str, date: str, data: dict, ttl: int = 3600):
        """设置天气缓存（TTL 1小时）"""
        key = f"weather:{city}:{date}"
        self._set(key, data, ttl)
    
    def get_sunset(self, city: str, date: str) -> Optional[dict]:
        """获取日落时间缓存"""
        key = f"sunset:{city}:{date}"
        return self._get(key)
    
    def set_sunset(self, city: str, date: str, data: dict, ttl: int = 86400):
        """设置日落时间缓存（TTL 24小时）"""
        key = f"sunset:{city}:{date}"
        self._set(key, data, ttl)
    
    def _get(self, key: str) -> Optional[Any]:
        """获取缓存（内部方法）"""
        if self.use_redis and self.redis_client:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
        else:
            if not self.memory_cache.is_expired(key):
                return self.memory_cache.get(key)
        return None
    
    def _set(self, key: str, value: Any, ttl: int):
        """设置缓存（内部方法）"""
        if self.use_redis and self.redis_client:
            self.redis_client.setex(key, ttl, json.dumps(value))
        else:
            self.memory_cache.set(key, value, ttl)
    
    def clear_all(self):
        """清空所有缓存"""
        if self.use_redis and self.redis_client:
            self.redis_client.flushdb()
        else:
            self.memory_cache.clear()
