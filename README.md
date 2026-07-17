# SmartRecruit — 基于 RAG 的智能简历推荐系统

<p align="center">
  <strong>🤖 AI 驱动 | RAG 架构 | 多引擎混合检索 | 智能招聘助手</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.45-FF4B4B?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/LangChain-0.3-1C3C3C?logo=langchain" alt="LangChain">
  <img src="https://img.shields.io/badge/Milvus-2.6-00A3E0?logo=milvus" alt="Milvus">
  <img src="https://img.shields.io/badge/Elasticsearch-8.14-005571?logo=elasticsearch" alt="Elasticsearch">
  <img src="https://img.shields.io/badge/MongoDB-7-47A248?logo=mongodb" alt="MongoDB">
  <img src="https://img.shields.io/badge/PyTorch-2.7-EE4C2C?logo=pytorch" alt="PyTorch">
</p>

---

## 📌 项目简介

SmartRecruit 是一个基于 **RAG（检索增强生成）** 架构的智能招聘助手系统。用户上传简历后，可以用自然语言描述招聘需求，系统自动匹配并推荐最合适的候选人，支持多轮追问对话。

**核心流程**：上传简历 → 文档解析与向量化 → 自然语言查询 → 意图识别 → 参数提取 → 混合检索 → 重排序 → 生成推荐结果 → 结构化输出

底层整合 **Milvus（向量存储）+ Elasticsearch（全文检索）+ MongoDB（文档存储）** 三大引擎，通过 LangChain 编排 RAG 流程，前端使用 Streamlit 构建 Web 交互界面。

---

## ✨ 核心功能

### 📄 多格式简历解析

支持 **PDF、DOCX、Markdown、TXT、JPG、PNG** 等多种格式。图片类简历通过 Qwen-Omni-Turbo 多模态模型提取文字，自动计算 SHA256 哈希去重，避免重复导入。

### 🧠 智能意图识别

系统能自动识别用户输入的意图类型：

| 意图 | 说明 | 示例 |
|------|------|------|
| `recruitment` | 新招聘需求 | "帮我找一个 Python 工程师" |
| `refinement_or_correction` | 修正上一轮条件 | "把年龄范围改成 25-35 岁" |
| `follow_up_question` | 对候选人的追问 | "第一个候选人会什么技能？" |
| `general_job_inquiry` | 行业/岗位咨询 | "数据分析师一般需要什么技能？" |
| `chit_chat` | 闲聊 | "你好，今天天气不错" |
| `meta_inquiry` | 系统询问 | "这个系统支持什么格式的文件？" |

### 🔍 混合检索 + 重排序

```text
用户查询 → 查询改写(LLM) → BGE-M3 双路编码
                               ├─ 稠密向量(1024维) ─┐
                               └─ 稀疏向量(词袋)   ─┤
                                                   ▼
                              Milvus hybrid_search (稠密70% + 稀疏30% 加权)
                                                   +
                              Elasticsearch BM25 关键词召回
                                                   ▼
                              结果合并去重 → BGE-Reranker CrossEncoder 精排
                                                   ▼
                                              Top-K 候选人
```

### 💬 多轮对话追问

支持在上一轮推荐基础上进行追问，分为两种模式：
- **筛选式**："这些候选人里面哪些有博士学位？"
- **问答式**："描述一下候选人 2 的工作经历"

系统自动关联上下文中的候选人列表，返回筛选结果或针对性的回答。

### 📊 结构化推荐输出

```json
{
  "response": "为您找到了以下候选人...",
  "candidates": [
    {
      "candidate_id": 1,
      "reason": "该候选人具有5年Python开发经验，熟练掌握Django和Flask框架...",
      "file_path": "data/resume/张三简历.pdf",
      "doc_hash": "a1b2c3d4..."
    }
  ]
}
```

前端以卡片形式展示，点击可查看简历全文。

### 📥 批量导入与单份上传

- **批量导入**：`system_data_init.py` 扫描 `data/resume/` 目录，一键入库
- **单份上传**：Web UI 拖拽上传，实时解析→切块→向量化→存储

---

## 🏗 系统架构

