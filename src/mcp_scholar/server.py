from mcp.server.fastmcp import FastMCP, Context
from mcp_scholar.scholar import search_scholar, parse_profile
import httpx
import logging
import sys  # 添加这一行
from bs4 import BeautifulSoup

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

# 修改为STDIO类型的MCP服务器
mcp = FastMCP(
    "ScholarServer",
    dependencies=["beautifulsoup4", "httpx"],
    verbose=True,
    debug=True,
    # 移除了host和port配置，默认使用STDIO
)


@mcp.tool()
async def scholar_search(ctx: Context, keywords: str, count: int = 5) -> dict:
    """搜索谷歌学术并返回论文摘要"""
    try:
        results = await search_scholar(keywords, count)
        papers = []
        for p in results:
            papers.append(
                {
                    "title": p["title"],
                    "authors": p["authors"],
                    "abstract": (
                        p["abstract"][:200] + "..."
                        if len(p["abstract"]) > 200
                        else p["abstract"]
                    ),
                    "citations": p["citations"],
                    "year": p.get("year", "Unknown"),
                }
            )
        return {"status": "success", "count": len(papers), "papers": papers}
    except Exception as e:
        ctx.error(f"搜索失败: {str(e)}")
        return {"status": "error", "message": "学术搜索服务暂时不可用", "error": str(e)}


@mcp.tool()
async def profile_analysis(ctx: Context, profile_url: str, top_n: int = 5) -> str:
    """解析谷歌学术个人主页"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(profile_url)
            resp.raise_for_status()
            papers = parse_profile(resp.text, top_n)

        return "\n".join(
            f"{i+1}. {p['title']} (引用量：{p['citations']})"
            for i, p in enumerate(papers)
        )
    except Exception as e:
        ctx.error(f"个人主页解析失败: {str(e)}")
        return "无法获取个人学术资料"


@mcp.tool()
async def summarize_papers(ctx: Context, topic: str, count: int = 5) -> str:
    """根据主题搜索并总结论文"""
    try:
        ctx.info(f"正在搜索关于 '{topic}' 的{count}篇论文...")
        results = await search_scholar(topic, count)

        if not results:
            return f"未找到关于 '{topic}' 的相关论文"

        summary = f"## 关于 '{topic}' 的{len(results)}篇论文总结\n\n"

        for i, paper in enumerate(results):
            summary += f"### {i+1}. {paper['title']}\n"
            summary += f"**作者**: {paper['authors']}\n"
            summary += f"**引用量**: {paper['citations']}\n"
            summary += f"**摘要**: {paper['abstract']}\n\n"

        return summary
    except Exception as e:
        ctx.error(f"论文总结失败: {str(e)}")
        return "论文总结服务暂时不可用"


@mcp.tool()
async def health_check(ctx: Context) -> str:
    """健康检查端点，用于验证服务是否正常运行"""
    return "MCP Scholar服务运行正常"


def main():
    """服务入口点函数"""
    print("MCP Scholar STDIO服务准备启动...", file=sys.stderr)

    try:
        # 启动STDIO服务器
        sys.stderr.write("MCP Scholar STDIO服务已启动，等待输入...\n")
        sys.stderr.flush()
        mcp.run()
    except Exception as e:
        print(f"服务启动失败: {str(e)}", file=sys.stderr)


if __name__ == "__main__":
    main()
