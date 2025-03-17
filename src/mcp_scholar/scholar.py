"""
谷歌学术搜索和解析功能
使用 scholarly 库与谷歌学术交互
"""

import re
import httpx
import asyncio
from scholarly import scholarly
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

# 配置 scholarly 的代理，如果需要的话
# scholarly.use_proxy(http="http://127.0.0.1:7890", https="http://127.0.0.1:7890")


async def enrich_abstract(paper: Dict[str, Any]) -> Dict[str, Any]:
    """
    尝试从多个来源获取更完整的论文摘要

    Args:
        paper: 包含基本信息的论文字典

    Returns:
        Dict: 添加了完整摘要的论文信息
    """
    title = paper.get("title", "")
    if not title:
        return paper

    try:
        # 1. 尝试从 Semantic Scholar 获取摘要
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 使用论文标题搜索
            params = {"query": title, "limit": 1}
            response = await client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search", params=params
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    paper_id = data["data"][0]["paperId"]

                    # 获取论文详情
                    fields = "title,abstract,authors,year,citationCount,venue"
                    paper_response = await client.get(
                        f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields={fields}"
                    )

                    if paper_response.status_code == 200:
                        paper_details = paper_response.json()
                        if paper_details.get("abstract") and len(
                            paper_details["abstract"]
                        ) > len(paper.get("abstract", "")):
                            paper["abstract"] = paper_details["abstract"]
                            paper["abstract_source"] = "Semantic Scholar"
                            return paper

        # 2. 尝试从 Crossref 获取摘要
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {"query.title": title, "rows": 1}
            response = await client.get("https://api.crossref.org/works", params=params)

            if response.status_code == 200:
                data = response.json()
                if (
                    data.get("message", {}).get("items")
                    and len(data["message"]["items"]) > 0
                ):
                    item = data["message"]["items"][0]
                    if item.get("abstract") and len(item["abstract"]) > len(
                        paper.get("abstract", "")
                    ):
                        # 移除 XML/HTML 标签
                        abstract = BeautifulSoup(
                            item["abstract"], "html.parser"
                        ).get_text()
                        paper["abstract"] = abstract
                        paper["abstract_source"] = "Crossref"
                        return paper

        # 3. 如果有 DOI，尝试从 Unpaywall 获取
        if paper.get("doi"):
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://api.unpaywall.org/v2/{paper['doi']}?email=your_email@example.com"
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("abstract") and len(data["abstract"]) > len(
                        paper.get("abstract", "")
                    ):
                        paper["abstract"] = data["abstract"]
                        paper["abstract_source"] = "Unpaywall"
                        return paper

        # 在这里可以继续添加其他学术 API 的尝试...

    except Exception as e:
        print(f"丰富摘要时出错: {str(e)}")

    # 如果没有找到更完整的摘要，返回原始论文
    return paper


async def search_scholar(query: str, count: int = 5) -> List[Dict[str, Any]]:
    """
    搜索谷歌学术论文，并尝试获取完整摘要

    Args:
        query: 搜索关键词
        count: 返回结果数量

    Returns:
        List[Dict]: 论文信息列表，按引用量排序
    """
    results = []
    try:
        # 使用scholarly库进行搜索
        search_query = scholarly.search_pubs(query)

        for _ in range(count):
            try:
                pub = next(search_query)

                # 提取论文信息
                paper = {
                    "title": pub.get("bib", {}).get("title", "未知标题"),
                    "authors": ", ".join(pub.get("bib", {}).get("author", [])),
                    "abstract": pub.get("bib", {}).get("abstract", "无摘要"),
                    "citations": pub.get("num_citations", 0),
                    "year": pub.get("bib", {}).get("pub_year", "未知年份"),
                    "venue": pub.get("bib", {}).get("venue", ""),
                }

                # 提取论文ID
                pub_url = pub.get("pub_url", "")
                if "citation_for_view=" in pub_url:
                    paper["paper_id"] = pub_url.split("citation_for_view=")[-1]
                elif "cluster=" in pub_url:
                    paper["paper_id"] = pub_url.split("cluster=")[-1].split("&")[0]
                else:
                    paper["paper_id"] = None

                # 提取 DOI（如果有）
                if pub.get("doi"):
                    paper["doi"] = pub["doi"]

                # 尝试获取完整摘要
                paper = await enrich_abstract(paper)

                results.append(paper)

                # 添加延迟以避免被谷歌限制
                await asyncio.sleep(1)

            except StopIteration:
                break
            except Exception as e:
                print(f"处理单篇论文时出错: {str(e)}")
                continue

        return sorted(results, key=lambda x: -x["citations"])
    except Exception as e:
        print(f"搜索谷歌学术时出错: {str(e)}")
        return []


