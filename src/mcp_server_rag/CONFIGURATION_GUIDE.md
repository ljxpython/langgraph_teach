# 🔐 FastMCP RAG 服务器安全配置指南

## 📋 概述

本指南帮助你安全地配置 FastMCP RAG 服务器，将所有敏感信息（API 密钥、服务器地址等）从代码中分离，存储在环境变量中。

## 🚀 快速开始

### 1. 创建环境变量文件

```bash
cd src/mcp_server_rag
cp .env.example .env
```

### 2. 编辑配置文件

打开 `.env` 文件，填写你的实际配置：

```bash
# 编辑 .env 文件
nano .env
```

### 3. 运行服务器

```bash
python server.py
```

## 📖 配置说明

### 🔑 必需配置

| 环境变量 | 说明 | 示例 |
|----------|------|------|
| `LLM_API_KEY` | LLM 服务的 API 密钥 | `sk-your-api-key-here` |

### ⚙️ 可选配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `LLM_PROVIDER` | LLM 提供商 | `deepseek` |
| `LLM_MODEL` | LLM 模型名称 | `deepseek-chat` |
| `LLM_BASE_URL` | LLM 服务地址 | `https://api.deepseek.com/v1` |
| `EMBEDDING_MODEL` | 嵌入模型 | `qwen3-embedding:0.6b` |
| `EMBEDDING_BASE_URL` | 嵌入服务地址 | `http://localhost:11434` |
| `MILVUS_URI` | Milvus 服务器地址 | `http://localhost:19530` |
| `MILVUS_COLLECTION` | 默认集合名称 | `None` |
| `SERVER_PORT` | 服务器端口 | `8001` |
| `SERVER_HOST` | 服务器主机 | `0.0.0.0` |

## 📝 配置示例

### 示例 1: 基本配置
```bash
# .env 文件
LLM_API_KEY=sk-your-secret-api-key
EMBEDDING_BASE_URL=http://your-embedding-server:11434
MILVUS_URI=http://your-milvus-server:19530
```

### 示例 2: 完整配置
```bash
# .env 文件
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_API_KEY=sk-your-api-key-here
LLM_BASE_URL=https://api.deepseek.com/v1

EMBEDDING_MODEL=qwen3-embedding:0.6b
EMBEDDING_BASE_URL=http://your-embedding-server:11434

MILVUS_URI=http://your-milvus-server:19530
MILVUS_COLLECTION=my_knowledge_base

SERVER_PORT=8001
SERVER_HOST=0.0.0.0
```

### 示例 3: 使用 OpenAI
```bash
# .env 文件
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
LLM_API_KEY=sk-your-openai-api-key
LLM_BASE_URL=https://api.openai.com/v1
```

## ⚠️ 安全最佳实践

### 1. 永远不要提交敏感信息到代码仓库
```bash
# 确保 .env 文件在 .gitignore 中
echo ".env" >> .gitignore
```

### 2. 使用强 API 密钥
- 使用复杂、难以猜测的 API 密钥
- 定期更换 API 密钥
- 为不同服务使用不同的 API 密钥

### 3. 限制服务器访问
```bash
# 只允许本地访问
SERVER_HOST=127.0.0.1

# 或只允许特定 IP 访问
SERVER_HOST=192.168.1.100
```

### 4. 使用 HTTPS
```bash
# 对于生产环境，使用 HTTPS
LLM_BASE_URL=https://api.deepseek.com/v1
EMBEDDING_BASE_URL=https://your-secure-embedding-server:11434
```

## 🔧 高级配置

### 环境变量优先级
配置优先级（从高到低）：
1. 环境变量（`.env` 文件）
2. 命令行参数
3. 默认值

### 命令行参数覆盖
即使设置了环境变量，仍然可以通过命令行参数覆盖：
```bash
# 环境变量中设置了 deepseek，但命令行使用 openai
LLM_PROVIDER=deepseek python server.py --llm-provider openai
```

### Docker 环境配置
如果使用 Docker，可以在 docker-compose.yml 中设置：
```yaml
environment:
  - LLM_API_KEY=${LLM_API_KEY}
  - EMBEDDING_BASE_URL=${EMBEDDING_BASE_URL}
  - MILVUS_URI=${MILVUS_URI}
```

## 🐛 故障排除

### 问题 1: API 密钥无效
```
❌ LLM_API_KEY 未设置
```
**解决**: 确保在 `.env` 文件中设置了 `LLM_API_KEY`

### 问题 2: 连接超时
```
❌ 无法连接到嵌入服务
```
**解决**: 检查 `EMBEDDING_BASE_URL` 是否正确，服务是否运行

### 问题 3: Milvus 连接失败
```
❌ 无法连接到 Milvus
```
**解决**: 检查 `MILVUS_URI` 是否正确，Milvus 服务是否可用

## 📊 配置验证

服务器启动时会显示配置摘要：
```
============================================================
🔧 服务器配置摘要
============================================================
LLM 提供商: deepseek
LLM 模型: deepseek-chat
LLM Base URL: https://api.deepseek.com/v1
嵌入模型: qwen3-embedding:0.6b
嵌入服务 URL: http://your-embedding-server:11434
Milvus URI: http://your-milvus-server:19530
默认集合: my_knowledge_base
============================================================
```

注意：API 密钥等敏感信息不会显示在日志中。

## 🚀 下一步

1. **配置完成**: 设置好你的 `.env` 文件
2. **测试运行**: 启动服务器验证配置
3. **安全审查**: 确保没有敏感信息泄露
4. **生产部署**: 考虑使用更安全的配置管理方式

## 💡 提示

- 使用不同的 `.env` 文件用于开发、测试和生产环境
- 考虑使用配置管理工具如 Consul、etcd 等
- 定期审查和更新安全配置
- 监控 API 使用情况，及时发现异常

祝你配置顺利！🔐