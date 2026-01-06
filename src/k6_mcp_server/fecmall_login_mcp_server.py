"""
Fecmall 登录 MCP 服务器 - 用于获取 Access Token

本 MCP 服务器提供 Fecmall 登录功能，包括：
- 用户登录并获取 Access-Token
- 支持自定义登录凭证
- 返回响应头中的 Access-Token

主要工具：
1. fecmall_login: 登录并获取 Access-Token
"""
import argparse
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from dotenv import load_dotenv

import httpx
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field


# ============================================================================
# 数据模型
# ============================================================================

class LoginResponse(BaseModel):
    """登录响应"""
    status: str = Field(description="状态：success 或 failure")
    message: str = Field(description="状态描述消息")
    access_token: Optional[str] = Field(default=None, description="访问令牌")
    response_body: Optional[dict] = Field(default=None, description="响应体内容")


# ============================================================================
# Fecmall 客户端
# ============================================================================

class FecmallClient:
    """Fecmall API 客户端"""
# pylint: disable

    def __init__(
        self,
        base_url: str = "http://appserver.huice.com",
        timeout: float = 30.0
    ):
        """初始化 Fecmall 客户端

        参数：
            base_url: Fecmall 服务器基础 URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True
            )
        return self._client

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def login(
        self,
        email: str,
        password: str
    ) -> LoginResponse:
        """调用登录接口获取 Access-Token

        参数：
            email: 用户邮箱
            password: 用户密码

        返回：
            LoginResponse: 包含 access_token 和响应信息

        异常：
            httpx.HTTPError: HTTP 请求错误
            ValueError: 参数验证错误
        """
        # 验证参数
        if not email or not email.strip():
            raise ValueError("邮箱不能为空")
        if not password or not password.strip():
            raise ValueError("密码不能为空")

        # 构建请求数据
        form_data = {
            "email": email.strip(),
            "password": password.strip()
        }

        client = await self._get_client()

        try:
            response = await client.post(
                "/customer/login/account",
                data=form_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            response.raise_for_status()

            # 从响应头中提取 Access-Token
            access_token = response.headers.get("Access-Token")

            # 解析响应体
            response_body = None
            try:
                response_body = response.json()
            except Exception:
                # 如果响应体不是 JSON，保存为文本
                response_body = {"text": response.text}

            if access_token:
                return LoginResponse(
                    status="success",
                    message="登录成功，已获取 Access-Token",
                    access_token=access_token,
                    response_body=response_body
                )
            else:
                return LoginResponse(
                    status="failure",
                    message="登录请求成功，但未在响应头中找到 Access-Token",
                    access_token=None,
                    response_body=response_body
                )

        except httpx.HTTPStatusError as e:
            error_message = f"HTTP 错误 {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_message += f": {error_detail}"
            except Exception:
                error_message += f": {e.response.text}"

            return LoginResponse(
                status="failure",
                message=error_message,
                access_token=None,
                response_body=None
            )
        except httpx.RequestError as e:
            return LoginResponse(
                status="failure",
                message=f"请求失败：{str(e)}",
                access_token=None,
                response_body=None
            )
        except Exception as e:
            return LoginResponse(
                status="failure",
                message=f"未知错误：{str(e)}",
                access_token=None,
                response_body=None
            )


# ============================================================================
# MCP 服务器设置
# ============================================================================

class FecmallContext:
    """Fecmall 操作的上下文"""
    def __init__(self, client: FecmallClient):
        self.client = client


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[FecmallContext]:
    """管理 Fecmall 客户端的应用程序生命周期"""
    config = server.config

    client = FecmallClient(
        base_url=config.get("fecmall_base_url", "http://appserver.huice.com"),
        timeout=config.get("timeout", 30.0)
    )

    try:
        yield FecmallContext(client)
    finally:
        await client.close()


mcp = FastMCP(name="Fecmall Login", lifespan=server_lifespan)


# ============================================================================
# MCP 工具
# ============================================================================

@mcp.tool()
async def fecmall_login(
    email: str,
    password: str,
    ctx: Context = None
) -> str:
    """
    登录 Fecmall 系统并获取 Access-Token。

    此工具用于：
    - 使用邮箱和密码登录 Fecmall 系统
    - 从响应头中提取 Access-Token
    - 返回登录状态和 Token 信息

    参数：
        email: 用户邮箱地址
        password: 用户密码

    返回：
        包含登录状态、Access-Token 和响应信息的格式化文本

    示例：
        fecmall_login(email="user@example.com", password="your_password")
    """
    client = ctx.request_context.lifespan_context.client

    try:
        response = await client.login(email=email, password=password)

        # 构建输出
        output = f"🔐 Fecmall 登录结果\n"
        output += f"{'='*80}\n\n"
        output += f"📧 邮箱：{email}\n"
        output += f"📈 状态：{response.status}\n"
        output += f"💬 消息：{response.message}\n\n"

        if response.access_token:
            output += f"🎫 Access-Token\n"
            output += f"{'='*80}\n"
            output += f"{response.access_token}\n\n"

        if response.response_body:
            output += f"{'='*80}\n"
            output += f"📄 响应体\n"
            output += f"{'='*80}\n"
            import json
            output += json.dumps(response.response_body, ensure_ascii=False, indent=2)
            output += "\n"

        return output

    except ValueError as e:
        return f"❌ 参数错误：{str(e)}"
    except Exception as e:
        return f"❌ 登录失败：{str(e)}"


# ============================================================================
# 主入口点
# ============================================================================

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Fecmall 登录 MCP 服务器")
    parser.add_argument(
        "--fecmall-url", type=str, default="http://appserver.huice.com",
        help="Fecmall 服务器 URL"
    )
    parser.add_argument(
        "--timeout", type=float, default=30.0,
        help="请求超时时间（秒）"
    )
    parser.add_argument(
        "--sse", action="store_true", default=True,
        help="启用 SSE 模式"
    )
    parser.add_argument(
        "--port", type=int, default=8003,
        help="SSE 服务器端口号"
    )
    return parser.parse_args()


def main():
    """主入口点"""
    load_dotenv()
    args = parse_arguments()

    mcp.config = {
        "fecmall_base_url": os.environ.get("FECMALL_BASE_URL", args.fecmall_url),
        "timeout": float(os.environ.get("FECMALL_TIMEOUT", args.timeout))
    }

    if args.sse:
        mcp.run(transport="sse", port=args.port, host="0.0.0.0")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
