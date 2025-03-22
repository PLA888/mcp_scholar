import asyncio
import os
import httpx
from mcp_scholar.scholar import (
    search_scholar,
    parse_profile,
    extract_profile_id_from_url,
    convert_inverted_index_to_text,
    convert_google_scholar_to_openalex,  # 导入新函数
    get_paper_references,  # 导入引用函数
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
        print(f"摘要: {paper['abstract']}")
        print(f"引用次数: {paper['citations']}")


async def test_parse_real_profile():
    print("\n测试解析OpenAlex学者档案...")
    # 使用一个OpenAlex作者ID作为测试
    profile_id = "A2208157607"  # OpenAlex上的一个作者ID

    try:
        # 解析个人主页
        papers = await parse_profile(profile_id, top_n=5)

        print(f"解析出 {len(papers)} 篇最高引用论文:")
        for i, paper in enumerate(papers, 1):
            print(f"\n论文 {i}:")
            print(f"标题: {paper['title']}")
            print(f"引用: {paper['citations']}")
            print(
                f"摘要: {paper['abstract'][:150]}..."
                if len(paper["abstract"]) > 150
                else paper["abstract"]
            )
            print(f"年份: {paper.get('year', 'N/A')}")
            if "authors" in paper:
                print(f"作者: {paper['authors']}")
            if "venue" in paper:
                print(f"发表于: {paper['venue']}")

    except Exception as e:
        print(f"解析时出错: {e}")


async def test_inverted_index_conversion():
    print("\n测试倒排索引转换函数...")
    # 示例倒排索引
    inverted_index = {"这是": [0], "一个": [1], "测试": [2], "示例": [3]}
    text = convert_inverted_index_to_text(inverted_index)
    print(f"转换结果: {text}")

    # 空索引测试
    empty_text = convert_inverted_index_to_text({})
    print(f"空索引转换结果: '{empty_text}'")


async def test_google_scholar_profile():
    print("\n测试从谷歌学术主页解析学者信息...")
    # 使用一个知名学者的谷歌学术页面URL作为示例
    # 这里使用Andrew Ng的谷歌学术主页作为例子
    google_scholar_url = "https://scholar.google.com/citations?user=mG4imMEAAAAJ"

    # 从URL提取ID
    profile_id = extract_profile_id_from_url(google_scholar_url)

    if profile_id and profile_id.startswith("google:"):
        try:
            print(f"从URL中提取的谷歌学术ID: {profile_id}")

            # 解析个人主页（内部会自动转换为OpenAlex ID）
            papers = await parse_profile(profile_id, top_n=3)

            print(f"解析出 {len(papers)} 篇最高引用论文:")
            for i, paper in enumerate(papers, 1):
                print(f"\n论文 {i}:")
                print(f"标题: {paper['title']}")
                print(f"引用: {paper['citations']}")
                print(
                    f"摘要: {paper['abstract'][:]}..."
                    if len(paper.get("abstract", "")) > 150
                    else paper.get("abstract", "无摘要")
                )
                print(f"年份: {paper.get('year', 'N/A')}")
                if "authors" in paper:
                    print(f"作者: {paper['authors']}")
                if "venue" in paper:
                    print(f"发表于: {paper['venue']}")
        except Exception as e:
            print(f"解析谷歌学术主页时出错: {e}")
    else:
        print(f"无法从URL提取有效的谷歌学术ID: {google_scholar_url}")


async def test_papers_by_year():
    print("\n测试按年份筛选论文...")
    # 使用OpenAlex作者ID
    profile_id = "A2208157607"

    try:
        # 只获取2018年之后的论文
        papers = await parse_profile(profile_id, top_n=5, min_year=2018)

        print(f"找到 {len(papers)} 篇2018年之后的论文:")
        for i, paper in enumerate(papers, 1):
            print(f"\n论文 {i}:")
            print(f"标题: {paper['title']}")
            print(f"引用: {paper['citations']}")
            print(f"年份: {paper.get('year', 'N/A')}")

        # 测试年份范围
        papers = await parse_profile(profile_id, top_n=5, min_year=2015, max_year=2020)

        print(f"\n找到 {len(papers)} 篇2015-2020年间的论文:")
        for i, paper in enumerate(papers, 1):
            print(f"\n论文 {i}:")
            print(f"标题: {paper['title']}")
            print(f"引用: {paper['citations']}")
            print(f"年份: {paper.get('year', 'N/A')}")

    except Exception as e:
        print(f"按年份筛选论文时出错: {e}")


async def test_papers_without_citation_sort():
    print("\n测试不按引用次数排序的论文...")
    # 使用OpenAlex作者ID
    profile_id = "A2208157607"

    try:
        # 按发表年份排序（降序）- 修正为新的排序参数
        papers = await parse_profile(profile_id, top_n=5, sort_by="date")

        print(f"按发表日期排序的 {len(papers)} 篇论文:")
        for i, paper in enumerate(papers, 1):
            print(f"\n论文 {i}:")
            print(f"标题: {paper['title']}")
            print(f"引用: {paper['citations']}")
            print(f"年份: {paper.get('year', 'N/A')}")

        # 按标题字母顺序排序
        papers = await parse_profile(profile_id, top_n=5, sort_by="title")

        print(f"\n按标题排序的 {len(papers)} 篇论文:")
        for i, paper in enumerate(papers, 1):
            print(f"\n论文 {i}:")
            print(f"标题: {paper['title']}")
            print(f"引用: {paper['citations']}")
            print(f"年份: {paper.get('year', 'N/A')}")

    except Exception as e:
        print(f"使用非引用排序时出错: {e}")


async def test_all_sorting_methods():
    """测试所有可用的排序方式"""
    print("\n===== 测试所有排序方式 =====")

    # 1. 测试search_scholar的排序
    print("\n1. 测试search_scholar的排序方式:")
    query = "artificial intelligence"

    for sort_by in ["relevance", "citations", "date", "title"]:
        print(f"\n--- 使用 {sort_by} 排序搜索结果 ---")
        results = await search_scholar(query, 3, sort_by=sort_by)

        print(f"找到 {len(results)} 篇论文:")
        for i, paper in enumerate(results, 1):
            print(f"论文 {i}: {paper['title']}")
            if sort_by == "citations":
                print(f"引用量: {paper['citations']}")
            elif sort_by == "date":
                print(f"发表年份: {paper['year']}")

    # 2. 测试get_paper_references的排序
    print("\n2. 测试get_paper_references的排序方式:")
    # 使用一个知名论文ID (GPT-3论文)
    paper_id = "W3098397289"

    for sort_by in ["relevance", "citations", "date", "title"]:
        print(f"\n--- 使用 {sort_by} 排序引用论文 ---")
        refs = await get_paper_references(paper_id, 3, sort_by=sort_by)

        print(f"找到 {len(refs)} 篇引用论文:")
        for i, ref in enumerate(refs, 1):
            print(f"论文 {i}: {ref['title']}")
            if sort_by == "citations":
                print(f"引用量: {ref['citations']}")
            elif sort_by == "date":
                print(f"发表年份: {ref['year']}")

    # 3. 测试parse_profile的排序
    print("\n3. 测试parse_profile的排序方式:")
    profile_id = "A2208157607"  # 使用一个OpenAlex作者ID

    for sort_by in ["relevance", "citations", "date", "title"]:
        print(f"\n--- 使用 {sort_by} 排序作者论文 ---")
        papers = await parse_profile(profile_id, 3, sort_by=sort_by)

        print(f"找到 {len(papers)} 篇作者论文:")
        for i, paper in enumerate(papers, 1):
            print(f"论文 {i}: {paper['title']}")
            if sort_by == "citations":
                print(f"引用量: {paper['citations']}")
            elif sort_by == "date":
                print(f"发表年份: {paper['year']}")


async def main():
    # await test_search_scholar()
    # await test_inverted_index_conversion()
    # await test_parse_real_profile()
    # await test_google_scholar_profile()
    # await test_papers_by_year()
    # await test_papers_without_citation_sort()

    # 新增的排序测试
    await test_all_sorting_methods()


if __name__ == "__main__":
    print("开始测试 mcp_scholar 模块...")
    asyncio.run(main())
    print("\n测试完成!")
