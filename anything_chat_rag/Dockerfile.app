FROM lijiaxin8187/langgraph-base:3.13-wolfi

# Add project code
ADD . /deps/anything_chat_rag

# 清理基础镜像里无代码的占位目录，避免装失败
RUN rm -rf /deps/langgraph_teach || true

# 仅安装当前项目（可编辑模式），复用基础镜像的 Python 依赖
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir -c /api/constraints.txt -e /deps/anything_chat_rag

# Configure graph entry
ENV LANGSERVE_GRAPHS='{"agent": "/deps/anything_chat_rag/src/anything_rag_server/agent_rag_async.py:agent"}'

# Ensure langgraph-api not overwritten
RUN mkdir -p /api/langgraph_api /api/langgraph_runtime /api/langgraph_license && \
    touch /api/langgraph_api/__init__.py /api/langgraph_runtime/__init__.py /api/langgraph_license/__init__.py && \
    PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir --no-deps -e /api

# Remove build-time packaging tools for a slimmer runtime
RUN pip uninstall -y pip setuptools wheel || true
RUN rm -rf /usr/local/lib/python*/site-packages/pip* /usr/local/lib/python*/site-packages/setuptools* /usr/local/lib/python*/site-packages/wheel* && find /usr/local/bin -name "pip*" -delete || true
RUN rm -rf /usr/lib/python*/site-packages/pip* /usr/lib/python*/site-packages/setuptools* /usr/lib/python*/site-packages/wheel* && find /usr/bin -name "pip*" -delete || true
RUN uv pip uninstall --system pip setuptools wheel || true && rm /usr/bin/uv /usr/bin/uvx || true

WORKDIR /deps/anything_chat_rag