async def get_paper_detail(paper_id: str) -> Optional[Dict[str, Any]]:
    """
    获取论文详情

    Args:
        paper_id: 论文ID

    Returns:
        Dict: 论文详细信息
    """
    try:
        # 尝试通过ID获取论文详情
        if ":" in paper_id:  # 可能是DOI或其他标识符
            # 使用scholarly的方式搜索特定论文
            query = f"source:{paper_id}"
            search_query = scholarly.search_pubs(query)
            try:
                pub = next(search_query)
                pub = scholarly.fill(pub)
            except StopIteration:
                return None
        else:
            # 尝试通过聚类ID查找
            url = f"https://scholar.google.com/scholar?cluster={paper_id}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()

                # 这里需要解析返回的HTML页面，比较复杂
                # 建议使用scholarly的工具
                return None

        # 提取详细信息
        return {
            "title": pub.get("bib", {}).get("title", "未知标题"),
            "authors": ", ".join(pub.get("bib", {}).get("author", [])),
            "abstract": pub.get("bib", {}).get("abstract", "无摘要"),
            "citations": pub.get("num_citations", 0),
            "year": pub.get("bib", {}).get("pub_year", "未知年份"),
            "venue": pub.get("bib", {}).get("venue", ""),
            "paper_id": paper_id,
            "url": pub.get("pub_url", ""),
            "citation_url": (
                pub.get("cites_id", {}).get("link", "") if pub.get("cites_id") else ""
            ),
        }
    except Exception as e:
        print(f"获取论文详情时出错: {str(e)}")
        return None


async def get_paper_references(paper_id: str, count: int = 5) -> List[Dict[str, Any]]:
    """
    获取引用指定论文的文献

    Args:
        paper_id: 论文ID
        count: 返回结果数量

    Returns:
        List[Dict]: 引用论文信息列表
    """
    results = []
    try:
        # 通过ID获取论文的引用
        if ":" in paper_id:  # 可能是DOI或其他标识符
            query = f"cite:{paper_id}"
        else:
            query = f"cites={paper_id}"

        search_query = scholarly.search_pubs(query)

        for _ in range(count):
            try:
                pub = next(search_query)

                paper = {
                    "title": pub.get("bib", {}).get("title", "未知标题"),
                    "authors": ", ".join(pub.get("bib", {}).get("author", [])),
                    "abstract": pub.get("bib", {}).get("abstract", "无摘要"),
                    "citations": pub.get("num_citations", 0),
                    "year": pub.get("bib", {}).get("pub_year", "未知年份"),
                    "venue": pub.get("bib", {}).get("venue", ""),
                }

                # 提取论文ID
                pub_url = pub.get("pub_url", "")
                if "citation_for_view=" in pub_url:
                    paper["paper_id"] = pub_url.split("citation_for_view=")[-1]
                elif "cluster=" in pub_url:
                    paper["paper_id"] = pub_url.split("cluster=")[-1].split("&")[0]
                else:
                    paper["paper_id"] = None

                results.append(paper)

                # 添加延迟以避免被谷歌限制
                await asyncio.sleep(1)

            except StopIteration:
                break
            except Exception as e:
                print(f"处理引用论文时出错: {str(e)}")
                continue

        return sorted(results, key=lambda x: -x["citations"])
    except Exception as e:
        print(f"获取论文引用时出错: {str(e)}")
        return []


async def parse_profile(profile_id: str, top_n: int = 5) -> List[Dict[str, Any]]:
    """
    解析谷歌学术个人主页

    Args:
        profile_id: 学者ID
        top_n: 返回结果数量

    Returns:
        List[Dict]: 论文信息列表
    """
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

        for pub in publications[
            : min(len(publications), top_n * 2)
        ]:  # 获取更多论文，以防有些无法填充
            try:
                # 获取详细信息
                filled_pub = scholarly.fill(pub)

                paper = {
                    "title": filled_pub.get("bib", {}).get("title", "未知标题"),
                    "authors": ", ".join(filled_pub.get("bib", {}).get("author", [])),
                    "citations": filled_pub.get("num_citations", 0),
                    "year": filled_pub.get("bib", {}).get("pub_year", "未知年份"),
                    "venue": filled_pub.get("bib", {}).get("venue", ""),
                    "abstract": filled_pub.get("bib", {}).get("abstract", "无摘要"),
                }

                # 提取论文ID
                pub_url = filled_pub.get("pub_url", "")
                if "citation_for_view=" in pub_url:
                    paper["paper_id"] = pub_url.split("citation_for_view=")[-1]
                elif "cluster=" in pub_url:
                    paper["paper_id"] = pub_url.split("cluster=")[-1].split("&")[0]
                else:
                    paper["paper_id"] = None

                papers.append(paper)

                # 添加延迟以避免被谷歌限制
                await asyncio.sleep(1)

            except Exception as e:
                print(f"处理作者论文时出错: {str(e)}")
                continue

        # 按引用数排序
        papers = sorted(papers, key=lambda x: -x["citations"])
        return papers[:top_n]
    except Exception as e:
        print(f"解析学者档案时出错: {str(e)}")
        return []


def extract_profile_id_from_url(url: str) -> str:
    """
    从谷歌学术个人主页URL中提取学者ID

    Args:
        url: 谷歌学术个人主页URL

    Returns:
        str: 学者ID
    """
    match = re.search(r"user=([^&]+)", url)
    if match:
        return match.group(1)
    return ""
