# 部署说明（前后端同栈）

## 1. 前置要求
- 已安装 Docker 与 Docker Compose (v2)。
- `.env` 已按需填好（Compose 会自动读取）。**注意：`NEXT_PUBLIC_LANGSMITH_API_KEY` 会下发到前端，请使用受限 Key。**
- 如更新了 `langgraph.json`，请重新生成后端 Dockerfile：
  ```bash
  uvx langgraph dockerfile -c langgraph.json Dockerfile
  ```

## 2. 关键环境变量（`.env` 示例）
```env
IMAGE_NAME=my-langgraph:latest              # 后端镜像名
FRONT_IMAGE_NAME=my-langgraph-ui:latest     # 前端镜像名
LANGSMITH_API_KEY=lsv2_xxx                  # LangGraph/LangSmith 访问所需
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
DATABASE_URI=postgres://postgres:postgres@langgraph-postgres:5432/postgres?sslmode=disable
REDIS_URI=redis://langgraph-redis:6379
zhipu_search_mcp_url=...                    # 必填，Agent MCP 服务地址
# 可选：NEXT_PUBLIC_DEFAULT_DEPLOYMENT_URL / NEXT_PUBLIC_DEFAULT_ASSISTANT_ID 覆盖前端默认
```

## 3. 构建镜像
单次构建前后端（推荐）：
```bash
docker compose -f docker-compose.langgraph.yml build
```
或分别构建：
```bash
docker build -t ${IMAGE_NAME:-my-langgraph} -f Dockerfile .
docker build -t ${FRONT_IMAGE_NAME:-my-langgraph-ui} -f fronted/Dockerfile fronted
```

## 4. 单实例启动（含前端）
```bash
docker compose -f docker-compose.langgraph.yml up -d
```
- API 健康检查：`curl http://localhost:8123/ok`
- 前端入口：`http://localhost:3000`
- 默认前端配置：`部署URL=http://localhost:8123`，`助手ID=agent`；可在 UI 右上“设置”中修改并保存到本地。

## 5. 负载均衡（2 实例示例）
```bash
docker compose -f docker-compose.lb.yml up -d --build --scale langgraph-api=2
```
- 入口仍为 `http://localhost:8123`（Nginx 轮询后端）。
- 前端入口：`http://localhost:3000`

## 6. 常用运维命令
- 停止：`docker compose -f docker-compose.langgraph.yml down`
- 查看日志：
  - API：`docker compose -f docker-compose.langgraph.yml logs -n 200 langgraph-api`
  - 前端：`docker compose -f docker-compose.langgraph.yml logs -n 200 langgraph-ui`
  - 实时：`docker compose -f docker-compose.langgraph.yml logs -f langgraph-api`
- 数据卷：Postgres 数据持久化卷为 `langgraph-data`。

## 7. 注意事项
- 前端 `NEXT_PUBLIC_LANGSMITH_API_KEY` 会暴露给浏览器，仅放低权限 Key；或在 UI 内自行输入。
- 如更换部署域名/端口，请同步调整 `.env` 中的 `NEXT_PUBLIC_DEFAULT_DEPLOYMENT_URL`，以便前端默认连接正确地址。
- `zhipu_search_mcp_url` 必填，否则后端启动会因缺失环境变量报错。
