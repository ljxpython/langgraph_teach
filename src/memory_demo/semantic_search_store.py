"""内存 Store 语义搜索示例（使用简易 embedding 函数）。

用 InMemoryStore 配置 index，演示基于 query 的相似搜索。
"""

from langgraph.store.memory import InMemoryStore


def embed(texts: list[str]) -> list[list[float]]:
    # 简易向量：按字符长度生成二维向量，便于无网络运行
    return [[len(t), len(t) % 7] for t in texts]


def run_demo() -> None:
    store = InMemoryStore(index={"embed": embed, "dims": 2})
    ns = ("user_123", "memories")
    store.put(ns, "1", {"text": "我喜欢披萨"})
    store.put(ns, "2", {"text": "我是水管工"})

    items = store.search(ns, query="我饿了", limit=1)
    print("语义搜索结果：", [item.value for item in items])


if __name__ == "__main__":
    run_demo()
