"""
RAG 向量存储管理
使用 Chroma 作为向量数据库
"""
import os
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma


class VectorStoreManager:
    """向量存储管理器（使用 Chroma）"""
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "stylemate_knowledge",
        embedding_model: str = "text-embedding-v4"
    ):
        """
        初始化向量存储管理器
        
        Args:
            persist_directory: Chroma 数据持久化目录
            collection_name: 集合名称
            embedding_model: 嵌入模型名称（sentence-transformers）
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # 创建持久化目录
        os.makedirs(persist_directory, exist_ok=True)
        
        # 初始化嵌入模型（使用阿里云 DashScope 服务）
        print(f"🔄 正在初始化嵌入模型: {embedding_model}...")
        self.embeddings = DashScopeEmbeddings(
            model=embedding_model,
        )
        print(f"✅ 嵌入模型初始化完成")
        
        # 初始化 Chroma 向量存储
        self.vectorstore = None
        self._init_vectorstore()
    
    def _init_vectorstore(self):
        """初始化 Chroma 向量存储"""
        try:
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            print(f"✅ Chroma 向量存储已连接: {self.persist_directory}")
        except Exception as e:
            raise Exception(f"初始化 Chroma 失败: {str(e)}")
    
    def add_documents(self, documents: List[Document]) -> int:
        """
        添加文档到向量存储
        
        Args:
            documents: Document 列表
            
        Returns:
            添加的文档数量
        """
        if not documents:
            return 0
        
        try:
            # 添加到 Chroma（Chroma 0.4.x+ 自动持久化，无需手动调用 persist()）
            ids = self.vectorstore.add_documents(documents)

            print(f"✅ 已添加 {len(ids)} 个文档块到向量存储")
            return len(ids)

        except Exception as e:
            raise Exception(f"添加文档失败: {str(e)}")
    
    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """
        相似度搜索
        
        Args:
            query: 查询文本
            k: 返回的文档块数量
            
        Returns:
            相关文档块列表
        """
        if not self.vectorstore:
            raise Exception("向量存储未初始化")
        
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            print(f"✅ 找到 {len(docs)} 个相关文档块")
            return docs
        except Exception as e:
            raise Exception(f"搜索失败: {str(e)}")
    
    def similarity_search_with_score(self, query: str, k: int = 3):
        """
        相似度搜索（带相似度分数）
        
        Args:
            query: 查询文本
            k: 返回的文档块数量
            
        Returns:
            (Document, score) 元组列表
        """
        if not self.vectorstore:
            raise Exception("向量存储未初始化")
        
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            print(f"✅ 找到 {len(results)} 个相关文档块（带分数）")
            return results
        except Exception as e:
            raise Exception(f"搜索失败: {str(e)}")
    
    def get_retriever(self, search_kwargs: Optional[dict] = None):
        """
        获取检索器（用于 LangChain Agent）
        
        Args:
            search_kwargs: 搜索参数（如 {"k": 3}）
            
        Returns:
            Retriever 对象
        """
        if not self.vectorstore:
            raise Exception("向量存储未初始化")
        
        if search_kwargs is None:
            search_kwargs = {"k": 3}
        
        return self.vectorstore.as_retriever(search_kwargs=search_kwargs)
    
    def clear_collection(self):
        """清空集合（慎用！）"""
        try:
            self.vectorstore.delete_collection()
            print(f"✅ 已清空集合: {self.collection_name}")
            
            # 重新初始化
            self._init_vectorstore()
        except Exception as e:
            raise Exception(f"清空集合失败: {str(e)}")
    
    def get_collection_stats(self) -> dict:
        """
        获取集合统计信息
        
        Returns:
            统计信息字典
        """
        if not self.vectorstore:
            return {"error": "向量存储未初始化"}
        
        try:
            collection = self.vectorstore._collection
            count = collection.count()
            
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            return {"error": str(e)}
