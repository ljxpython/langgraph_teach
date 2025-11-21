#!/usr/bin/env python3
"""
验证配置是否正确从环境变量加载
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 确保加载当前目录的 .env 文件
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 加载了 .env 文件: {env_path}")
else:
    print(f"⚠️  未找到 .env 文件: {env_path}")

print("\n📋 当前环境变量状态:")
print("-" * 50)

# 检查所有相关的环境变量
env_vars = {
    "LLM_PROVIDER": "LLM 提供商",
    "LLM_MODEL": "LLM 模型", 
    "LLM_API_KEY": "LLM API 密钥",
    "LLM_BASE_URL": "LLM Base URL",
    "EMBEDDING_MODEL": "嵌入模型",
    "EMBEDDING_BASE_URL": "嵌入服务 URL",
    "MILVUS_URI": "Milvus URI",
    "MILVUS_COLLECTION": "Milvus 集合",
    "SERVER_PORT": "服务器端口",
    "SERVER_HOST": "服务器主机",
}

for var, description in env_vars.items():
    value = os.getenv(var)
    if value:
        if "API_KEY" in var or "SECRET" in var:
            # 隐藏敏感信息
            masked_value = value[:8] + "*" * (len(value) - 12) + value[-4:] if len(value) > 12 else "*" * len(value)
            print(f"✅ {description}: {masked_value}")
        else:
            print(f"✅ {description}: {value}")
    else:
        print(f"ℹ️  {description}: 未设置")

print("\n🔍 验证结果:")
print("-" * 50)

# 检查必需的 API 密钥
if os.getenv("LLM_API_KEY"):
    print("✅ LLM_API_KEY 已设置，服务器可以正常启动")
else:
    print("❌ LLM_API_KEY 未设置，服务器将无法启动")
    print("   请在 .env 文件中添加: LLM_API_KEY=your_api_key")

# 检查其他重要配置
if os.getenv("EMBEDDING_BASE_URL"):
    print("✅ 嵌入服务地址已配置")
else:
    print("ℹ️  嵌入服务地址将使用默认值")

if os.getenv("MILVUS_URI"):
    print("✅ Milvus 服务地址已配置")
else:
    print("ℹ️  Milvus 服务地址将使用默认值")

print("\n🎯 下一步:")
print("1. 如果所有必需的配置都已设置，可以运行: python server.py")
print("2. 如果需要修改配置，请编辑 .env 文件")
print("3. 查看配置指南: cat CONFIGURATION_GUIDE.md")