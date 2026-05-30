# SmartRecruit — 基于 RAG 的智能简历推荐系统

## 📌 项目简介

SmartRecruit 是一个基于 **RAG（检索增强生成）** 架构的智能招聘助手系统。支持多格式简历解析、混合向量检索、意图识别与参数提取、候选人智能推荐与追问交互。前端基于 Streamlit 构建 Web 界面，后端采用 LangChain 编排 RAG 流程，底层整合 Milvus / Elasticsearch / MongoDB 三大存储引擎。

---

## 🛠 技术栈

### AI / ML

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 大语言模型 | Qwen-plus / Qwen-omni-turbo（阿里云 DashScope API） | 意图识别、参数提取、答案生成、图片文本提取 |
| 嵌入模型 | BGE-M3（本地部署） | 稠密向量(1024维) + 稀疏向量双路编码 |
| 重排序模型 | BGE-Reranker-Base（CrossEncoder，本地部署） | 检索结果精排 |
| 深度学习框架 | PyTorch 2.x + Transformers | 模型推理 |
| LLM 编排框架 | LangChain 1.x + LangChain-Core | RAG 链构建与异步调用 |

### 数据存储与检索引擎

| 组件 | 技术选型 | 用途 |
|------|----------|------|
| 向量数据库 | **Milvus 2.5.4**（Docker Standalone） | 稠密 + 稀疏向量混合存储与 ANN 搜索 |
| 全文检索引擎 | **Elasticsearch 8.14.0**（Docker） | BM25 关键词全文检索 |
| 文档数据库 | **MongoDB 7**（Docker） | 简历元数据、完整文本存储与去重 |
| 关系型数据库 | MySQL 8.x（预留） | 配置存储（当前未启用） |

### 检索策略

- **混合搜索**：Milvus `hybrid_search` — 稠密向量(语义匹配) + 稀疏向量(关键词匹配)，`WeightedRanker(0.7, 0.3)` 加权融合
- **多路召回**：Milvus 向量搜索 + Elasticsearch BM25 搜索 → 结果合并去重
- **CrossEncoder 重排序**：BGE-Reranker 对召回结果二次排序，提升 Top-K 精度

### Web 与工程化

| 组件 | 技术选型 |
|------|----------|
| Web 框架 | **Streamlit 1.56** |
| 异步编程 | Python asyncio + nest-asyncio |
| 配置管理 | Pydantic BaseSettings |
| 日志系统 | Loguru（分级、自动轮转） |
| 文档解析 | LangChain Community Document Loaders（PDF/DOCX/Markdown/TXT/Image） |
| 文本切分 | LangChain Text Splitters（父子块策略：1000+400，重叠100） |
| 评估框架 | Ragas（Context Precision / Recall 等指标） |
| 容器化 | Docker + Docker Compose |

### 开发语言与环境

- **语言**：Python 3.13
- **包管理**：pip + requirements.txt
- **操作系统**：Windows 11 / Linux

---

## 🏗 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web UI                         │
│            (候选人推荐 / 简历上传 / 简历查看)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 SmartRecruitAgent (RAG Pipeline)            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ 意图识别  │→│ 参数提取  │→│ 查询改写  │→│ 混合检索    │  │
│  │(qwen-plus)│ │(qwen-plus)│ │(qwen-plus)│ │(Milvus+ES) │  │
│  └──────────┘  └──────────┘  └──────────┘  └─────┬──────┘  │
│                                                  │         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┘         │
│  │ 追问处理  │←│ JSON输出  │←│ 重排序 → 答案生成            │
│  │(上下文)   │  │(候选人)   │  │(Reranker)(qwen-plus)       │
│  └──────────┘  └──────────┘  └─────────────────────────────┘
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                 ▼
   ┌──────────┐    ┌──────────────┐   ┌──────────┐
   │  Milvus  │    │Elasticsearch │   │ MongoDB  │
   │ 向量存储  │    │  全文索引     │   │ 元数据   │
   │Dense+Sparse│   │   BM25       │   │ 完整文本  │
   └──────────┘    └──────────────┘   └──────────┘
          ▲                                 ▲
          │          ┌──────────┐           │
          └──────────│  BGE-M3  │───────────┘
                     │ 双路编码  │
                     └──────────┘
