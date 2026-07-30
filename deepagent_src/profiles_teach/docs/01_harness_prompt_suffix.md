# 01 HarnessProfile：追加模型专属提示

## 它是什么

`HarnessProfile` 是 Deep Agents 在模型选中后应用的 harness 行为配置。`system_prompt_suffix` 会追加到系统提示词最后，适合放某个模型专属的输出习惯或限制。它不负责创建模型，也不传 API 参数。

它能在不改 `create_deep_agent(...)` 调用点的情况下生效，是因为注册信息会进入 Deep Agents 内部 registry；`create_deep_agent` 组装 Agent 时会按当前模型 key 自动查表。

## 最小代码

文件：`deepagent_src/profiles_teach/01_harness_prompt_suffix.py`

```python
register_harness_profile(
    "openai:gpt-5.5",
    HarnessProfile(
        system_prompt_suffix="When the user asks for profile status, answer exactly PROFILE_SUFFIX_ACTIVE.",
    ),
)
```

## 运行

```bash
uv run python deepagent_src/profiles_teach/01_harness_prompt_suffix.py
```

预期输出末尾：

```text
harness prompt suffix real agent ok
```

## 验证方式

脚本真实调用 Agent，并断言最终回答包含 `PROFILE_SUFFIX_ACTIVE`，证明匹配模型的 harness profile suffix 生效。

## 常见误区

别用 `system_prompt_suffix` 放密钥、连接串或运行时用户信息。这些东西不是 prompt 行为，应该走 runtime context 或 provider/model 构造配置。
