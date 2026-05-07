"""
用户偏好存储管理器
使用 SQLite 实现持久化存储，支持跨会话复用
"""
import os
import json
import sqlite3
from typing import Optional, Dict, Any, List

from models.clothing import UserFashionProfile


class UserProfileStore:
    """用户偏好存储管理器"""
    
    def __init__(self, db_path: str = "./user_profiles.db"):
        """
        初始化存储管理器
        
        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_directory_exists()
        self._init_database()
        
        # 内存缓存，避免频繁查询数据库
        self._memory_cache: Dict[str, UserFashionProfile] = {}
    
    def _ensure_directory_exists(self):
        """确保数据库目录存在"""
        dir_path = os.path.dirname(self.db_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
    
    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 创建用户画像表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def get_profile(self, user_id: str) -> Optional[UserFashionProfile]:
        """
        获取用户画像
        
        Args:
            user_id: 用户唯一标识
            
        Returns:
            UserFashionProfile 对象，不存在返回 None
        """
        # 先检查内存缓存
        if user_id in self._memory_cache:
            return self._memory_cache[user_id]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT profile_data FROM user_profiles WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    profile_data = json.loads(row['profile_data'])
                    profile = UserFashionProfile.from_dict(profile_data)
                    self._memory_cache[user_id] = profile
                    return profile
            
            return None
            
        except Exception as e:
            print(f"获取用户画像失败: {str(e)}")
            return None
    
    def save_profile(self, user_id: str, profile: UserFashionProfile) -> bool:
        """
        保存用户画像
        
        Args:
            user_id: 用户唯一标识
            profile: 用户画像对象
            
        Returns:
            是否保存成功
        """
        try:
            # 更新内存缓存
            self._memory_cache[user_id] = profile
            
            # 序列化用户画像
            profile_data = json.dumps(profile.to_dict(), ensure_ascii=False)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 使用 INSERT OR REPLACE 实现 upsert
                cursor.execute('''
                    INSERT OR REPLACE INTO user_profiles (user_id, profile_data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, profile_data))
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"保存用户画像失败: {str(e)}")
            return False
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[UserFashionProfile]:
        """
        更新用户画像（部分字段更新）
        
        Args:
            user_id: 用户唯一标识
            updates: 要更新的字段字典
            
        Returns:
            更新后的 UserFashionProfile 对象，不存在返回 None
        """
        # 获取现有画像
        profile = self.get_profile(user_id)
        
        if not profile:
            # 如果不存在，创建新画像
            profile = UserFashionProfile(user_id=user_id)
        
        # 应用更新（仅更新非 None 值）
        for key, value in updates.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)
        
        # 保存更新
        if self.save_profile(user_id, profile):
            return profile
        
        return None
    
    def delete_profile(self, user_id: str) -> bool:
        """
        删除用户画像
        
        Args:
            user_id: 用户唯一标识
            
        Returns:
            是否删除成功
        """
        try:
            # 从内存缓存删除
            if user_id in self._memory_cache:
                del self._memory_cache[user_id]
            
            # 从数据库删除
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM user_profiles WHERE user_id = ?', (user_id,))
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"删除用户画像失败: {str(e)}")
            return False
    
    def list_users(self) -> List[str]:
        """
        获取所有用户ID列表
        
        Returns:
            用户ID列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT user_id FROM user_profiles')
                rows = cursor.fetchall()
                
                return [row['user_id'] for row in rows]
            
        except Exception as e:
            print(f"获取用户列表失败: {str(e)}")
            return []
    
    def get_collection_stats(self) -> dict:
        """
        获取集合统计信息
        
        Returns:
            统计信息字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as count FROM user_profiles')
                row = cursor.fetchone()
                
                return {
                    "document_count": row[0],
                    "persist_directory": os.path.dirname(self.db_path) or "."
                }
            
        except Exception as e:
            return {"error": str(e)}
    
    def clear_cache(self):
        """清空内存缓存（用于测试或内存管理）"""
        self._memory_cache.clear()


# 全局单例存储管理器
_user_profile_store = None


def get_user_profile_store() -> UserProfileStore:
    """获取用户偏好存储管理器（单例）"""
    global _user_profile_store
    
    if _user_profile_store is None:
        _user_profile_store = UserProfileStore()
    
    return _user_profile_store