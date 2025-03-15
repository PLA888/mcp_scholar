import asyncio
import argparse
import json
import sys
from mcp.shared.memory import create_connected_server_and_client_session
from mcp_scholar.server import mcp


def custom_encoder(o):
    """自定义JSON编码器，处理不可序列化的对象"""
    if hasattr(o, "__dict__"):
        return o.__dict__
    return str(o)


async def run_tests(args) -> None:
    """运行MCP服务测试"""
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        if args.test == "health":
            result = await client.call_tool("health_check")
            content = result.content[0]
            if hasattr(content, "text"):
                print(f"健康检查结果: {content.text}")
            else:
                print(f"健康检查结果: {content}")

        elif args.test == "search":
            result = await client.call_tool(
                "scholar_search", {"keywords": args.keywords, "count": args.count}
            )
            content = result.content[0]
            if hasattr(content, "text"):
                try:
                    data = json.loads(content.text)
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                    papers = data.get("papers", [])
                    if papers:
                        print(f"\n搜索结果共 {len(papers)} 条:")
                        for idx, paper in enumerate(papers, 1):
                            print(f"\n--- 论文 {idx} ---")
                            print(f"标题: {paper.get('title', 'N/A')}")
                            print(f"作者: {paper.get('authors', 'N/A')}")
                            print(f"年份: {paper.get('year', 'N/A')}")
                            print(f"摘要: {paper.get('abstract', 'N/A')}...")
                except json.JSONDecodeError:
                    print(f"无法解析JSON结果: {content.text}")
            else:
                print(f"无法获取搜索结果: {content}")

        elif args.test == "detail":
            result = await client.call_tool("paper_detail", {"paper_id": args.paper_id})
            print("论文详情:")
            content = result.content[0]
            if hasattr(content, "text"):
                try:
                    data = json.loads(content.text)
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                except json.JSONDecodeError:
                    print(content.text)
            else:
                print(f"详情内容: {content}")

        elif args.test == "references":
            result = await client.call_tool(
                "paper_references", {"paper_id": args.paper_id, "count": args.count}
            )
            print("论文引用:")
            content = result.content[0]
            if hasattr(content, "text"):
                try:
                    data = json.loads(content.text)
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                except json.JSONDecodeError:
                    print(content.text)
            else:
                print(f"引用内容: {content}")

        elif args.test == "profile":
            result = await client.call_tool(
                "profile_papers", {"profile_url": args.profile_url, "count": args.count}
            )
            print("学者论文:")
            content = result.content[0]
            if hasattr(content, "text"):
                try:
                    data = json.loads(content.text)
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                except json.JSONDecodeError:
                    print(content.text)
            else:
                print(f"学者论文内容: {content}")

        elif args.test == "summarize":
            result = await client.call_tool(
                "summarize_papers", {"topic": args.keywords, "count": args.count}
            )
            print("论文总结:")
            content = result.content[0]
            if hasattr(content, "text"):
                print(content.text)
            else:
                print(content)

        elif args.test == "all":
            # 健康检查
            result = await client.call_tool("health_check")
            content = result.content[0]
            if hasattr(content, "text"):
                print(f"健康检查结果: {content.text}")
            else:
                print(f"健康检查结果: {content}")

            # 搜索论文
            result = await client.call_tool(
                "scholar_search", {"keywords": args.keywords, "count": 1}
            )
            content = result.content[0]
            if hasattr(content, "text"):
                try:
                    data = json.loads(content.text)
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                    papers = data.get("papers", [])
                    if papers:
                        paper_id = papers[0].get("paper_id")
                        if paper_id:
                            # 获取论文详情
                            result = await client.call_tool(
                                "paper_detail", {"paper_id": paper_id}
                            )
                            print("\n论文详情:")
                            content = result.content[0]
                            if hasattr(content, "text"):
                                try:
                                    data = json.loads(content.text)
                                    print(
                                        json.dumps(data, ensure_ascii=False, indent=2)
                                    )
                                except json.JSONDecodeError:
                                    print(content.text)
                            else:
                                print(f"详情内容: {content}")

                            # 获取论文引用
                            result = await client.call_tool(
                                "paper_references", {"paper_id": paper_id, "count": 2}
                            )
                            print("\n论文引用:")
                            content = result.content[0]
                            if hasattr(content, "text"):
                                try:
                                    data = json.loads(content.text)
                                    print(
                                        json.dumps(data, ensure_ascii=False, indent=2)
                                    )
                                except json.JSONDecodeError:
                                    print(content.text)
                            else:
                                print(f"引用内容: {content}")
                except json.JSONDecodeError:
                    print(f"无法解析JSON结果: {content.text}")
            else:
                print(f"无法获取搜索结果: {content}")


def main():
    parser = argparse.ArgumentParser(description="MCP学术服务测试工具")
    parser.add_argument(
        "--test",
        choices=[
            "health",
            "search",
            "detail",
            "references",
            "profile",
            "summarize",
            "all",
        ],
        default="search",
        help="要执行的测试类型",
    )
    parser.add_argument("--keywords", default="人工智能", help="搜索关键词")
    parser.add_argument(
        "--paper-id",
        help="论文ID，用于详情和引用测试",
        default="10.1000/j.jss.2021.10.002",
    )
    parser.add_argument("--count", type=int, default=5, help="结果数量限制")
    parser.add_argument("--profile-url", help="学者个人主页URL，用于学者论文测试")

    args = parser.parse_args()

    if args.test in ["detail", "references"] and not args.paper_id:
        print("错误: 详情和引用测试需要提供 --paper-id 参数")
        sys.exit(1)

    asyncio.run(run_tests(args))


if __name__ == "__main__":
    main()
