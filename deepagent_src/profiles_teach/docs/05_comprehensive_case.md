# 05 综合案例：Provider + Harness 一起用

## 它是什么

综合案例把两类 profile 放在一条流程里：Provider profile 合并模型构造参数，Harness profile 调整 Agent 行为。它解决的问题是：同一模型既需要构造默认值，又需要工具和 subagent 层面的 harness 调优。两者分工清楚，别互相乱代替。

## 最小代码

文件：`deepagent_src/profiles_teach/05_comprehensive_case.py`

```python
register_provider_profile("profiledemo", ProviderProfile(init_kwargs={"temperature": 0}))
register_harness_profile(
    "openai:gpt-5.5",
    HarnessProfile(
        tool_description_overrides={"profile_summary_tool": "Use this for the profiles lesson summary."},
        excluded_tools=frozenset({"execute"}),
        general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
    ),
)
```

## 运行

```bash
uv run python deepagent_src/profiles_teach/05_comprehensive_case.py
```

预期输出末尾：

```text
profiles comprehensive real agent ok
```

## 验证方式

脚本断言 provider 参数按优先级合并；同时真实调用 Agent，让它调用 `profile_summary_tool`，并通过工具消息证明 harness profile 下的工具链能正常工作。

## 常见误区

不要用 profile 做全局开关。profiles 是“选中某个 provider/model 时才应用”的调优；不随模型变化的全局行为，直接放 `create_deep_agent(...)` 调用点。

