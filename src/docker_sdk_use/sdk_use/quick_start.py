#!/usr/bin/env python3
"""
🚀 LangGraph SDK 快速启动脚本
一键验证环境、运行示例、学习SDK

老王出品，必属精品！
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv未安装，将使用默认环境变量")

# 从环境变量获取配置
LANGGRAPH_URL = os.getenv("LANGGRAPH_URL", "http://localhost:8123")
LANGGRAPH_ASSISTANT_ID = os.getenv("LANGGRAPH_ASSISTANT_ID", "agent_not_deep")


def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本！")
        print(f"   当前版本: {sys.version}")
        return False
    print(f"✅ Python版本检查通过: {sys.version.split()[0]}")
    return True


def check_dependencies():
    """检查依赖包"""
    required_packages = ['langgraph_sdk', 'asyncio']
    if os.path.exists(".env"):
        required_packages.append('dotenv')

    missing_packages = []

    for package in required_packages:
        try:
            if package == 'langgraph_sdk':
                import langgraph_sdk
            elif package == 'asyncio':
                import asyncio
            elif package == 'dotenv':
                import dotenv
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        if 'dotenv' in missing_packages:
            print("请运行: pip install python-dotenv")
        if 'langgraph_sdk' in missing_packages:
            print("请运行: pip install langgraph-sdk")
        return False

    print("✅ 依赖包检查通过")
    return True


async def check_service_connection():
    """检查服务连接"""
    print("🔗 检查LangGraph服务连接...")

    try:
        from langgraph_sdk import get_client

        client = get_client(url=LANGGRAPH_URL)
        assistants = await client.assistants.search()

        print(f"✅ 服务连接成功！找到 {len(assistants)} 个助手")
        for assistant in assistants:
            print(f"   - {assistant.get('assistant_id', 'Unknown')}")

        # 检查配置的助手是否存在
        configured_assistant = None
        for assistant in assistants:
            if assistant.get('assistant_id') == LANGGRAPH_ASSISTANT_ID:
                configured_assistant = assistant
                break

        if configured_assistant:
            print(f"✅ 配置的助手存在: {LANGGRAPH_ASSISTANT_ID}")
        else:
            print(f"⚠️ 配置的助手不存在: {LANGGRAPH_ASSISTANT_ID}")
            print("   可用的助手:", [a.get('assistant_id') for a in assistants])

        return True

    except Exception as e:
        print(f"❌ 服务连接失败: {e}")
        print("\n💡 解决方案:")
        print("   1. 启动服务: docker compose -f docker-compose.langgraph.yml up -d")
        print("   2. 检查端口:", LANGGRAPH_URL)
        print("   3. 等待服务启动完成")
        return False


async def run_basic_example():
    """运行基础示例"""
    print("\n" + "="*50)
    print("📚 运行基础示例")
    print("="*50)

    basic_file = Path(__file__).parent / "01_basic" / "python_basic_connection.py"

    if not basic_file.exists():
        print(f"❌ 找不到基础示例文件: {basic_file}")
        return False

    try:
        # 导入并运行基础示例
        sys.path.insert(0, str(basic_file.parent))
        import importlib.util

        spec = importlib.util.spec_from_file_location("basic_connection", basic_file)
        module = importlib.util.module_from_spec(spec)

        print("🚀 运行基础连接示例...")
        await spec.loader.exec_module(module)

        print("✅ 基础示例运行完成！")
        return True

    except Exception as e:
        print(f"❌ 基础示例运行失败: {e}")
        return False


def show_learning_menu():
    """显示学习菜单"""
    print("\n" + "="*60)
    print("📚 LangGraph SDK 学习菜单")
    print("="*60)
    print("1. 🚀 阶段一：基础连接和简单交互")
    print("   python 01_basic/python_basic_connection.py")
    print("")
    print("2. 🔧 阶段二：线程管理和运行控制")
    print("   python 02_core/python_thread_management.py")
    print("")
    print("3. 🚀 阶段三：高级功能和特性")
    print("   python 03_advanced/python_advanced_features.py")
    print("")
    print("4. 🧪 验证所有代码")
    print("   python validate_code.py")
    print("")
    print("5. 📖 查看学习计划")
    print("   cat README.md")
    print("")
    print("💡 老王建议：")
    print("   - 按顺序学习，不要跳跃")
    print("   - 亲自运行每个示例")
    print("   - 遇到问题仔细看错误信息")
    print("   - 修改代码实验不同功能")


def show_project_structure():
    """显示项目结构"""
    print("\n" + "="*60)
    print("📁 项目结构")
    print("="*60)

    sdk_use_dir = Path(__file__).parent
    print(f"sdk_use/           # SDK学习目录")
    print(f"├── 01_basic/       # 基础示例")
    print(f"│   └── python_basic_connection.py")
    print(f"├── 02_core/        # 核心功能")
    print(f"│   └── python_thread_management.py")
    print(f"├── 03_advanced/    # 高级功能")
    print(f"│   └── python_advanced_features.py")
    print(f"├── 04_project/     # 实战项目（待实现）")
    print(f"├── README.md       # 学习计划")
    print(f"├── requirements.txt")
    print(f"├── package.json    # JS依赖（已删除TS相关）")
    print(f"├── .env.example    # 环境变量示例")
    print(f"├── validate_code.py # 代码验证工具")
    print(f"└── quick_start.py  # 本启动脚本")


async def main():
    """主启动函数"""
    print("🚀 LangGraph SDK 快速启动")
    print("👨‍🏫 老王带你入门！")

    # 1. 环境检查
    print("\n📋 环境检查")
    print("-" * 30)

    if not check_python_version():
        return

    if not check_dependencies():
        return

    # 2. 服务连接检查
    print("\n📡 服务检查")
    print("-" * 30)

    service_ok = await check_service_connection()

    if not service_ok:
        print("\n⚠️  服务未启动，但可以继续学习代码结构")
        input("\n按Enter键继续...")
    else:
        # 3. 运行基础示例（如果服务可用）
        await run_basic_example()

    # 4. 显示学习资源
    show_learning_menu()
    show_project_structure()

    # 5. 交互式选择
    print("\n" + "="*60)
    print("🎯 接下来做什么？")
    print("="*60)
    print("1. 运行验证工具 (推荐)")
    print("2. 查看基础示例")
    print("3. 启动服务")
    print("4. 退出")

    try:
        choice = input("\n请选择 (1-4): ").strip()

        if choice == "1":
            print("\n🧪 运行代码验证工具...")
            subprocess.run([sys.executable, "validate_code.py"])
        elif choice == "2":
            print(f"\n📖 基础示例文件: {Path(__file__).parent / '01_basic' / 'python_basic_connection.py'}")
            print("运行命令: python 01_basic/python_basic_connection.py")
        elif choice == "3":
            print("\n🐳 启动Docker服务...")
            print("请在新终端运行:")
            print("docker compose -f docker-compose.langgraph.yml up -d")
        else:
            print("\n👋 再见！继续学习吧！")

    except KeyboardInterrupt:
        print("\n\n👋 用户取消，再见！")
    except Exception as e:
        print(f"\n❌ 选择处理错误: {e}")


if __name__ == "__main__":
    print("💡 快速使用指南:")
    print("   python quick_start.py  # 运行启动脚本")
    print("   python validate_code.py  # 验证代码")
    print("   确保.env文件配置正确！")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 程序中断，再见！")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        print("💡 请检查Python环境和依赖安装")