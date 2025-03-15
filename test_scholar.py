import asyncio
import os
import httpx
from mcp_scholar.scholar import (
    search_scholar,
    parse_profile,
    extract_profile_id_from_url,
)


async def test_search_scholar():
    print("测试 search_scholar 函数...")
    # 搜索关于人工智能的论文，获取前3篇
    results = await search_scholar("artificial intelligence", 3)
    print(f"找到 {len(results)} 篇论文:")
    for i, paper in enumerate(results, 1):
        print(f"\n论文 {i}:")
        print(f"标题: {paper['title']}")
        print(f"作者: {paper['authors']}")
        print(f"摘要: {paper['abstract']}...")
        print(f"引用次数: {paper['citations']}")


async def test_parse_real_profile():
    print("\n测试解析真实谷歌学术个人主页...")
    url = "https://scholar.google.com/citations?user=SJdlvnQAAAAJ&hl=en"
    profile_id = extract_profile_id_from_url(url)  # 提取 SJdlvnQAAAAJ

    async with httpx.AsyncClient() as client:
        try:
            # 发送请求获取页面内容
            response = await client.get(url)
            response.raise_for_status()  # 确保请求成功

            # 解析个人主页
            papers = await parse_profile(profile_id, top_n=5)

            print(f"解析出 {len(papers)} 篇最高引用论文:")
            for i, paper in enumerate(papers, 1):
                print(f"\n论文 {i}:")
                print(f"标题: {paper['title']}")
                print(f"引用: {paper['citations']}")
                print(f"年份: {paper.get('year', 'N/A')}")
                if "authors" in paper:
                    print(f"作者: {paper['authors']}")
                if "venue" in paper:
                    print(f"发表于: {paper['venue']}")

        except httpx.HTTPError as e:
            print(f"HTTP错误: {e}")
        except Exception as e:
            print(f"解析时出错: {e}")



async def main():
    await test_search_scholar()  # 可能触发谷歌限制，可选择性注释
    # await test_parse_real_profile()  # 真实数据测试


if __name__ == "__main__":
    print("开始测试 mcp_scholar 模块...")
    asyncio.run(main())
    print("\n测试完成!")
