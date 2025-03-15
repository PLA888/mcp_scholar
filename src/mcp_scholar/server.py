"""
MCP Scholar 服务
提供谷歌学术搜索、论文详情、引用信息和论文总结功能
"""

import logging
import sys
import json
from mcp.server.fastmcp import FastMCP, Context, prompt
from mcp_scholar.scholar import (
    search_scholar,
    get_paper_detail,
    get_paper_references,
    parse_profile,
    extract_profile_id_from_url,
)
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)
# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

# 创建MCP服务器
mcp = FastMCP(
    "ScholarServer",
    dependencies=["scholarly", "httpx", "beautifulsoup4"],
    verbose=True,
    debug=True,
)

# 预设提示词常量
PRESET_SUMMARY_PROMPT = """
分析并总结以下学术论文的内容，请遵循以下结构：

1. **研究概览**：用简明扼要的语言概括所有提供论文的总体研究方向和贡献。
   
2. **主要研究主题**：识别这些论文中出现的关键研究主题和模式，归纳这些主题的发展趋势。
   
3. **研究方法分析**：总结论文中使用的主要研究方法和技术，评估它们的有效性和创新点。
   
4. **重要发现与贡献**：提炼出论文中最重要的科学发现和对该领域的具体贡献。
   
5. **未来研究方向**：基于这些论文的内容，指出该领域可能的未来研究方向和尚未解决的问题。

请确保总结全面、客观、准确，并突出这些论文的学术价值和实际应用意义。对于引用量较高的论文，请给予更多关注。
"""

# 针对学者论文的预设提示词
PROFILE_SUMMARY_PROMPT = """
请对以下学者的高引用论文进行综合分析，包括：

1. **学者研究方向**：基于这些高引用论文，总结该学者的主要研究领域和专长。
   
2. **研究影响力分析**：评估这些论文的学术影响力，特别关注引用量高的工作及其在相关领域的地位。
   
3. **研究发展历程**：按时间顺序分析这些论文，揭示该学者研究兴趣和方法的演变过程。
   
4. **与同行的研究对比**：如果可能，比较该学者的研究与该领域其他重要工作的异同。
   
5. **研究价值与应用**：分析这些研究成果的实际应用价值和对相关产业的潜在影响。

请提供一个全面、客观的学术分析，突出该学者的研究特色和学术贡献。
"""

# 搜索提示词常量
SEARCH_SUMMARY_PROMPT = """
请对以下搜索结果进行详细分析和总结:

1. **文献概述**: 简要概述这些搜索结果的共同主题和各自特点，特别关注最新的研究成果。

2. **研究脉络**: 梳理这些论文反映的研究发展脉络，展示领域内的思想演变过程。

3. **方法论比较**: 比较不同论文采用的研究方法和技术路线，分析各自的优缺点。

4. **核心发现**: 提炼出最具创新性和影响力的研究发现，评估其对该领域的贡献。

5. **应用价值**: 分析这些研究成果的实际应用前景和潜在价值。

6. **研究缺口**: 指出现有研究中的不足之处和未来可能的研究方向。

请根据引用量和发表时间对文献进行适当加权，对高引用的经典文献和最新研究成果给予更多关注。
"""

@mcp.prompt(SEARCH_SUMMARY_PROMPT)
@mcp.tool()
async def scholar_search(ctx: Context, keywords: str, count: int = 5) -> Dict[str, Any]:
    """
    搜索谷歌学术并返回论文摘要

    Args:
        keywords: 搜索关键词
        count: 返回结果数量，默认为5

    Returns:
        Dict: 包含论文列表的字典
    """
    try:
        logger.info(f"正在搜索谷歌学术: {keywords}...")
        results = await search_scholar(keywords, count)

        papers = []
        for p in results:
            papers.append(
                {
                    "title": p["title"],
                    "authors": p["authors"],
                    "abstract": p["abstract"],
                    "citations": p["citations"],
                    "year": p.get("year", "Unknown"),
                    "paper_id": p.get("paper_id", None),
                    "venue": p.get("venue", ""),
                }
            )

        return {"status": "success", "papers": papers}
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}", exc_info=True)
        return {"status": "error", "message": "学术搜索服务暂时不可用", "error": str(e)}


@mcp.tool()
async def paper_detail(ctx: Context, paper_id: str) -> Dict[str, Any]:
    """
    获取论文详细信息

    Args:
        paper_id: 论文ID

    Returns:
        Dict: 论文详细信息
    """
    try:
        # 移除进度显示
        logger.info(f"正在获取论文ID为 {paper_id} 的详细信息...")
        detail = await get_paper_detail(paper_id)

        if detail:
            return {"status": "success", "detail": detail}
        else:
            # 移除错误通知
            logger.warning(f"未找到ID为 {paper_id} 的论文")
            return {"status": "error", "message": f"未找到ID为 {paper_id} 的论文"}
    except Exception as e:
        # 移除错误通知
        logger.error(f"获取论文详情失败: {str(e)}", exc_info=True)
        return {"status": "error", "message": "论文详情服务暂时不可用", "error": str(e)}


