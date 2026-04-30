# StyleMate - 穿搭推荐 AI Agent

基于实时天气与场景的智能穿搭推荐助手，根据用户所在城市、日期、场合、个人偏好、色系搭配，结合实时天气数据，给出个性化、可执行的穿搭建议。

## 功能特性

### 核心功能
- **实时天气查询**：获取指定城市的温度、湿度、降水、风力等数据
- **日落时间查询**：获取城市当天/次日日出日落时间
- **智能穿搭建议**：基于天气+场合+色系给出搭配方案
- **多轮对话**：支持用户反馈后动态调整推荐
- **偏好记忆**：记住用户常用城市、尺码、风格偏好

### 技术特性
- 使用 LangChain + qwen3-max 构建智能 Agent
- 支持 Server-Sent Events (SSE) 流式输出
- 基于 Redis / 内存 LRU 的缓存机制
- Vue 3 + Vite + TypeScript + Pinia + Element Plus 前端
- RESTful API + SSE 双模式接口

## 项目结构

```
Outfit_Style/
├── backend/                 # 后端服务
│   ├── agents/            # Agent 核心逻辑
│   │   └── stylemate_agent.py
│   ├── api/               # API 路由
│   │   ├── chat.py        # 聊天接口（SSE 流式）
│   │   └── health.py     # 健康检查
│   ├── models/            # 数据模型
│   │   └── clothing.py    # 穿搭建议 Pydantic 模型
│   ├── tools/             # 工具函数
│   │   ├── weather_tool.py
│   │   ├── sunset_tool.py
│   │   └── geocoding_tool.py
│   ├── utils/             # 工具类
│   │   ├── cache.py       # 缓存管理
│   │   └── prompt.py     # 系统提示词
│   ├── main.py            # FastAPI 主程序
│   └── requirements.txt   # Python 依赖
└── frontend/              # 前端项目
    ├── src/
    │   ├── components/    # Vue 组件
    │   │   ├── ChatWindow.vue
    │   │   ├── ClothingCard.vue
    │   │   └── MessageBubble.vue
    │   ├── stores/        # Pinia 状态管理
    │   ├── api/           # API 调用
    │   └── types/        # TypeScript 类型定义
    ├── package.json
    ├── vite.config.ts
    └── tsconfig.json
```

## 快速开始

### 后端启动

1. 安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 配置 API Key：
   - 修改 `tools/weather_tool.py` 中的 `OPENWEATHER_API_KEY`
   - 确保 `main.py` 中的 qwen3-max API Key 正确

3. 启动服务：
```bash
python main.py
```

后端将在 `http://localhost:8000` 启动。

### 前端启动

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

前端将在 `http://localhost:3000` 启动。

## API 文档

### 1. 发起对话（SSE 流式）

**Endpoint**: `POST /v1/chat/stream`

**Headers**:
- Content-Type: application/json
- Accept: text/event-stream

**Request Body**:
```json
{
  "message": "上海明天穿什么？",
  "session_id": "default",
  "stream": true
}
```

**Response**: SSE 数据流
```
data: {"type": "start", "session_id": "default"}
data: {"type": "text", "data": "正在查询上海明天的天气..."}
data: {"type": "text", "data": "根据天气情况，建议穿着：..."}
data: [DONE]
```

### 2. 健康检查

**Endpoint**: `GET /v1/health`

**Response**:
```json
{
  "status": "ok",
  "service": "StyleMate",
  "version": "1.0.0",
  "timestamp": "2026-04-30T14:30:00"
}
```

## 技术栈

### 后端
- **Web 框架**: FastAPI
- **LLM 框架**: LangChain + LangChain-OpenAI
- **LLM 模型**: qwen3-max (阿里云百炼)
- **数据验证**: Pydantic v2
- **HTTP 客户端**: httpx
- **缓存**: Redis / 内存 LRU

### 前端
- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **语言**: TypeScript
- **状态管理**: Pinia
- **UI 组件库**: Element Plus
- **Markdown 渲染**: marked

## 配置说明

### 天气 API

当前使用模拟数据。如需真实天气数据，请：

1. 申请 OpenWeatherMap API Key: https://openweathermap.org/api
2. 修改 `backend/tools/weather_tool.py`:
```python
OPENWEATHER_API_KEY = "your_api_key_here"
```

### LLM 配置

在 `backend/agents/stylemate_agent.py` 中配置：
```python
self.llm = ChatOpenAI(
    model="qwen3-max",
    api_key="your_api_key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.7,
    streaming=True
)
```

## 开发计划

- [ ] 接入真实天气 API
- [ ] 完善会话历史存储（数据库）
- [ ] 用户偏好设置和记忆
- [ ] 支持多轮对话上下文管理
- [ ] 优化缓存策略
- [ ] 增加更多穿搭场景模板
- [ ] 移动端适配优化
- [ ] 部署到生产环境

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**开发者**: StyleMate Team  
**最后更新**: 2026-04-30
