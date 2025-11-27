# Vision Model 配置指南

## 概述

LightRAG API 服务器支持配置专门的 Vision Model 用于多模态文档处理。Vision Model 用于理解和描述文档中的图片内容，提升多模态 RAG 的质量。

## 配置方式

### 方式一：环境变量配置（推荐）

在项目根目录的 `.env` 文件中添加以下配置：

```bash
# 启用多模态处理
ENABLE_MULTIMODAL_PROCESSING=true

# Vision Model 配置
VL_BINDING=openai
VL_MODEL=gpt-4o
VL_BINDING_HOST=https://api.openai.com/v1
VL_BINDING_API_KEY=your_openai_api_key
```

### 方式二：命令行参数

启动服务器时通过命令行参数指定：

```bash
lightrag-server \
  --enable-multimodal-processing \
  --vl-binding openai \
  --vl-model gpt-4o \
  --vl-binding-host https://api.openai.com/v1 \
  --vl-binding-api-key your_api_key
```

## 支持的 Vision Model 提供商

### 1. OpenAI GPT-4 Vision

**推荐模型**：`gpt-4o`、`gpt-4o-mini`、`gpt-4-turbo`

```bash
VL_BINDING=openai
VL_MODEL=gpt-4o
VL_BINDING_HOST=https://api.openai.com/v1
VL_BINDING_API_KEY=sk-your-api-key
```

**特点**：
- 图片理解能力强
- 支持高分辨率图片
- API 稳定可靠

### 2. Azure OpenAI

**推荐模型**：`gpt-4o`

```bash
VL_BINDING=azure_openai
VL_MODEL=gpt-4o
VL_BINDING_HOST=https://your-resource.openai.azure.com
VL_BINDING_API_KEY=your_azure_api_key
AZURE_OPENAI_VL_API_VERSION=2024-08-01-preview
```

**特点**：
- 企业级安全和合规
- 数据隐私保护
- 可自定义部署区域

### 3. Google Gemini

**推荐模型**：`gemini-2.0-flash-exp`、`gemini-1.5-pro`

```bash
VL_BINDING=gemini
VL_MODEL=gemini-2.0-flash-exp
VL_BINDING_HOST=https://generativelanguage.googleapis.com
VL_BINDING_API_KEY=your_gemini_api_key
```

**特点**：
- 原生多模态支持
- 处理速度快
- 成本相对较低

### 4. Ollama 本地模型

**推荐模型**：`llava:latest`、`bakllava:latest`

```bash
VL_BINDING=ollama
VL_MODEL=llava:latest
VL_BINDING_HOST=http://localhost:11434
```

**特点**：
- 完全本地部署
- 无需 API 密钥
- 数据不出本地
- 适合离线环境

**安装 Ollama Vision Model**：
```bash
# 安装 llava 模型
ollama pull llava:latest

# 或安装 bakllava 模型
ollama pull bakllava:latest
```

## Fallback 机制

如果未配置 Vision Model 或配置的 Vision Model 不可用，系统会自动使用以下 fallback 策略：

1. **自动 Fallback 到 LLM 配置**：如果未设置 `VL_BINDING`，将使用 `LLM_BINDING` 的配置
2. **LLM 文本处理**：如果 Vision Model 调用失败，将使用 LLM 处理文本内容
3. **日志记录**：所有 fallback 行为都会记录在日志中

## 配置验证

启动服务器后，检查日志输出以确认 Vision Model 配置：

```
INFO: Vision model initialized: gpt-4o using openai provider
INFO: RAG-Anything multimodal processing enabled with parser=mineru with vision model gpt-4o
```

如果看到以下日志，说明使用了 fallback：

```
WARNING: Vision model initialization failed. Multimodal processing will use LLM fallback.
INFO: RAG-Anything multimodal processing enabled with parser=mineru (using LLM fallback)
```

## 最佳实践

### 1. 选择合适的 Vision Model

- **高质量需求**：使用 `gpt-4o` 或 `gemini-1.5-pro`
- **成本优化**：使用 `gpt-4o-mini` 或 `gemini-2.0-flash-exp`
- **离线部署**：使用 Ollama 本地模型
- **企业部署**：使用 Azure OpenAI

### 2. API 密钥管理

- 使用 `.env` 文件管理密钥，不要提交到版本控制
- 为不同环境使用不同的 API 密钥
- 定期轮换 API 密钥

### 3. 性能优化

- 对于大量图片处理，考虑使用更快的模型（如 Gemini Flash）
- 监控 API 调用次数和成本
- 合理设置超时时间（默认使用 `LLM_TIMEOUT`）

## 故障排除

### 问题：Vision Model 初始化失败

**可能原因**：
- API 密钥无效或过期
- 网络连接问题
- 模型名称错误

**解决方案**：
1. 检查 API 密钥是否正确
2. 验证网络连接和 API 端点
3. 查看日志获取详细错误信息
4. 系统会自动 fallback 到 LLM

### 问题：图片处理质量不佳

**解决方案**：
1. 升级到更强大的 Vision Model（如 gpt-4o）
2. 检查图片质量和分辨率
3. 调整解析器配置（`MULTIMODAL_PARSE_METHOD`）

## 相关文档

- [多模态文档处理指南](./MultimodalProcessing.md)
- [环境变量配置示例](../env.example)
- [API 服务器文档](../lightrag/api/README.md)

