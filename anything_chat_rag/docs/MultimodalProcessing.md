# 多模态文档处理集成指南

## 概述

LightRAG 现已集成 RAG-Anything 框架，支持对包含图片、表格、公式等多模态内容的文档进行高质量解析和处理。

## 功能特性

- **多模态内容支持**：自动识别和处理文档中的图片、表格、公式等元素
- **智能解析器选择**：支持 MinerU 和 Docling 两种解析器
- **自动回退机制**：如果多模态处理失败，自动回退到标准文档处理流程
- **无缝集成**：与现有的文档上传和扫描功能完全兼容

## 支持的文件格式

- **PDF 文档**：包含图片、表格、公式的 PDF 文件
- **Office 文档**：Word (.docx)、PowerPoint (.pptx)、Excel (.xlsx)
- **图片文件**：PNG、JPG、JPEG、BMP、GIF、TIFF、WEBP
- **文本文件**：TXT、Markdown (.md)

## 配置选项

### 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# 启用多模态处理（默认：true）
ENABLE_MULTIMODAL_PROCESSING=true

# 选择解析器：mineru 或 docling（默认：mineru）
MULTIMODAL_PARSER=mineru

# 解析方法：auto、ocr 或 txt（默认：auto）
MULTIMODAL_PARSE_METHOD=auto

# 解析器输出目录（默认：./parser_output）
MULTIMODAL_PARSER_OUTPUT_DIR=./parser_output

# ===== Vision Model 配置（用于图片理解） =====
# 如果不配置，将使用 LLM_BINDING 的配置作为 fallback

# OpenAI Vision Model 配置示例
VL_BINDING=openai
VL_MODEL=gpt-4o
VL_BINDING_HOST=https://api.openai.com/v1
VL_BINDING_API_KEY=your_api_key

# Azure OpenAI Vision Model 配置示例
# VL_BINDING=azure_openai
# VL_MODEL=gpt-4o
# VL_BINDING_HOST=https://your-resource.openai.azure.com
# VL_BINDING_API_KEY=your_azure_api_key
# AZURE_OPENAI_VL_API_VERSION=2024-08-01-preview

# Gemini Vision Model 配置示例
# VL_BINDING=gemini
# VL_MODEL=gemini-2.0-flash-exp
# VL_BINDING_HOST=https://generativelanguage.googleapis.com
# VL_BINDING_API_KEY=your_gemini_api_key

# Ollama 本地 Vision Model 配置示例（如 llava）
# VL_BINDING=ollama
# VL_MODEL=llava:latest
# VL_BINDING_HOST=http://localhost:11434
```

### 命令行参数配置

启动 API 服务器时可以使用以下参数：

```bash
lightrag-server \
  --enable-multimodal-processing \
  --multimodal-parser mineru \
  --multimodal-parse-method auto \
  --multimodal-parser-output-dir ./parser_output \
  --vl-binding openai \
  --vl-model gpt-4o \
  --vl-binding-host https://api.openai.com/v1 \
  --vl-binding-api-key your_api_key
```

### Vision Model 配置说明

Vision Model 用于处理文档中的图片内容，生成图片描述和理解图片语义。

**配置优先级**：
1. 如果设置了 `VL_BINDING`、`VL_MODEL` 等参数，将使用专门的 Vision Model
2. 如果未设置，将自动使用 `LLM_BINDING` 的配置作为 fallback
3. 如果 Vision Model 初始化失败，将使用 LLM 作为 fallback

**推荐配置**：
- **高质量图片理解**：使用 `gpt-4o` 或 `gemini-2.0-flash-exp`
- **成本优化**：使用 `gpt-4o-mini` 或本地 Ollama 模型（如 `llava`）
- **离线部署**：使用 Ollama 本地模型

**支持的 Vision Model Binding**：
- `openai`：OpenAI GPT-4 Vision 系列模型
- `azure_openai`：Azure OpenAI 部署的 Vision 模型
- `gemini`：Google Gemini 多模态模型
- `ollama`：本地 Ollama 部署的 Vision 模型（如 llava、bakllava）

## 解析器说明

### MinerU 解析器

- **优势**：对 PDF 文档的解析质量高，特别适合学术论文、技术文档
- **支持格式**：PDF、图片、Office 文档
- **推荐场景**：包含复杂公式、表格、图表的文档

### Docling 解析器

- **优势**：对 Office 文档和 HTML 的解析效果好
- **支持格式**：Office 文档、HTML、PDF
- **推荐场景**：企业文档、报告、演示文稿

## 使用方法

### 1. 通过 API 上传文件

```bash
curl -X POST "http://localhost:9621/documents/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf"
```

响应示例：

```json
{
  "status": "success",
  "message": "File 'document.pdf' uploaded successfully. Processing will continue in background.",
  "track_id": "upload_20250113_123456_abc123"
}
```

### 2. 通过扫描目录批量处理

```bash
curl -X POST "http://localhost:9621/documents/scan" \
  -H "accept: application/json"