```

---

## 🔑 核心功能

### 1. 多格式简历解析
- 支持格式：**PDF、DOCX、Markdown、TXT、JPG、PNG**
- 图片类型简历通过 Qwen-omni-turbo 多模态模型提取文字
- 自动计算文件 SHA256 哈希去重

### 2. 智能意图识别与参数提取
- 6 种意图分类：recruitment / refinement / follow_up / general_inquiry / chit_chat / meta
- 自动提取筛选条件：数量、性别、年龄范围、工作经验年限
- 自然语言理解（如"30岁左右" → age_min:28, age_max:32）

### 3. 混合检索 + 重排序
- Milvus 混合搜索（稠密 70% + 稀疏 30% 加权）
- Elasticsearch BM25 关键词匹配补充召回
- BGE-Reranker CrossEncoder 精排

### 4. 候选人智能推荐
- 结构化 JSON 输出（候选人 ID、推荐理由、文件名、哈希值）
- 支持上下文追问（如"第一个候选人会什么技能？"）
- 前端卡片式展示，支持点击查看简历全文

### 5. 简历批量导入与单份上传
- `system_data_init.py`：扫描目录批量处理
- Web UI 拖拽上传，实时解析入库

---

## 📦 项目结构

```
SmartRecruit/
├── app.py                    # Streamlit 主入口
├── config.py                 # Pydantic 全局配置
├── system_data_init.py       # 批量数据导入脚本
├── requirements.txt          # Python 依赖清单
│
├── rag/                      # RAG 核心模块
│   ├── chain.py              # RAG 链（查询改写→检索→生成）
│   └── rag_pipeline.py       # Agent 编排（意图→参数→检索→输出）
│
├── utils/                    # 工具模块
│   ├── vector_store.py       # Milvus + ES + MongoDB 管理
│   ├── document_processor.py # 文档加载/解析/切块/结构化提取
│   └── model_download.py     # 模型下载管理
│
├── eval/                     # 评估模块
│   └── evaluator.py          # Ragas 评估指标计算
│
├── models/                   # 本地模型
│   ├── bge-m3/               # BGE-M3 嵌入模型 (14 files)
│   └── bge-reranker-base/    # CrossEncoder 重排序模型 (6 files)
│
├── data/resume/              # 本地简历存储 (21 份样本)
├── logs/                     # 分级运行日志
└── tests/                    # 24 个单元测试脚本
```

---

## 🚀 使用说明

### 环境要求

- Docker Desktop（运行 Milvus + MongoDB + Elasticsearch）
- Python 3.10+
- 阿里云 DashScope API Key

### 快速启动

```powershell
# 1. 启动 Docker 服务（Milvus + MongoDB + Elasticsearch）
docker-compose -f D:\milvus-standalone\docker-compose.yml up -d
docker run -d --name mongodb -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=123456 mongo:7
docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" elasticsearch:8.14.0

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 批量导入样本简历（首次运行必须执行）
python system_data_init.py

# 4. 启动 Web 应用
streamlit run app.py --server.port 8501

# 5. 浏览器访问
# http://localhost:8501
```

### 测试搜索功能

在 Web UI「候选人推荐」标签页输入自然语言招聘需求：

> "帮我找一个懂 Python，有3年以上工作经验的工程师"

系统会自动：
1. 识别意图为 `recruitment`
2. 提取参数 `{experience_min: 3, count: 3}`
3. 改写查询为更精确的检索词
4. 执行 Milvus 混合搜索 + Elasticsearch BM25 召回
5. CrossEncoder 重排序
6. 调用 LLM 生成推荐理由并返回 JSON 格式候选人列表

---

## 📊 技术亮点

1. **双路向量编码**：BGE-M3 同时生成稠密向量（语义匹配）和稀疏向量（关键词匹配），无需部署两套模型
2. **混合检索**：Milvus 2.4+ `hybrid_search` API，原生支持多向量字段加权融合
3. **模块化 RAG 链**：基于 LangChain LCEL 声明式语法构建，查询改写→检索→重排→生成解耦可替换
4. **Agent 上下文管理**：支持多轮对话追问，自动关联上一轮候选人列表
5. **结构化数据提取**：LLM 从简历文本中提取姓名/年龄/性别/工作经验等结构化字段，存入 Milvus 标量字段支持过滤查询
6. **全 Docker 化部署**：Milvus Standalone（含 etcd + MinIO）+ MongoDB + Elasticsearch 一站式容器编排
