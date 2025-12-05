#!/usr/bin/env python3
"""
LangGraph API Server (Postgres 版)

通过环境变量提供 Postgres/Redis 配置，不使用自定义 checkpointer。
示例：
  POSTGRES_URI="postgresql://user:pass@host:5432/db?sslmode=disable" \
  REDIS_URI="redis://localhost:6379" \
  python start_server_by_pg.py
"""

import os
import sys
import json
from pathlib import Path


def setup_environment():
    """Setup required environment variables for Postgres backend."""
    # Add src to Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))

    # Load .env first (用户配置优先)
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print("✅ Loaded environment from .env")
        except ImportError:
            print("⚠️ python-dotenv not installed, skipping .env file")

    # Load graphs from graph.json
    config_path = Path(__file__).parent / "graph.json"
    graphs = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            graphs = config.get("graphs", {})

    # Require POSTGRES_URI and REDIS_URI to be set in env/.env
    required = ["POSTGRES_URI", "REDIS_URI"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {missing}. "
            "Please set POSTGRES_URI (e.g., postgresql://user:pass@host:5432/db?sslmode=disable) "
            "and REDIS_URI (e.g., redis://localhost:6379)."
        )

    defaults = {
        # Use Postgres as DATABASE_URI
        "DATABASE_URI": os.getenv("POSTGRES_URI"),
        # Migrations path can stay in-memory for local dev
        "MIGRATIONS_PATH": "__inmem",
        # Server configuration
        "ALLOW_PRIVATE_NETWORK": "true",
        "LANGGRAPH_UI_BUNDLER": "true",
        # 使用 postgres runtime
        "LANGGRAPH_RUNTIME_EDITION": "postgres",
        "LANGSMITH_LANGGRAPH_API_VARIANT": "local_dev",
        "LANGGRAPH_DISABLE_FILE_PERSISTENCE": "true",
        "LANGGRAPH_ALLOW_BLOCKING": "true",
        "LANGGRAPH_API_URL": "http://localhost:2025",
        "LANGGRAPH_DEFAULT_RECURSION_LIMIT": "200",
        # Graphs configuration
        "LANGSERVE_GRAPHS": json.dumps(graphs) if graphs else "{}",
        # Worker configuration
        "N_JOBS_PER_WORKER": "1",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)


def main():
    """Start the server with Postgres backend."""
    print("🚀 Starting LangGraph API Server (Postgres)...")

    # Setup environment
    setup_environment()

    # Print server information
    print("\n" + "=" * 60)
    print("📍 Server URL: http://localhost:2025")
    print("📚 API Documentation: http://localhost:2025/docs")
    print("🎨 Studio UI: http://localhost:2025/ui")
    print("💚 Health Check: http://localhost:2025/ok")
    print("=" * 60)

    try:
        import uvicorn

        uvicorn.run(
            "langgraph_api.server:app",
            host="0.0.0.0",
            port=2025,
            reload=True,
            access_log=False,
            log_config={
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    }
                },
                "handlers": {
                    "default": {
                        "formatter": "default",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                    }
                },
                "root": {
                    "level": "INFO",
                    "handlers": ["default"],
                },
                "loggers": {
                    "uvicorn": {"level": "INFO"},
                    "uvicorn.error": {"level": "INFO"},
                    "uvicorn.access": {"level": "WARNING"},
                },
            },
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
