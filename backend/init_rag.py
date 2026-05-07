"""
初始化 RAG 知识库
加载文档到 Chroma 向量数据库
"""
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.retriever_tool import setup_knowledge_base


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 初始化 RAG 知识库")
    print("=" * 60)
    
    # 文档路径
    docx_path = r"C:\Users\12629\Desktop\穿搭核心原则.docx"
    
    if not os.path.exists(docx_path):
        print(f"❌ 文档不存在: {docx_path}")
        print("\n请修改脚本中的 docx_path 为实际路径")
        sys.exit(1)
    
    print(f"📄 文档路径: {docx_path}")
    print()
    
    # 初始化知识库
    result = setup_knowledge_base(docx_path)
    
    print()
    print("=" * 60)
    if result["success"]:
        print("✅ 知识库初始化成功！")
        print(f"📊 加载文档块数: {result['document_count']}")
        print(f"📥 添加到向量库数: {result['added_count']}")
        print(f"📈 统计信息: {result['stats']}")
    else:
        print("❌ 知识库初始化失败！")
        print(f"错误信息: {result['error']}")
    print("=" * 60)
