# 第七章：Multimodal

Deep Agents 的内置 `read_file` 不只读文本。对受支持的图片、PDF、音视频文件，它会返回标准多模态 content blocks，让支持对应模态的模型直接检查文件内容，而不是把二进制转成乱码塞进 prompt。

## 最小代码

代码在 `deepagent_src/advanced_teach/07_multimodal.py`。

本例复用仓库既有的一张真实机场登机照片，并把它复制进临时目录。它会用**同一模型**走两条路径：直接通过 `HumanMessage` 传图，以及让 Agent 调用 `read_file("/airport.png")`。这样能区分“模型根本不能识图”和“provider 不支持多模态工具结果”这两类问题。

```python
agent = create_deep_agent(
    model=get_gpt_model(disable_tool_streaming=True),
    backend=LocalShellBackend(root_dir=tmp, virtual_mode=True),
    subagents=[],
)

direct = model.invoke(
    [HumanMessage(content=[text_block, image_block])]
)

state = agent.invoke(
    {"messages": [HumanMessage(content="Inspect the scene in /airport.png.")]}
)
```

这里的关键不是复制代码，而是 Agent 的 `read_file` 工具。backend 返回 PNG 的数据；Deep Agents 的 filesystem middleware 根据扩展名把它变成 image content block，再交给模型。示例将 filesystem tool allowlist 限为 `read_file`，避免模型在这个单一验证中绕去 `ls` 或 `execute`。

## 运行命令

```bash
uv run python -m deepagent_src.advanced_teach.07_multimodal
```

这会将仓库里的实拍图复制到临时目录，触发一次直接视觉调用和一次 Agent 调用；文件只存在临时目录，运行结束自动删除。

## 预期现象

```text
direct_image: The aircraft is Thai AirAsia, its dominant color is red, and the people are boarding in a line up the stairs.
tool_calls: read_file
read_file_blocks: image
final: ...
tool_result_vision_supported: False
multimodal capability probe complete
```

直接路径必须识别 `AirAsia`、red 与登机/排队行为，否则脚本会失败。Agent 路径则先断言真的调用 `read_file`，并且返回了 `image` content block，再打印 `tool_result_vision_supported`。

本项目在 **2026-07-29** 的真实结果是：`gpt-5.5` 经当前 `ChatOpenAI` gateway 能正确处理直接图片输入，但 `read_file` 的图片 `ToolMessage` 没有被正确理解，探针输出 `False`。这不是 Deep Agents 把文件当成文本，也不证明模型不支持视觉；它说明这个 provider 链路不支持或没有正确实现**多模态工具结果**。升级或切换模型前，必须重新运行探针，不要凭模型宣传页瞎猜。

## 支持文件

官方当前文档列出的扩展名：

| 类型 | 扩展名 |
| --- | --- |
| 图片 | `.png`、`.jpg`、`.jpeg`、`.gif`、`.webp`、`.heic`、`.heif` |
| 文档 | `.pdf`、`.ppt`、`.pptx` |
| 音频 | `.wav`、`.mp3`、`.aiff`、`.aac`、`.ogg`、`.flac` |
| 视频 | `.mp4`、`.mpeg`、`.mov`、`.avi`、`.flv`、`.mpg`、`.webm`、`.wmv`、`.3gpp` |

是否真正能看、听、读，仍取决于所选模型和 provider 支持的 MIME type。文件扩展名受支持，不等于每个模型都支持该模态。

## 常见误区

不要把 base64 字符串拼进普通文本 prompt。本例的直接探针使用标准 `{"type": "image", "base64": ..., "mime_type": ...}` content block，这是合法的模型输入。长对话或大媒体仍应优先传文件路径或 URL；如果走 `read_file`，还必须验证 provider 支持多模态 tool result。

不要无上限读取大媒体文件。图片、PDF 页面、音视频都会占模型上下文和成本；生产环境要限制大小、页数、时长和允许的 MIME type，并对用户上传文件做恶意内容和权限检查。

## 验证

1. 临时目录复制到有效 PNG。
2. Agent 的 tool call 列表包含 `read_file`。
3. 直接图片输入必须识别 `AirAsia`、red 与登机/排队行为。
4. Agent 路径必须有 `read_file` tool call，且该 tool result 包含 `image` content block。
5. `tool_result_vision_supported` 才表示当前 provider 是否真的能让 Agent 看见工具返回的图片。

官方依据：`/oss/python/deepagents/multimodal` 说明 `read_file` 对支持的非文本文件返回多模态 content blocks，前提是所选模型支持对应模态和 tool result；`/oss/python/langchain/messages` 说明图片可以使用标准 image content block；`/oss/python/deepagents/tools` 说明自定义工具也可以返回同类 content blocks。
