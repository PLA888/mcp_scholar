from mcp.server.fastmcp import FastMCP, Context
from mcp_scholar.scholar import search_scholar, parse_profile
import httpx
from bs4 import BeautifulSoup

mcp = FastMCP(
    "ScholarServer",
    dependencies=["beautifulsoup4", "httpx"],
    host="0.0.0.0",
    port=8080,
    verbose=True,
)


@mcp.tool()
async def scholar_search(ctx: Context, keywords: str, count: int = 5) -> str:
    """搜索谷歌学术并返回论文摘要"""
    try:
        results = await search_scholar(keywords, count)
        return "\n\n".join(
            f"标题：{p['title']}\n作者：{p['authors']}\n摘要：{p['abstract'][:200]}..."
            for p in results
        )
    except Exception as e:
        ctx.error(f"搜索失败: {str(e)}")
        return "学术搜索服务暂时不可用"


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


def main():
    """服务入口点函数"""
    print("MCP Scholar服务已启动，等待连接...")
    mcp.run()


if __name__ == "__main__":
    main()
