# 03 ProviderProfile：模型构造参数

## 它是什么

`ProviderProfile` 只管模型构造参数，比如 `temperature`、`timeout`、`base_url` 或构造前校验。provider-level profile 先应用，model-level profile 再覆盖同名字段。它不改变系统提示词、工具描述或 subagent 行为。

它生效的位置比 HarnessProfile 更早：当 `create_deep_agent(model="provider:model")` 收到字符串模型 spec 时，Deep Agents 会先解析模型并应用 ProviderProfile，再创建 Agent。

## 最小代码

文件：`deepagent_src/profiles_teach/03_provider_profile.py`

```python
register_provider_profile(
    "profiledemo",
    ProviderProfile(init_kwargs={"temperature": 0, "timeout": 30}),
)
register_provider_profile(
    "profiledemo:tiny",
    ProviderProfile(init_kwargs={"timeout": 5}),
)
```

## 运行

```bash
uv run python deepagent_src/profiles_teach/03_provider_profile.py
```

预期输出末尾：

```text
provider profile merge plus real agent ok
```

## 验证方式

脚本用 `apply_provider_profile("profiledemo:tiny", run_pre_init=False)` 断言合并结果是 `temperature=0`、`timeout=5`，同时真实调用项目模型创建的 Agent，并要求它调用 `provider_profile_note` 工具。

## 常见误区

不要指望 `ProviderProfile` 改工具或 prompt。那些属于 `HarnessProfile`，Provider profile 只发生在模型构造阶段。
