import asyncio
import argparse
import json
import sys
from mcp.shared.memory import create_connected_server_and_client_session
from mcp_scholar.server import mcp  # 确保这里导入的是您使用的 FastMCP 实例


def custom_encoder(o):
    # 如果对象有 __dict__ 属性，直接返回
    if hasattr(o, "__dict__"):
        return o.__dict__
    # 否则返回字符串表示
    return str(o)


async def run_tests(args) -> None:
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        if args.test == "health":
            result = await client.call_tool("health_check")
            # 处理结果
            content = result.content[0]
            if hasattr(content, "text"):
                print(f"健康检查结果: {content.text}")
            else:
                print(f"健康检查结果: {content}")

        elif args.test == "search":
            result = await client.call_tool(
                "scholar_search", {"keywords": args.keywords, "count": args.count}
            )
            # 调试代码
            print(f"结果类型: {type(result)}")
            print(f"内容列表长度: {len(result.content)}")
            print(f"第一个内容类型: {type(result.content[0])}")
            
            content = result.content[0]
            if hasattr(content, "text"):
                try:
                    data = json.loads(content.text)
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                    papers = data.get("papers", [])
                    if papers:
                        paper_id = papers[0].get("paper_id")
                        # 其他处理...
                except json.JSONDecodeError:
                    print(f"无法解析JSON结果: {content.text}")
            else:
                print(f"无法获取搜索结果: {content}")

        elif args.test == "detail":
            result = await client.call_tool("paper_detail", {"paper_id": args.paper_id})
            print("论文详情:")
            # 提取内容而不是直接序列化
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
            # 提取内容而不是直接序列化
            content = result.content[0]
            if hasattr(content, "text"):
                try:
                    data = json.loads(content.text)
                    print(f"论文引用共 {len(data)} 条:")
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                except json.JSONDecodeError:
                    print(content.text)
            else:
                print(f"引用内容: {content}")

        elif args.test == "all":
            # 同样处理 health_check 结果
            result = await client.call_tool("health_check")
            content = result.content[0]
            if hasattr(content, "text"):
                print(f"健康检查结果: {content.text}")
            else:
                print(f"健康检查结果: {content}")

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
                        # 继续处理...
                except json.JSONDecodeError:
                    print(f"无法解析JSON结果: {content.text}")
            else:
                print(f"无法获取搜索结果: {content}")

                result = await client.call_tool(
                    "paper_detail", {"paper_id": paper_id}
                )
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

                result = await client.call_tool(
                    "paper_references", {"paper_id": paper_id, "count": 3}
                )
                print("论文引用:")
                content = result.content[0]
                if hasattr(content, "text"):
                    try:
                        data = json.loads(content.text)
                        print(f"论文引用共 {len(data)} 条:")
                        print(json.dumps(data, ensure_ascii=False, indent=2))
                    except json.JSONDecodeError:
                        print(content.text)
                else:
                    print(f"引用内容: {content}")


def main():
    parser = argparse.ArgumentParser(description="MCP学术服务测试工具")
    parser.add_argument(
        "--test",
        choices=["health", "search", "detail", "references", "all"],
        default="all",
        help="要执行的测试类型",
    )
    parser.add_argument("--keywords", default="人工智能", help="搜索关键词")
    parser.add_argument(
        "--paper-id",
        help="论文ID，用于详情和引用测试",
        default="10.1000/j.jss.2021.10.002",
    )
    parser.add_argument("--count", type=int, default=5, help="结果数量限制")

    args = parser.parse_args()

    if args.test in ["detail", "references"] and not args.paper_id:
        print("错误: 详情和引用测试需要提供 --paper-id 参数")
        sys.exit(1)

    asyncio.run(run_tests(args))


if __name__ == "__main__":
    main()