```text
┌──────────────────────────────────────────────────────────────┐
│                     Streamlit Web UI                         │
│             (候选人推荐 / 简历上传 / 简历查看)                  │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                 SmartRecruitAgent (RAG Pipeline)             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐   │
│  │ 意图识别  │→ │ 参数提取  │→ │ 查询改写  │→ │ 混合检索    │   │
│  │(qwen-plus)│  │(qwen-plus)│  │(qwen-plus)│  │(Milvus+ES) │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────┬─────┘   │
│                                                   │          │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┘          │
│  │ 追问处理  │← │ JSON 输出 │← │ 重排序 → 答案生成             │
│  │ (上下文)  │  │ (候选人)  │  │(Reranker)  (qwen-plus)       │
│  └──────────┘  └──────────┘  └───────────────────────────────┘
└───────────────────────────┬──────────────────────────────────┘
                            │
           ┌────────────────┼────────────────┐
           ▼                ▼                 ▼
    ┌──────────┐    ┌──────────────┐   ┌──────────┐
    │  Milvus  │    │ Elasticsearch│   │ MongoDB  │
    │ 稠密+稀疏 │    │     BM25     │   │  元数据   │
    │ 向量存储  │    │   全文索引    │   │  完整文本  │
    └──────────┘    └──────────────┘   └──────────┘
           ▲                                 ▲
           │          ┌──────────┐           │
           └──────────│  BGE-M3  │───────────┘
                      │  双路编码  │
                      └──────────┘
```

---

## 🛠 技术栈

### AI / ML

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 大语言模型 | **Qwen-Plus / Qwen-Omni-Turbo**（阿里云 DashScope API） | 意图识别、参数提取、答案生成、图片 OCR |
| 嵌入模型 | **BGE-M3**（本地部署） | 稠密向量(1024维) + 稀疏向量双路编码 |
| 重排序模型 | **BGE-Reranker-Base**（CrossEncoder，本地部署） | 检索结果精排 |
| LLM 编排 | **LangChain 0.3** + LangGraph 0.4 | RAG 链构建与异步调用 |
| 深度学习 | **PyTorch 2.7** + Transformers 4.54 + Sentence-Transformers 5.0 | 模型推理 |

### 数据存储与检索引擎

| 组件 | 技术选型 | 用途 |
|------|----------|------|
| 向量数据库 | **Milvus 2.6**（Docker Standalone） | 稠密+稀疏向量混合存储与 ANN 搜索 |
| 全文检索引擎 | **Elasticsearch 8.14**（Docker） | BM25 关键词全文检索 |
| 文档数据库 | **MongoDB 7**（Docker） | 简历元数据、完整文本存储与去重 |
| 关系型数据库 | MySQL 8.x（预留） | 配置存储（当前未启用） |

### Web 与工程化

| 组件 | 技术选型 |
|------|----------|
| Web 框架 | **Streamlit 1.45** |
| 异步编程 | Python asyncio + nest-asyncio |
| 配置管理 | **Pydantic 2.11** BaseModel |
| 日志系统 | **Loguru 0.7**（分模块、自动轮转） |
| 文档解析 | LangChain Community Loaders（PDF / DOCX / Markdown / TXT / Image） |
| 文本切分 | LangChain Text Splitters（父子块策略：父块1000 / 子块400，重叠100） |
| 评估框架 | **Ragas 0.2.6**（忠实度、答案相关性、上下文精确度/召回率） |

### 开发环境

- **语言**：Python 3.13
- **包管理**：pip + requirements.txt
- **操作系统**：Windows 11 / Linux
- **容器化**：Docker + Docker Compose

---

## 📦 项目结构

```text
SmartRecruit/
├── app.py                      # Streamlit 主入口（Web UI）
├── config.py                   # Pydantic 全局配置
├── system_data_init.py         # 批量简历导入脚本
├── requirements.txt            # Python 依赖清单
│
├── rag/                        # RAG 核心模块
│   ├── chain.py                # RAG 链：查询改写 → 检索 → 答案生成
│   └── rag_pipeline.py         # Agent 编排：意图识别 → 参数提取 → RAG → 追问
│
├── utils/                      # 工具模块
│   ├── vector_store.py         # Milvus + ES + MongoDB 管理（混合搜索、存储）
│   ├── document_processor.py   # 文档加载 / 解析 / 切块 / 结构化提取
│   └── model_download.py       # HuggingFace 模型下载
│
├── eval/                       # 评估模块
│   └── evaluator.py            # Ragas 评估指标
│
├── models/                     # 本地模型文件（需自行下载）
│   ├── bge-m3/                 # BGE-M3 嵌入模型
│   └── bge-reranker-base/      # CrossEncoder 重排序模型
│
├── data/resume/                # 样本简历（21 份，含 PDF/DOCX/MD/TXT/JPG）
├── logs/                       # 分级运行日志
└── tests/                      # 24 个单元/集成测试脚本
```

---

## 🚀 快速启动

### 环境要求