@mcp.tool()
async def paper_references(
    ctx: Context, paper_id: str, count: int = 5
) -> Dict[str, Any]:
    """
    获取引用指定论文的文献列表

    Args:
        paper_id: 论文ID
        count: 返回结果数量，默认为5

    Returns:
        Dict: 引用论文列表
    """
    try:
        # 移除进度显示
        logger.info(f"正在获取论文ID为 {paper_id} 的引用...")
        references = await get_paper_references(paper_id, count)

        refs = []
        for ref in references:
            refs.append(
                {
                    "title": ref["title"],
                    "authors": ref["authors"],
                    "abstract": (
                        ref["abstract"][:200] + "..."
                        if len(ref["abstract"]) > 200
                        else ref["abstract"]
                    ),
                    "citations": ref["citations"],
                    "year": ref.get("year", "Unknown"),
                    "paper_id": ref.get("paper_id", None),
                }
            )

        return {"status": "success", "references": refs}
    except Exception as e:
        error_msg = f"获取论文引用失败: {str(e)}"
        # 移除错误通知
        logger.error(error_msg, exc_info=True)
        return {"status": "error", "message": "论文引用服务暂时不可用", "error": str(e)}


@mcp.prompt(PROFILE_SUMMARY_PROMPT)
@mcp.tool()
async def profile_papers(
    ctx: Context, profile_url: str, count: int = 5
) -> Dict[str, Any]:
    """
    获取学者的高引用论文

    Args:
        profile_url: 谷歌学术个人主页URL
        count: 返回结果数量，默认为5

    Returns:
        Dict: 论文列表
    """
    try:
        # 移除进度显示
        logger.info(f"正在解析个人主页 {profile_url}...")
        profile_id = extract_profile_id_from_url(profile_url)

        if not profile_id:
            # 移除错误通知
            logger.error("无法从URL中提取学者ID")
            return {"status": "error", "message": "无法从URL中提取学者ID"}

        papers = await parse_profile(profile_id, count)

        result_papers = []
        for p in papers:
            result_papers.append(
                {
                    "title": p["title"],
                    "authors": p["authors"],
                    "abstract": p["abstract"],
                    "citations": p["citations"],
                    "year": p.get("year", "Unknown"),
                    "venue": p.get("venue", ""),
                    "paper_id": p.get("paper_id", None),
                }
            )

        return {"status": "success", "papers": result_papers}
    except Exception as e:
        error_msg = f"获取学者论文失败: {str(e)}"
        # 移除错误通知
        logger.error(error_msg, exc_info=True)
        return {"status": "error", "message": "学者论文服务暂时不可用", "error": str(e)}


@mcp.prompt(PRESET_SUMMARY_PROMPT)
@mcp.tool()
async def summarize_papers(ctx: Context, topic: str, count: int = 5) -> str:
    """
    搜索并总结特定主题的论文

    Args:
        topic: 研究主题
        count: 返回结果数量，默认为5

    Returns:
        str: 论文总结的Markdown格式文本
    """
    try:
        # 移除进度显示
        logger.info(f"正在搜索并总结关于 {topic} 的论文...")

        # 搜索论文
        results = await search_scholar(topic, count)

        if not results:
            return f"未找到关于 {topic} 的论文。"

        # 构建总结
        summary = f"# {topic} 相关研究总结\n\n"
        summary += f"以下是关于 {topic} 的 {len(results)} 篇高引用研究论文的总结：\n\n"

        for i, paper in enumerate(results):
            summary += f"### {i+1}. {paper['title']}\n"
            summary += f"**作者**: {paper['authors']}\n"
            summary += f"**引用量**: {paper['citations']}\n"
            summary += f"**摘要**: {paper['abstract']}\n\n"

        return summary
    except Exception as e:
        # 移除错误通知
        logger.error(f"论文总结失败: {str(e)}", exc_info=True)
        return "论文总结服务暂时不可用"


@mcp.tool()
async def health_check(ctx: Context) -> str:
    """
    健康检查端点，用于验证服务是否正常运行

    Returns:
        str: 服务状态信息
    """
    return "MCP Scholar服务运行正常"


def cli_main():
    """
    CLI入口点，使用STDIO交互
    """
    print("MCP Scholar STDIO服务准备启动...", file=sys.stderr)

    try:
        # 启动STDIO服务器
        sys.stderr.write("MCP Scholar STDIO服务已启动，等待输入...\n")
        sys.stderr.flush()
        mcp.run()
    except Exception as e:
        print(f"服务启动失败: {str(e)}", file=sys.stderr)


def main():
    """
    服务入口点函数，使用WebSocket交互
    """
    try:
        # 启动WebSocket服务器
        mcp.run(host="0.0.0.0", port=8765)
    except Exception as e:
        print(f"服务启动失败: {str(e)}", file=sys.stderr)


if __name__ == "__main__":
    main()