```

响应示例：

```json
{
  "status": "scanning_started",
  "message": "Scanning process has been initiated in the background",
  "track_id": "scan_20250113_123456_def456"
}
```

### 3. 监控处理进度

使用返回的 `track_id` 查询处理状态：

```bash
curl -X GET "http://localhost:9621/pipeline/status?track_id=upload_20250113_123456_abc123" \
  -H "accept: application/json"
```

## 工作流程

1. **文件上传**：用户通过 API 上传文档
2. **格式检测**：系统检测文件格式，判断是否需要多模态处理
3. **文档解析**：
   - 如果启用多模态处理且文件格式支持，使用 RAG-Anything 解析
   - 否则使用标准文本提取方法
4. **内容处理**：
   - 提取文本内容
   - 处理图片（生成描述）
   - 处理表格（转换为结构化文本）
   - 处理公式（转换为 LaTeX 或文本描述）
5. **知识图谱构建**：将处理后的内容插入 LightRAG 知识图谱
6. **状态更新**：更新文档处理状态

## 多模态内容处理

### 图片处理

LightRAG 使用配置的 Vision Model 来理解和处理文档中的图片：

- **自动图片识别**：系统自动检测文档中的图片元素
- **Vision Model 调用**：使用配置的 Vision Model（如 GPT-4o、Gemini）生成图片描述
- **上下文融合**：提取图片周围的上下文文本，与图片描述结合
- **语义增强**：将图片描述与上下文结合，生成完整的语义表示
- **Fallback 机制**：如果 Vision Model 不可用，使用 LLM 进行文本处理

**Vision Model 工作流程**：
1. 解析器提取文档中的图片（base64 编码）
2. 将图片和提示词发送给 Vision Model
3. Vision Model 返回图片的详细描述
4. 将描述整合到文档的知识图谱中

**支持的图片格式**：JPG、PNG、BMP、GIF、TIFF、WEBP

### 表格处理

- 识别表格结构
- 转换为 Markdown 格式
- 提取表格标题和说明
- 保留表格的语义关系

### 公式处理

- 识别数学公式
- 转换为 LaTeX 格式
- 提取公式周围的解释文本
- 保留公式的数学语义

## 故障排除

### 问题：多模态处理失败

**解决方案**：
1. 检查日志文件，查看具体错误信息
2. 确认 RAG-Anything 依赖已正确安装
3. 验证解析器配置是否正确
4. 系统会自动回退到标准处理流程

### 问题：解析速度慢

**解决方案**：
1. 对于简单文档，可以禁用多模态处理
2. 调整 `MULTIMODAL_PARSE_METHOD` 为 `txt` 以跳过 OCR
3. 考虑使用更快的解析器（如 Docling）

### 问题：内存占用高

**解决方案**：
1. 减少并发处理的文档数量
2. 清理 `parser_output` 目录中的临时文件
3. 调整解析器的批处理大小

## 性能优化建议

1. **批量处理**：使用扫描功能批量处理多个文档
2. **缓存利用**：解析结果会缓存在 `parser_output` 目录
3. **选择性启用**：仅对需要多模态处理的文档启用该功能
4. **资源监控**：监控系统资源使用情况，适时调整配置

## 示例代码

### Python 客户端示例

```python
import requests

# 上传文档
def upload_document(file_path):
    url = "http://localhost:9621/documents/upload"
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
    return response.json()

# 查询处理状态
def check_status(track_id):
    url = f"http://localhost:9621/pipeline/status?track_id={track_id}"
    response = requests.get(url)
    return response.json()

# 使用示例
result = upload_document("document_with_images.pdf")
print(f"Upload result: {result}")

track_id = result['track_id']
status = check_status(track_id)
print(f"Processing status: {status}")
```

## 相关文档

- [RAG-Anything 官方文档](https://github.com/HKUDS/RAG-Anything)
- [LightRAG API 文档](../README.md)
- [Docker 部署指南](./DockerDeployment.md)

## 技术支持

如有问题或建议，请在 GitHub 上提交 Issue。