- **Docker Desktop**（运行 Milvus + MongoDB + Elasticsearch）
- **Python 3.10+**
- **阿里云 DashScope API Key**（[前往获取](https://dashscope.console.aliyun.com/)）

### 第一步：启动 Docker 服务

```bash
# 1. 启动 Milvus Standalone（内含 etcd + MinIO）
docker-compose -f D:\milvus-standalone\docker-compose.yml up -d

# 2. 启动 MongoDB
docker run -d --name mongodb -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=123456 \
  mongo:7

# 3. 启动 Elasticsearch
docker run -d --name elasticsearch -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.14.0
```

### 第二步：安装依赖

```bash
pip install -r requirements.txt
```

### 第三步：下载模型文件

> ⚠️ **重要**：由于 GitHub 上传大小限制，项目中 `models/` 目录不包含模型权重文件，需要自行下载。

需要下载以下两个模型，放入对应目录：

| 模型 | 下载地址 | 存放路径 |
|------|----------|----------|
| BGE-M3 | [HuggingFace / BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) | `models/bge-m3/` |
| BGE-Reranker-Base | [HuggingFace / BAAI/bge-reranker-base](https://huggingface.co/BAAI/bge-reranker-base) | `models/bge-reranker-base/` |

下载方式（任选一种）：

```bash
# 方式一：使用项目自带的下载脚本
python utils/model_download.py

# 方式二：使用 HuggingFace CLI
huggingface-cli download BAAI/bge-m3 --local-dir models/bge-m3
huggingface-cli download BAAI/bge-reranker-base --local-dir models/bge-reranker-base

# 方式三：使用 Python 代码下载
from transformers import AutoModel, AutoTokenizer
AutoModel.from_pretrained("BAAI/bge-m3").save_pretrained("models/bge-m3")
AutoModel.from_pretrained("BAAI/bge-reranker-base").save_pretrained("models/bge-reranker-base")
```

### 第四步：导入数据

```bash
# 批量导入 data/resume/ 中的样本简历
python system_data_init.py
```

### 第五步：启动应用

```bash
streamlit run app.py --server.port 8501
```

浏览器访问 **http://localhost:8501** 即可使用。

---

## 💡 使用示例

### 搜索候选人

在「候选人推荐」标签页输入自然语言需求：

> "帮我找一个懂 Python，有 3 年以上工作经验的工程师"

系统自动完成：
1. **意图识别** → 判定为 `recruitment`
2. **参数提取** → `{experience_min: 3, count: 2}`
3. **查询改写** → 优化为更精确的检索词
4. **混合召回** → Milvus 向量搜索（稠密+稀疏）+ Elasticsearch BM25
5. **重排序** → BGE-Reranker CrossEncoder 精排
6. **生成推荐** → LLM 输出结构化 JSON，含推荐理由

### 多轮追问

拿到推荐列表后，可以继续追问：

> "这些候选人里谁会大数据？"
> "详细介绍一下第 2 个候选人的项目经验"

### 上传简历

切换到「简历上传」标签页，拖拽或选择文件即可。支持 PDF / DOCX / MD / TXT / JPG / PNG。

---

## 📊 评估体系

项目内置了基于 Ragas 的评估模块（`eval/evaluator.py`），包含两个阶段：

1. **健全性检查**：用标准中文问答对（姚明是谁？）验证评估框架是否正常工作，期望忠实度为 1.0
2. **端到端评估**：用真实招聘查询测试完整 RAG 流程，计算以下指标：

| 指标 | 说明 | 参考阈值 |
|------|------|----------|
| `faithfulness` | 答案是否完全基于检索到的上下文，有无编造 | ≥ 0.80 |
| `answer_relevancy` | 答案与问题的相关程度 | ≥ 0.70 |
| `context_precision` | 检索到的上下文中相关文档的排名 | ≥ 0.70 |
| `context_recall` | 检索是否覆盖了答案所需的所有信息 | ≥ 0.60 |

---

## 🔑 技术亮点

1. **双路向量编码** — BGE-M3 单个模型同时生成稠密向量（语义匹配）和稀疏向量（关键词匹配），无需部署两套模型
2. **混合检索融合** — Milvus `hybrid_search` API + `WeightedRanker(0.7, 0.3)` 原生支持多向量字段加权
3. **多路召回** — Milvus 向量搜索 + Elasticsearch BM25 → 取并集去重 → CrossEncoder 精排，兼顾语义和关键词
4. **模块化 RAG 链** — 基于 LangChain LCEL 声明式语法，查询改写→检索→重排→生成各环节解耦、可替换
5. **父子块切分策略** — 子块(400字)用于索引和检索，父块(1000字)提供更完整的上下文给 LLM，兼顾检索精度和生成完整度
6. **Markdown 感知切分** — 对 `.md` 文件使用 `MarkdownTextSplitter`，保留文档结构
7. **结构化简历提取** — LLM 从原始简历中提取姓名、性别、年龄、工作经验等字段，存入 Milvus 标量字段，支持过滤查询
8. **Agent 上下文管理** — 多轮对话中自动维护当前候选人列表，追问时只需指代"第一个"、"他们"等
9. **多编码兼容** — 对 `.txt` 文件依次尝试 UTF-8、GBK、Latin-1 编码，稳定处理中文文本

---

## 📄 License

本项目仅供学习和演示使用。
