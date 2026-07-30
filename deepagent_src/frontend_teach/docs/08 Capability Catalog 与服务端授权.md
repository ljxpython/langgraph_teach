生产连接缓存与多租户隔离暂未加入，等进
  入部署章节再处理。







v2 submit 不再接受顶层 context，只接受 config/metadata/
  forkFrom；而仓库后端已有测试明确支持从 config.configurable 归一化运行参数到正式 context。  这个看下,应该如何







不包含整页重写、React UI、全局聊天 store、前端直连 upstream，legacy /runs/* 也暂不删除。



  ### 08 Capability Catalog 与服务端授权

  目标：前端不再硬编码 Tools/MCP/Skills，而是从后端 /capabilities 获取当前用户允许使用的能
  力。

  重点：

  - 后端作为唯一白名单来源
  - 用户、角色、租户权限
  - 前端选择只能缩小权限，不能扩大
  - MCP Server 状态与 Skill 元数据
  - 防止篡改 enabled_tools

  这是最自然的下一章。

  ### 09 Thread 生命周期与历史恢复

  目标：掌握一次对话如何创建、持久化、恢复和清空。

  重点：

  - threadId 与 sessionStorage
  - 加载历史消息和 graph state
  - 页面刷新后恢复 Tool、Todo、HITL 状态
  - New Thread、切换 Thread
  - 同一 Thread 并发运行策略

  ### 10 Streaming 可靠性

  目标：让流式 UI 面对断网、刷新和重复事件仍然正确。

  重点：

  - Cancel、Retry、Reconnect
  - stream.error 分类
  - 重复 ToolMessage 去重
  - 运行中禁用重复提交
  - SSE 中断后的状态重建
  - 长任务自定义进度事件

  ### 11 高级 HITL

  目标：处理多个工具、并行审批和长时间暂停。

  重点：

  - 多个 action_requests
  - respondAll
  - 审批超时和撤销
  - 参数编辑校验
  - 审批人身份与审计日志
  - 恢复时 checkpoint 冲突

  ### 12 文件与 Artifact 工作流

  目标：完善 Coding Agent 的真实 IDE 工作流。

  重点：

  - 文件上传、下载和删除
  - 二进制文件处理
  - 增量文件树刷新
  - 正确的 unified diff
  - 接受或回滚 Agent 修改
  - 大文件和 node_modules 过滤

  ### 13 生产安全与部署

  目标：把本地 localhost 架构迁移到可上线架构。

  重点：

  - LangGraph Server 鉴权
  - CORS 与反向代理
  - Thread/Sandbox 多租户隔离
  - MCP OAuth 和密钥代理
  - Sandbox TTL、资源限制
  - Capability 审计与限流

  ### 14 可观测性与测试

  目标：能够定位“模型为什么调用了这个工具”。

  重点：

  - LangSmith Trace 与 runId
  - 前端展示 Trace URL
  - 用户反馈与评分
  - 后端 contract tests
  - React 组件测试
  - Playwright E2E
  - 少量真实模型验收

  推荐顺序：08 Capability Catalog -> 09 Thread -> 10 Streaming -> 11 HITL -> 12 Artifacts ->
  13 Production -> 14 Testing。下一章应从 08 Capability Catalog 与服务端授权 开始，因为当前
  前端能力列表仍与后端白名单重复维护。





Insufficient account balance





https://xiaok.lol/sign-up?aff=j8Sy







› 在讨论一个问题,这种动态创建agent的方式,其实很耗时吧,所以一般情况下不使用这种方式
  langgraph dev 创建agent的时机是怎么样的? 动态的和静态的

  是每次创建一个线程对话时,就创建一个实例,还是langgraph dev时就创建了一个agent,都共用这个
  agent呢?

  真正的实际生产应用,我们大部分还是使用静态的这种方式吧

  我看到其他的平台的agent可以动态的选择工具和skills,他们的实现方式是怎么样的?





多用户隔离和并发如何做