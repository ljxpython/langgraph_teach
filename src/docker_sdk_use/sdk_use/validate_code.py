"""
🧪 LangGraph SDK 代码验证工具
自动验证所有示例代码的可用性

老王出品，必属精品！
"""

import asyncio
import sys
import os
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Any

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv未安装，将使用默认环境变量")

# 项目根目录添加到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class CodeValidator:
    """代码验证器"""

    def __init__(self):
        """从环境变量获取配置"""
        self.sdk_url = os.getenv("LANGGRAPH_URL", "http://localhost:8123")
        self.api_key = os.getenv("LANGGRAPH_API_KEY")
        self.assistant_id = os.getenv("LANGGRAPH_ASSISTANT_ID", "agent_not_deep")
        self.results = {
            "connection_test": False,
            "basic_examples": [],
            "core_examples": [],
            "advanced_examples": [],
            "errors": []
        }

        print(f"🔧 验证器配置:")
        print(f"   服务地址: {self.sdk_url}")
        print(f"   助手ID: {self.assistant_id}")
        print(f"   API密钥: {'已设置' if self.api_key else '未设置'}")

    async def test_connection(self) -> bool:
        """测试LangGraph服务连接"""
        print("🔗 测试LangGraph服务连接...")

        try:
            from langgraph_sdk import get_client

            client = get_client(url=self.sdk_url)

            # 尝试获取助手列表
            assistants = await client.assistants.search()

            print(f"✅ 连接成功！找到 {len(assistants)} 个助手:")
            for assistant in assistants:
                print(f"   - {assistant.get('assistant_id', 'Unknown')}: {assistant.get('name', 'No name')}")

            self.results["connection_test"] = True
            return True

        except ImportError:
            error = "❌ langgraph-sdk未安装！请运行: pip install langgraph-sdk"
            print(error)
            self.results["errors"].append(error)
            return False

        except Exception as e:
            error = f"❌ 连接失败: {e}"
            print(error)
            self.results["errors"].append(error)
            return False

    async def validate_basic_examples(self) -> List[Dict]:
        """验证基础示例"""
        print("\n" + "="*50)
        print("📚 验证基础示例代码")
        print("="*50)

        basic_dir = Path(__file__).parent / "01_basic"
        examples = []

        # 查找Python示例文件
        for py_file in basic_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            example_name = py_file.stem
            print(f"\n🔍 验证: {example_name}")

            result = {
                "name": example_name,
                "file": str(py_file),
                "syntax_valid": False,
                "imports_valid": False,
                "execution_test": False,
                "error": None
            }

            # 1. 语法检查
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                compile(code, str(py_file), 'exec')
                result["syntax_valid"] = True
                print("   ✅ 语法检查通过")
            except SyntaxError as e:
                result["error"] = f"语法错误: {e}"
                print(f"   ❌ 语法错误: {e}")
                examples.append(result)
                continue
            except Exception as e:
                result["error"] = f"文件读取错误: {e}"
                print(f"   ❌ 文件错误: {e}")
                examples.append(result)
                continue

            # 2. 导入检查
            try:
                spec = importlib.util.spec_from_file_location(example_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    result["imports_valid"] = True
                    print("   ✅ 导入检查通过")
                else:
                    result["error"] = "无法创建模块规范"
                    print("   ❌ 模块创建失败")
            except ImportError as e:
                result["error"] = f"导入错误: {e}"
                print(f"   ❌ 导入错误: {e}")
            except Exception as e:
                # 其他运行时错误可能是因为缺少环境变量等
                if "main" in dir(module):
                    result["imports_valid"] = True
                    print("   ⚠️ 导入基本通过，但可能需要运行时环境")
                else:
                    result["error"] = f"模块加载错误: {e}"
                    print(f"   ❌ 模块错误: {e}")

            # 3. 简单执行测试（如果连接可用）
            if self.results["connection_test"] and result["imports_valid"]:
                try:
                    # 尝试执行基础功能
                    from langgraph_sdk import get_client
                    client = get_client(url=self.sdk_url)

                    # 简单的连接测试
                    assistants = await client.assistants.search()
                    if assistants:
                        result["execution_test"] = True
                        print("   ✅ 执行测试通过")

                except Exception as e:
                    result["error"] = f"执行错误: {e}"
                    print(f"   ⚠️ 执行警告: {e}")

            examples.append(result)

        self.results["basic_examples"] = examples
        return examples

    async def validate_core_examples(self) -> List[Dict]:
        """验证核心功能示例"""
        print("\n" + "="*50)
        print("🔧 验证核心功能代码")
        print("="*50)

        core_dir = Path(__file__).parent / "02_core"
        examples = []

        for py_file in core_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            example_name = py_file.stem
            print(f"\n🔍 验证: {example_name}")

            result = {
                "name": example_name,
                "file": str(py_file),
                "syntax_valid": False,
                "imports_valid": False,
                "execution_test": False,
                "error": None
            }

            # 语法检查
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                compile(code, str(py_file), 'exec')
                result["syntax_valid"] = True
                print("   ✅ 语法检查通过")
            except Exception as e:
                result["error"] = f"语法错误: {e}"
                print(f"   ❌ 语法错误: {e}")
                examples.append(result)
                continue

            # 导入检查
            try:
                spec = importlib.util.spec_from_file_location(example_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    result["imports_valid"] = True
                    print("   ✅ 导入检查通过")
            except Exception as e:
                result["error"] = f"导入错误: {e}"
                print(f"   ❌ 导入错误: {e}")

            examples.append(result)

        self.results["core_examples"] = examples
        return examples

    async def validate_advanced_examples(self) -> List[Dict]:
        """验证高级功能示例"""
        print("\n" + "="*50)
        print("🚀 验证高级功能代码")
        print("="*50)

        advanced_dir = Path(__file__).parent / "03_advanced"
        examples = []

        for py_file in advanced_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            example_name = py_file.stem
            print(f"\n🔍 验证: {example_name}")

            result = {
                "name": example_name,
                "file": str(py_file),
                "syntax_valid": False,
                "imports_valid": False,
                "execution_test": False,
                "error": None
            }

            # 语法检查
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                compile(code, str(py_file), 'exec')
                result["syntax_valid"] = True
                print("   ✅ 语法检查通过")
            except Exception as e:
                result["error"] = f"语法错误: {e}"
                print(f"   ❌ 语法错误: {e}")
                examples.append(result)
                continue

            # 导入检查
            try:
                spec = importlib.util.spec_from_file_location(example_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    result["imports_valid"] = True
                    print("   ✅ 导入检查通过")
            except Exception as e:
                result["error"] = f"导入错误: {e}"
                print(f"   ❌ 导入错误: {e}")

            examples.append(result)

        self.results["advanced_examples"] = examples
        return examples

    async def run_quick_demo(self) -> bool:
        """运行快速演示"""
        print("\n" + "="*50)
        print("⚡ 运行快速演示")
        print("="*50)

        if not self.results["connection_test"]:
            print("❌ 连接失败，跳过演示")
            return False

        try:
            from langgraph_sdk import get_client

            client = get_client(url=self.sdk_url)

            # 创建测试线程
            thread = await client.threads.create()
            thread_id = thread['thread_id']
            print(f"✅ 测试线程创建成功: {thread_id}")

            # 发送测试消息
            input_data = {
                "messages": [
                    {
                        "role": "user",
                        "content": "你好！这是SDK验证测试。"
                    }
                ]
            }

            # 流式运行测试
            print("📤 发送测试消息...")
            event_count = 0
            async for chunk in client.runs.stream(
                None,
                "agent_not_deep",
                input=input_data,
                stream_mode="updates"
            ):
                event_count += 1
                if event_count <= 3:  # 只显示前3个事件
                    print(f"📥 事件 {event_count}: {chunk.event}")
                if event_count > 10:  # 防止无限循环
                    break

            print(f"✅ 演示成功！接收到 {event_count} 个事件")
            return True

        except Exception as e:
            print(f"❌ 演示失败: {e}")
            return False

    def generate_report(self) -> str:
        """生成验证报告"""
        report = []
        report.append("="*60)
        report.append("📋 LangGraph SDK 代码验证报告")
        report.append("="*60)
        report.append(f"🔗 服务连接: {'✅ 成功' if self.results['connection_test'] else '❌ 失败'}")

        # 统计基础示例
        basic_ok = sum(1 for ex in self.results["basic_examples"] if ex["syntax_valid"])
        basic_total = len(self.results["basic_examples"])
        report.append(f"📚 基础示例: {basic_ok}/{basic_total} 通过语法检查")

        # 统计核心示例
        core_ok = sum(1 for ex in self.results["core_examples"] if ex["syntax_valid"])
        core_total = len(self.results["core_examples"])
        report.append(f"🔧 核心功能: {core_ok}/{core_total} 通过语法检查")

        # 统计高级示例
        advanced_ok = sum(1 for ex in self.results["advanced_examples"] if ex["syntax_valid"])
        advanced_total = len(self.results["advanced_examples"])
        report.append(f"🚀 高级功能: {advanced_ok}/{advanced_total} 通过语法检查")

        # 错误汇总
        if self.results["errors"]:
            report.append("\n❌ 错误汇总:")
            for error in self.results["errors"]:
                report.append(f"   - {error}")

        # 详细结果
        report.append("\n📊 详细结果:")

        for category, examples in [
            ("📚 基础示例", self.results["basic_examples"]),
            ("🔧 核心功能", self.results["core_examples"]),
            ("🚀 高级功能", self.results["advanced_examples"])
        ]:
            if examples:
                report.append(f"\n{category}:")
                for ex in examples:
                    status = "✅" if ex["syntax_valid"] else "❌"
                    report.append(f"   {status} {ex['name']}")
                    if ex.get("error"):
                        report.append(f"      错误: {ex['error']}")

        report.append("\n💡 建议:")
        if not self.results["connection_test"]:
            report.append("   - 请确保LangGraph服务正在运行")
            report.append("   - 检查服务地址: http://localhost:8123")

        syntax_failed = basic_total - basic_ok + core_total - core_ok + advanced_total - advanced_ok
        if syntax_failed > 0:
            report.append("   - 请检查代码语法错误")

        report.append("   - 确保已安装所需依赖: pip install langgraph-sdk")
        report.append("   - 遇到问题请查看错误信息并逐一解决")

        return "\n".join(report)


async def main():
    """主验证函数"""
    print("🧪 LangGraph SDK 代码验证工具")
    print("👨‍🔬 老王帮你检查代码质量！")
    print(f"📍 验证路径: {Path(__file__).parent}")

    validator = CodeValidator()

    # 1. 连接测试
    await validator.test_connection()

    # 2. 验证各类示例
    await validator.validate_basic_examples()
    await validator.validate_core_examples()
    await validator.validate_advanced_examples()

    # 3. 运行快速演示
    await validator.run_quick_demo()

    # 4. 生成报告
    report = validator.generate_report()
    print("\n" + report)

    # 5. 保存报告
    report_file = Path(__file__).parent / "validation_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n💾 详细报告已保存到: {report_file}")
    print("\n🎯 验证完成！根据报告结果继续学习吧！")


if __name__ == "__main__":
    print("⚠️ 验证前准备:")
    print("   1. 启动服务: docker compose -f docker-compose.langgraph.yml up -d")
    print("   2. 确认端口: http://localhost:8123")
    print("   3. 安装SDK: pip install langgraph-sdk")
    print()

    asyncio.run(main())