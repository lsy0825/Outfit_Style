"""
检查 RAG 知识库状态
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.vector_store import VectorStoreManager


if __name__ == "__main__":
    print("=" * 60)
    print("📊 RAG 知识库状态检查")
    print("=" * 60)
    print()
    
    try:
        # 初始化向量存储管理器
        vs_manager = VectorStoreManager(
            persist_directory="./chroma_db",
            collection_name="stylemate_knowledge"
        )
        
        # 获取统计信息
        stats = vs_manager.get_collection_stats()
        
        print("📈 统计信息：")
        print(f"  集合名称：{stats.get('collection_name', 'N/A')}")
        print(f"  文档块数量：{stats.get('document_count', 0)}")
        print(f"  持久化目录：{stats.get('persist_directory', 'N/A')}")
        print()
        
        # 测试搜索
        print("🔍 测试搜索功能...")
        test_query = "穿搭原则"
        docs = vs_manager.similarity_search(test_query, k=2)
        
        print(f"✅ 搜索测试成功，找到 {len(docs)} 个相关文档块")
        print()
        
        print("📄 搜索结果预览：")
        for i, doc in enumerate(docs):
            content = doc.page_content[:100]
            print(f"  [{i+1}] {content}...")
        print()
        
        print("=" * 60)
        print("✅ 知识库状态正常")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 检查失败：{str(e)}")
        import traceback
        traceback.print_exc()
