# MCP Scholar

基于MCP协议的谷歌学术搜索和分析服务。

## 功能特点

- 谷歌学术论文搜索：根据关键词搜索相关论文，并按引用量排序
- 学者主页分析：分析谷歌学术个人主页，提取引用量最高的论文
- 支持与Cherry Studio集成：可以作为插件在Cherry Studio中使用

## 安装方法

### 使用uv安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/mcp-scholar.git
cd mcp-scholar

# 使用uv安装依赖
uv pip install -e .
```

### 使用pip安装

```bash
pip install mcp-scholar
```

## 使用方法

### 启动服务器

```bash
# 使用uvx启动
uvx mcp-scholar

# 或者直接使用Python模块
python -m mcp_scholar
```

### 在Cherry Studio中使用

1. 在Cherry Studio中，点击「设置」>「插件」
2. 添加新插件，输入MCP服务器地址：`http://localhost:8080`
3. 保存设置后，即可在对话中使用学术搜索功能

## 示例用法

在Cherry Studio中，可以使用以下提示：

- 「总结5篇关于人工智能的论文」
- 「分析学者主页 https://scholar.google.com/citations?user=SJdlvnQAAAAJ&hl=en 的前10篇高引论文」

## 开发说明

本项目使用MCP协议开发，基于Python SDK实现。详细信息请参考[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)。

## 许可证

MIT