# 多模态文档处理快速入门

## 🎉 新功能

LightRAG 现已集成 RAG-Anything 框架，支持处理包含图片、表格、公式等多模态内容的文档！

## 🚀 快速开始

### 1. 启动服务器

多模态处理功能默认已启用，直接启动服务器即可：

```bash
lightrag-server
```

或者使用自定义配置：

```bash
lightrag-server \
  --enable-multimodal-processing \
  --multimodal-parser mineru \
  --multimodal-parse-method auto
```

### 2. 上传文档

上传包含图片、表格或公式的 PDF 文档：

```bash
curl -X POST "http://localhost:9621/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.pdf"
```

响应示例：
```json
{
  "status": "success",
  "message": "File 'your_document.pdf' uploaded successfully. Processing will continue in background.",
  "track_id": "upload_20250113_123456_abc123"
}
```

### 3. 查询处理状态

使用返回的 `track_id` 查询处理进度：

```bash
curl -X GET "http://localhost:9621/pipeline/status?track_id=upload_20250113_123456_abc123"
```

## 📋 支持的文件格式

- ✅ **PDF 文档**：包含图片、表格、公式的 PDF
- ✅ **Office 文档**：Word (.docx)、PowerPoint (.pptx)、Excel (.xlsx)
- ✅ **图片文件**：PNG、JPG、JPEG、BMP、GIF、TIFF、WEBP
- ✅ **文本文件**：TXT、Markdown (.md)

## ⚙️ 配置选项

### 环境变量配置

在 `.env` 文件中添加：

```bash
# 启用多模态处理（默认：true）
ENABLE_MULTIMODAL_PROCESSING=true

# 选择解析器（默认：mineru）
# 可选值：mineru（适合学术论文）、docling（适合企业文档）
MULTIMODAL_PARSER=mineru

# 解析方法（默认：auto）
# 可选值：auto（自动）、ocr（OCR）、txt（纯文本）
MULTIMODAL_PARSE_METHOD=auto

# 解析器输出目录（默认：./parser_output）
MULTIMODAL_PARSER_OUTPUT_DIR=./parser_output
```

### 命令行参数

```bash
lightrag-server \
  --enable-multimodal-processing \
  --multimodal-parser mineru \
  --multimodal-parse-method auto \
  --multimodal-parser-output-dir ./parser_output
```

## 🔍 解析器说明

### MinerU 解析器（推荐用于学术文档）

- **优势**：对 PDF 文档的解析质量高，特别适合学术论文、技术文档
- **适用场景**：包含复杂公式、表格、图表的文档

### Docling 解析器（推荐用于企业文档）

- **优势**：对 Office 文档和 HTML 的解析效果好
- **适用场景**：企业文档、报告、演示文稿

## 💡 使用示例

### Python 客户端

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

### JavaScript/TypeScript 客户端

```typescript
// 上传文档
async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:9621/documents/upload', {
    method: 'POST',
    body: formData,
  });
  
  return await response.json();
}

// 查询处理状态
async function checkStatus(trackId: string) {
  const response = await fetch(
    `http://localhost:9621/pipeline/status?track_id=${trackId}`
  );
  return await response.json();
}

// 使用示例
const result = await uploadDocument(file);
console.log('Upload result:', result);

const status = await checkStatus(result.track_id);
console.log('Processing status:', status);
```

## 🎯 工作原理

1. **文件上传** → 用户通过 API 上传文档
2. **格式检测** → 系统检测文件格式，判断是否需要多模态处理
3. **文档解析** → 使用 RAG-Anything 解析文档内容
   - 提取文本内容
   - 处理图片（生成描述）
   - 处理表格（转换为结构化文本）
   - 处理公式（转换为 LaTeX）
4. **知识图谱构建** → 将处理后的内容插入 LightRAG 知识图谱
5. **状态更新** → 更新文档处理状态

## 🛡️ 自动回退机制

如果多模态处理失败，系统会自动回退到标准文档处理流程，确保系统的稳定性。

## 📊 性能优化建议

1. **批量处理**：使用扫描功能批量处理多个文档
2. **缓存利用**：解析结果会缓存在 `parser_output` 目录
3. **选择性启用**：仅对需要多模态处理的文档启用该功能
4. **资源监控**：监控系统资源使用情况，适时调整配置

## 🔧 故障排除

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

## 📚 详细文档

- [多模态处理详细指南](docs/MultimodalProcessing.md)
- [集成总结文档](docs/MultimodalIntegrationSummary.md)
- [RAG-Anything 官方文档](https://github.com/HKUDS/RAG-Anything)

## 🧪 运行测试

```bash
# 激活虚拟环境
source .venv/Scripts/activate  # Windows Git Bash
# 或
source .venv/bin/activate      # Linux/Mac

# 运行集成测试
python tests/test_multimodal_integration.py
```

## 🎓 示例场景

### 场景 1：处理学术论文

上传包含复杂公式和图表的学术论文：

```bash
curl -X POST "http://localhost:9621/documents/upload" \
  -F "file=@research_paper.pdf"
```

系统会：
- 识别并转换数学公式为 LaTeX
- 提取图表并生成描述
- 识别表格并转换为结构化文本

### 场景 2：处理企业报告

上传包含图片和表格的企业报告：

```bash
curl -X POST "http://localhost:9621/documents/upload" \
  -F "file=@business_report.docx"
```

系统会：
- 提取文档中的图片并生成描述
- 识别表格并保留结构
- 提取文本内容

### 场景 3：批量处理文档

将多个文档放入 input 目录，然后触发扫描：

```bash
curl -X POST "http://localhost:9621/documents/scan"
```

系统会自动处理所有新文档，包括多模态内容。

## 🤝 贡献

如有问题或建议，请在 GitHub 上提交 Issue。

## 📄 许可证

本项目遵循与 LightRAG 相同的许可证。

---

**享受强大的多模态文档处理能力！** 🚀

