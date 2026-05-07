"""
RAG 检索工具
LangChain Tool 包装，供 Agent 使用
"""
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import List, Optional
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vector_store import VectorStoreManager
from document_loader import DocumentLoader

# 全局向量存储管理器（单例模式）
_vector_store_manager = None

def get_vector_store_manager() -> VectorStoreManager:
    """获取向量存储管理器（单例）"""
    global _vector_store_manager
    
    if _vector_store_manager is None:
        _vector_store_manager = VectorStoreManager(
            persist_directory="./chroma_db",
            collection_name="stylemate_knowledge"
        )
    
    return _vector_store_manager


class RetrieveInput(BaseModel):
    """检索输入参数"""
    query: str = Field(description="检索查询文本，例如：穿搭原则、颜色搭配技巧、场合适配等")
    k: int = Field(default=3, description="返回的相关文档块数量（默认 3）")


@tool
def retrieve_knowledge(query: str, k: int = 3) -> str:
    """
    从知识库中检索相关穿搭知识
    
    使用场景：
    - 用户询问穿搭原则、技巧、建议时
    - 用户询问颜色搭配、场合适配等问题时
    - 需要参考专业知识库来回答时
    
    Args:
        query: 检索查询文本
        k: 返回的相关文档块数量（默认 3）
    
    Returns:
        相关文档内容字符串
    """
    try:
        # 获取向量存储管理器
        vs_manager = get_vector_store_manager()
        
        # 相似度搜索
        docs = vs_manager.similarity_search(query, k=k)
        
        if not docs:
            return "未找到相关知识，请尝试其他查询关键词。"
        
        # 格式化结果
        results = []
        for i, doc in enumerate(docs):
            content = doc.page_content
            source = doc.metadata.get("source", "未知来源")
            title = doc.metadata.get("title", "")
            
            result = f"[相关知识 {i+1}]"
            if title:
                result += f"\n来源：《{title}》"
            result += f"\n内容：{content}\n"
            results.append(result)
        
        return "\n".join(results)
        
    except Exception as e:
        return f"检索失败：{str(e)}"


def setup_knowledge_base(docx_path: str) -> dict:
    """
    初始化知识库（加载文档到 Chroma）
    
    Args:
        docx_path: .docx 文件路径
        
    Returns:
        统计信息字典
    """
    try:
        print(f"📚 开始初始化知识库...")
        
        # 1. 加载文档
        print(f"📄 正在加载文档：{docx_path}")
        loader = DocumentLoader(chunk_size=500, chunk_overlap=50)
        documents = loader.load_docx(docx_path)
        print(f"✅ 已加载 {len(documents)} 个文档块")
        
        # 2. 获取向量存储管理器
        vs_manager = get_vector_store_manager()
        
        # 3. 添加到向量存储
        count = vs_manager.add_documents(documents)
        
        # 4. 获取统计信息
        stats = vs_manager.get_collection_stats()
        
        print(f"✅ 知识库初始化完成")
        print(f"📊 统计信息：{stats}")
        
        return {
            "success": True,
            "document_count": len(documents),
            "added_count": count,
            "stats": stats
        }
        
    except Exception as e:
        print(f"❌ 初始化知识库失败：{str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e)
        }


def search_knowledge(query: str, k: int = 3) -> list:
    """
    搜索知识库（供外部调用）
    
    Args:
        query: 查询文本
        k: 返回数量
        
    Returns:
        文档列表
    """
    try:
        vs_manager = get_vector_store_manager()
        docs = vs_manager.similarity_search(query, k=k)
        return docs
    except Exception as e:
        print(f"❌ 搜索失败：{str(e)}")
        return []


if __name__ == "__main__":
    # 测试检索功能
    print("🧪 测试 RAG 检索功能...")
    
    # 测试搜索
    test_query = "穿搭核心原则"
    print(f"\n🔍 测试查询：{test_query}")
    
    result = retrieve_knowledge(test_query, k=3)
    print(result)
    
    print("\n✅ 测试完成")
