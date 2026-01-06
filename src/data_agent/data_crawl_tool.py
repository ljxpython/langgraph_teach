import asyncio
from crawl4ai import *
import httpx

async def main():
    async with AsyncWebCrawler() as crawler:
        # 配置爬虫，提取包含 server-api 的链接
        # config = CrawlerRunConfig(
        #     # 启用链接预览和评分
        #     link_preview_config=LinkPreviewConfig(
        #         include_internal=True,  # 提取内部链接
        #         include_external=False,  # 跳过外部链接
        #         max_links=50,  # 最多处理 50 个链接
        #         concurrency=5,  # 同时处理 5 个链接
        #         timeout=10,  # 每个链接 10 秒超时
        #         verbose=True,  # 显示详细进度
        #         # 只处理包含 server-api 的链接
        #         include_patterns=[
        #             "*server-api*",  # 匹配任何包含 server-api 的 URL
        #         ],
        #     ),
        #     # 启用链接评分
        #     score_links=True,
        #     # 只保留文本内容
        #     only_text=True,
        #     verbose=True
        # )

        result = await crawler.arun(
            url="https://www.fecmall.com/doc/fecshop-guide/develop/cn-2.0/guide-README.html",
            # config=config
        )

        # 提取并显示包含 server-api 的链接
        if result.success:
            internal_links = result.links.get("internal", [])

            # 过滤包含 server-api 的链接
            server_api_links = [
                link for link in internal_links
                if "server-api" in link.get("href", "").lower()
            ]

            print(f"✅ 爬取成功: {result.url}")
            print(f"📊 找到 {len(internal_links)} 个内部链接")
            print(f"🎯 找到 {len(server_api_links)} 个包含 server-api 的链接\n")

            # 显示所有 server-api 链接
            print("=" * 80)
            print("包含 server-api 的链接列表:")
            print("=" * 80)
            for i, link in enumerate(server_api_links, 1):
                print(f"\n{i}. URL: {link.get('href', 'N/A')}")
                print(f"   文本: {link.get('text', 'N/A')[:100]}")
                print(f"   标题: {link.get('title', 'N/A')[:100]}")

                # 如果有评分信息，显示评分
                if link.get('total_score'):
                    print(f"   总分: {link.get('total_score'):.3f}")
                if link.get('intrinsic_score'):
                    print(f"   内在分: {link.get('intrinsic_score'):.2f}/10.0")

                result = await crawler.arun(
                    url=link.get('href', 'N/A'),
                    # config=config
                )
                print(result.markdown)

                # 应该对当前接口数据进行过滤、清洗

                # 调用接口 POST /documents/text ，完成数据的入库
                rag_api_url = "http://localhost:9621"
                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.post(
                            f"{rag_api_url}/documents/text",
                            json={
                                "file_source": link.get('href', 'N/A'),
                                "text": result.markdown
                            },
                            timeout=30.0
                        )

                        if response.status_code == 200:
                            result_data = response.json()
                            track_id = result_data.get("track_id", "unknown")
                            print(f"✅ 成功插入数据到向量数据库 (track_id: {track_id})")
                        else:
                            print(f"❌ 插入失败: HTTP {response.status_code}")
                    except Exception as e:
                        print(f"❌ 插入数据时发生错误: {str(e)}")


        else:
            print(f"❌ 爬取失败: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
