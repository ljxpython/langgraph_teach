# LangGraph/LangSmith 独立部署速记

来源：https://docs.langchain.com/langsmith/deploy-standalone-server

## 官方要点
- 前置：用 LangGraph CLI 本地调试并构建镜像（`langgraph dev`、`langgraph build`/`langgraph dockerfile`），然后再部署。
- 关键环境变量：
  - `REDIS_URI`：作为 pub/sub 流式输出通道；可复用同一 Redis，但不同部署必须使用不同 DB 编号。
  - `DATABASE_URI`：Postgres 存储助手、线程、运行记录和任务队列；可复用同一实例，但每个部署用独立数据库。
  - `LANGSMITH_API_KEY`：访问 LangSmith 所需；`LANGSMITH_ENDPOINT` 指向自托管 LangSmith 时更新。
  - `LANGGRAPH_CLOUD_LICENSE_KEY`：有正式 license 时在启动时校验；为空即 Lite 模式。
  - 需允许访问 `https://beacon.langchain.com` 用于许可校验/用量上报（完全离线需参照 air-gapped 文档）。
- 运行方式：
  - 单容器示例：`docker run --env-file .env -p 8123:8000 -e REDIS_URI=... -e DATABASE_URI=... -e LANGSMITH_API_KEY=... <your-image>`.
  - Compose 基本栈包含 Redis、Postgres 与 `langgraph-api`（8123→8000）。健康检查：`curl http://0.0.0.0:8123/ok` 期待返回 `{"ok":true}`。

## 与当前项目流程对照
1. 使用 uv 管理 Python 3.13 虚拟环境；`langgraph.json` 配好后 `langgraph dev` 调试通过。
2. 生成部署镜像的 Dockerfile（如配置有变需重跑）：`langgraph dockerfile -c langgraph.json Dockerfile`。
3. 构建镜像并打明确 tag，例如：`docker build -t my-langgraph:latest -f Dockerfile .`。
4. 配置 `.env`：
   - `IMAGE_NAME=my-langgraph:latest`
   - `LANGSMITH_API_KEY=...`
   - `LANGSMITH_ENDPOINT=https://api.smith.langchain.com`（或你的自托管地址）
   - 选填 `LANGGRAPH_CLOUD_LICENSE_KEY=<JWT>`；为空则运行 Lite
   - `DATABASE_URI=postgres://postgres:postgres@langgraph-postgres:5432/postgres?sslmode=disable`
   - `REDIS_URI=redis://langgraph-redis:6379`
5. 选择 Compose 并启动：
   - 单实例：`docker compose -f docker-compose.langgraph.yml up -d`
   - 需要 2 个实例 + Nginx 负载（暴露 8123）：`docker compose -f docker-compose.lb.yml up -d --scale langgraph-api=2`
   - 若端口 8123 被 lb 栈占用，先 `docker compose -f docker-compose.lb.yml down` 再起单栈，或统一用 lb 栈。
6. 健康检查：
   - 单实例：`curl http://0.0.0.0:8123/ok`
   - 负载均衡栈：`curl http://<主机>:8123/ok`（Nginx 代理后端实例）。

## 额外注意
- 应用若需更多环境变量，按需在 `.env` 或 `docker run`/Compose `environment` 中补齐。
- Compose 默认 Redis/Postgres 数据卷为本地，生产可替换为托管服务并更新 URI。
- 多部署共用同一 Redis/Postgres 时，确保不同 DB/库名隔离，避免状态串扰。
