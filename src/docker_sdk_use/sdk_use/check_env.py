#!/usr/bin/env python3
"""
⚡ 快速验证修复后的代码
测试环境变量加载和基础功能

老王出品，必属精品！
"""

import sys
import os
from pathlib import Path

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ python-dotenv 安装并加载成功")
except ImportError:
    print("❌ python-dotenv 未安装")
    print("请运行: pip install python-dotenv")
    sys.exit(1)

# 检查.env文件是否存在
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    print(f"✅ .env 文件存在: {env_file}")
else:
    print(f"❌ .env 文件不存在: {env_file}")
    print("请复制 .env.example 为 .env 并配置相应参数")
    sys.exit(1)

# 检查环境变量
required_vars = ["LANGGRAPH_URL", "LANGGRAPH_ASSISTANT_ID"]
missing_vars = []

for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"✅ {var} = {value}")
    else:
        print(f"❌ {var} 未设置")
        missing_vars.append(var)

if missing_vars:
    print(f"\n❌ 缺少环境变量: {', '.join(missing_vars)}")
    print("请在 .env 文件中设置这些变量")
    sys.exit(1)

# 测试SDK导入
try:
    from langgraph_sdk import get_client
    print("✅ langgraph-sdk 导入成功")
except ImportError as e:
    print(f"❌ langgraph-sdk 导入失败: {e}")
    print("请运行: pip install langgraph-sdk")
    sys.exit(1)

print("\n🎉 环境验证通过！")
print("📋 配置信息:")
print(f"   服务地址: {os.getenv('LANGGRAPH_URL')}")
print(f"   助手ID: {os.getenv('LANGGRAPH_ASSISTANT_ID')}")
print(f"   API密钥: {'已设置' if os.getenv('LANGGRAPH_API_KEY') else '未设置'}")
print("\n💡 现在可以运行:")
print("   python quick_start.py")
print("   python validate_code.py")