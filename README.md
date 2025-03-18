# MCP Scholar

基于MCP协议的谷歌学术搜索和分析服务。

## 功能特点

- 谷歌学术论文搜索：根据关键词搜索相关论文，并按引用量排序
- 学者主页分析：分析谷歌学术个人主页，提取引用量最高的论文
- 支持与所有支持MCP客户端集成
- 支持与Cherry Studio集成：可以作为插件在Cherry Studio中使用

## 安装方法

### 启动服务器

```bash
# 方式一：使用uvx启动
uvx mcp-scholar

# 方式二：clone仓库后使用uv run启动
uv --directory 路径\到\mcp_scholar run mcp-scholar
```

### 在Cherry Studio中使用

- 「参照官方教程：https://vaayne.com/posts/2025/mcp-guide 」
 
## 示例用法

在Cherry Studio中，可以使用以下提示：

- 「总结5篇关于人工智能的论文」
- 「分析学者主页 https://scholar.google.com/citations?user=xxxxxx 的前10篇高引论文」

## 开发说明

本项目使用MCP协议开发，基于Python SDK实现。详细信息请参考[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)。

## 许可证

MIT