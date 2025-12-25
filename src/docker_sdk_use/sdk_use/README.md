# 🚀 LangGraph SDK 系统学习计划

## 📡 服务配置
**本项目使用已部署的LangGraph服务**
- 服务地址: `http://localhost:8123`
- 助手ID: `agent_not_deep`
- 启动命令: `docker compose -f docker-compose.langgraph.yml up -d`

## 🛠️ 环境准备

### 1. 安装依赖
```bash
pip install langgraph-sdk python-dotenv
```

### 2. 启动服务
```bash
# 在项目根目录执行
docker compose -f docker-compose.langgraph.yml up -d
```

### 3. 验证连接
```bash
# 检查服务是否正常
curl http://localhost:8123/ok

# 或使用Python验证
python -c "import asyncio; from langgraph_sdk import get_client; asyncio.run(get_client('http://localhost:8123').assistants.search())"
```

## 🚀 快速开始

### 方式1: 使用启动脚本（推荐）
```bash
python quick_start.py
```

### 方式2: 直接运行示例
```bash
# 基础连接示例
python 01_basic/python_basic_connection.py

# 线程管理示例
python 02_core/python_thread_management.py

# 高级功能示例
python 03_advanced/python_advanced_features.py
```

### 方式3: 验证所有代码
```bash
python validate_code.py
```

## 📚 学习大纲

### 阶段一：基础入门 (第1天)
**目标**: 掌握SDK基本安装、连接和简单交互

#### 1.1 环境准备 ✅
- [x] 安装LangGraph SDK
- [x] 配置开发环境
- [x] 获取项目服务地址

#### 1.2 基础连接 ✅
- [x] 创建客户端连接
- [x] 验证连接状态
- [x] 错误处理和重连机制

#### 1.3 简单交互 ✅
- [x] 创建线程(threads)
- [x] 发送消息
- [x] 接收响应
- [x] 基础流式处理

### 阶段二：核心功能 (第2天)
**目标**: 掌握threads、runs、streams的核心API

#### 2.1 线程管理 ✅
- [x] 创建新线程
- [x] 获取线程信息
- [x] 更新线程状态
- [x] 线程历史管理

#### 2.2 运行控制 ✅
- [x] 创建运行(runs)
- [x] 监控运行状态
- [x] 取消运行
- [x] 批量运行管理

#### 2.3 流式处理 ✅
- [x] 多种流模式(stream_mode)
- [x] 事件处理
- [x] 自定义数据流
- [x] 子图流处理

### 阶段三：高级特性 (第3天)
**目标**: 掌握高级功能和生产级应用

#### 3.1 并发处理 ✅
- [x] 多任务策略
- [x] 并发运行管理
- [x] 资源优化
- [x] 性能监控

#### 3.2 状态管理 ✅
- [x] 检查点管理
- [x] 状态持久化
- [x] 时间旅行调试
- [x] 人工干预

#### 3.3 部署集成 📝
- [ ] 认证和安全
- [ ] 云端部署
- [ ] 监控和日志
- [ ] 错误恢复

### 阶段四：实战项目 (第4-7天)
**目标**: 构建完整的应用程序

#### 4.1 项目架构设计 📝
- [ ] 需求分析
- [ ] 架构设计
- [ ] 技术选型
- [ ] 开发计划

#### 4.2 核心功能开发 📝
- [ ] 用户界面
- [ ] API集成
- [ ] 数据管理
- [ ] 错误处理

#### 4.3 测试和优化 📝
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 安全加固

## 📋 学习资源

### 官方文档
- [LangGraph Python SDK](https://github.com/langchain-ai/langgraph)
- [API参考文档](https://langchain-ai.github.io/langgraph/)

### 代码示例
每个阶段都包含可运行的代码示例，详见对应目录：
- `01_basic/` - 基础示例
- `02_core/` - 核心功能
- `03_advanced/` - 高级特性
- `04_project/` - 实战项目（待实现）

### 工具脚本
- `quick_start.py` - 快速启动脚本
- `validate_code.py` - 代码验证工具

## 🎯 学习成果

完成本计划后，你将能够：
- ✅ 熟练使用LangGraph SDK构建AI应用
- ✅ 掌握异步编程和流式处理
- ✅ 理解AI Agent的工作原理
- 📝 具备生产级应用开发能力

## 🚨 常见问题

### Q: 连接服务失败怎么办？
```bash
# 1. 检查Docker服务
docker ps | grep langgraph

# 2. 检查端口占用
curl http://localhost:8123/ok

# 3. 重启服务
docker compose -f docker-compose.langgraph.yml restart
```

### Q: 导入langgraph_sdk失败？
```bash
# 重新安装依赖
pip install --upgrade langgraph-sdk

# 检查Python环境
python --version  # 需要3.8+
```

### Q: 代码运行报错？
1. 查看错误信息和堆栈跟踪
2. 运行 `python validate_code.py` 验证代码
3. 检查服务是否正常启动
4. 确认使用正确的助手ID (`agent_not_deep`)

## ⚠️ 注意事项

1. **实践为主**: 每个概念都要亲自编写代码验证
2. **循序渐进**: 不要跳跃式学习，打好基础再进阶
3. **问题导向**: 遇到问题及时查阅文档和社区
4. **版本更新**: 关注SDK的版本更新和变化
5. **安全第一**: 不要在生产环境中暴露API密钥

---

**老王的学习建议**: 艹！别光看不练，代码敲起来！遇到不会的就骂，然后解决问题继续搞！

**学习路径总结**:
1. **Day 1**: 基础连接 → `01_basic/python_basic_connection.py`
2. **Day 2**: 核心功能 → `02_core/python_thread_management.py`
3. **Day 3**: 高级特性 → `03_advanced/python_advanced_features.py`
4. **Day 4-7**: 实战项目 → 自己动手实现！