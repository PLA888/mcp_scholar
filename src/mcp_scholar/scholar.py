from bs4 import BeautifulSoup
import httpx
from scholarly import scholarly  # 新增导入


async def search_scholar(query: str, count: int) -> list[dict]:
    """使用scholarly库搜索谷歌学术论文"""
    results = []
    try:
        # 使用scholarly库进行搜索
        search_query = scholarly.search_pubs(query)

        for _ in range(count):
            try:
                pub = next(search_query)
                # 提取相关信息
                results.append(
                    {
                        "title": pub.get("bib", {}).get("title", "未知标题"),
                        "authors": ", ".join(pub.get("bib", {}).get("author", [])),
                        "abstract": pub.get("bib", {}).get("abstract", "无摘要"),
                        "citations": pub.get("num_citations", 0),
                        "year": pub.get("bib", {}).get("pub_year", "未知年份"),
                        "paper_id": (
                            pub.get("pub_url", "").split("citation_for_view=")[-1]
                            if "citation_for_view=" in pub.get("pub_url", "")
                            else None
                        ),
                    }
                )
            except StopIteration:
                break
            except Exception as e:
                print(f"处理单篇论文时出错: {str(e)}")
                continue

        return sorted(results, key=lambda x: -x["citations"])
    except Exception as e:
        print(f"搜索谷歌学术时出错: {str(e)}")
        return []


async def parse_profile(profile_id: str, top_n: int) -> list[dict]:
    """使用scholarly库解析谷歌学术个人主页"""
    try:
        # 通过ID查找作者
        author = scholarly.search_author_id(profile_id)
        if not author:
            print(f"未找到ID为{profile_id}的学者")
            return []

        # 获取完整信息
        author = scholarly.fill(author)

        # 获取发表的论文
        publications = author.get("publications", [])
        papers = []

        for pub in publications[:top_n]:
            try:
                # 获取详细信息
                filled_pub = scholarly.fill(pub)
                papers.append(
                    {
                        "title": filled_pub.get("bib", {}).get("title", "未知标题"),
                        "authors": ", ".join(
                            filled_pub.get("bib", {}).get("author", [])
                        ),
                        "citations": filled_pub.get("num_citations", 0),
                        "year": filled_pub.get("bib", {}).get("pub_year", "未知年份"),
                        "venue": filled_pub.get("bib", {}).get("venue", ""),
                        "paper_id": (
                            filled_pub.get("pub_url", "").split("citation_for_view=")[
                                -1
                            ]
                            if "citation_for_view=" in filled_pub.get("pub_url", "")
                            else None
                        ),
                    }
                )
            except Exception as e:
                print(f"处理单篇论文时出错: {str(e)}")
                continue

        # 按引用数排序
        papers = sorted(papers, key=lambda x: -x["citations"])
        return papers[:top_n]
    except Exception as e:
        print(f"解析学者档案时出错: {str(e)}")
        return []


# 增加一个新函数，用于从URL中提取学者ID
def extract_profile_id_from_url(url: str) -> str:
    """从谷歌学术个人主页URL中提取学者ID"""
    import re

    match = re.search(r"user=([^&]+)", url)
    if match:
        return match.group(1)
    return ""
