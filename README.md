# ICDS Chat Project

这是一个基于 Python socket 的聊天程序，包含图形界面客户端、服务器、群聊、聊天记录搜索、文件发送、AI 聊天、AI 图片生成、聊天总结/关键词分析，以及 Snake 和 Tic-Tac-Toe 小游戏。

## 环境要求

- Python 3
- 推荐在项目根目录运行命令
- 基础聊天功能主要使用 Python 标准库和 `tkinter`
- AI 功能需要额外安装依赖：

```bash
pip install openai ollama
```

## 启动方法

先启动服务器：

```bash
python chat_server.py
```

再打开一个新的终端启动客户端：

```bash
python chat_cmdl_client.py -d 127.0.0.1
```

如果服务器在另一台机器上，可以指定服务器 IP：

```bash
python chat_cmdl_client.py -d 服务器IP地址
```

需要多人聊天时，重复运行客户端即可。

## 常用功能

登录后可以在客户端里使用这些命令：

- `who`：查看在线用户
- `c 用户名`：连接某个用户开始聊天
- `bye`：退出当前聊天
- `time`：查看服务器时间
- `? 关键词`：搜索聊天记录
- `p 编号`：查看指定编号的 sonnet
- `q`：退出程序

图形界面中还可以使用：

- 发送文件
- Snake 游戏和排行榜
- Tic-Tac-Toe 双人游戏
- `@bot 消息`：向本地 AI 聊天机器人提问
- `/aipic: 提示词`：生成 AI 图片
- `/summary`：总结最近聊天
- `/keywords`：提取聊天关键词

## AI 配置

如果使用 AI 图片或 DeepSeek NLP 功能，可以在项目根目录创建 `.env` 文件：

```env
OPENAI_API_KEY=你的 OpenAI Key
ARK_API_KEY=你的火山方舟 Key
DEEPSEEK_API_KEY=你的 DeepSeek Key
```

本地聊天机器人默认使用 Ollama，需要先启动 Ollama，并准备模型：

```bash
ollama pull qwen2.5:0.5b
```

也可以单独启动群聊机器人：

```bash
python bot_client.py -d 127.0.0.1
```

自定义机器人名字：

```bash
python bot_client.py -d 127.0.0.1 -n AI_Bot
```

## 文件说明

- `chat_server.py`：聊天服务器
- `chat_cmdl_client.py`：客户端启动入口
- `GUI.py`：图形界面
- `chat_utils.py`：公共配置和消息工具
- `bot_client.py` / `chat_bot_client.py`：AI 聊天机器人
- `aipic_client.py`：AI 图片生成
- `chat_nlp.py`：聊天总结和关键词分析
- `snake_game.py` / `tictactoe_game.py`：小游戏

## 注意事项

- 服务器默认端口是 `1112`，配置在 `chat_utils.py`。
- `.env` 和生成的图片目录 `generated_images/` 不会提交到 Git。
- 使用 AI 功能前，请确认依赖、API Key 或本地 Ollama 服务已经配置好。
