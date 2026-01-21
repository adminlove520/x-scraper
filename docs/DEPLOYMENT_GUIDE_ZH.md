# 🚀 X-Scraper 部署与使用指南

本指南将引导您完成 X-Scraper 的安装、配置及部署，帮助您快速搭建属于自己的 Twitter 监控系统。

## 📋 目录

- [快速配置](#-快速配置)
- [环境安装](#-环境安装)
- [配置文件说明](#-配置文件说明)
- [Discord 机器人设置](#-discord-机器人设置)
- [部署到 Zeabur](#-部署到-zeabur)
- [常见问题](#-常见问题)

## ⚡ 快速配置

### 1. 克隆项目
```bash
git clone https://github.com/adminlove520/x-scraper.git
cd x-scraper
```

### 2. 初始化环境
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 填写 API 密钥
编辑 `.env` 文件（或在 Zeabur 环境变量中设置）：
```env
# 支持多个 Token 轮换，用逗号分隔
TWITTER_BEARER_TOKEN=token1,token2
DISCORD_TOKEN=你的_机器人Token
DISCORD_WEBHOOK_URL=你的_Webhook链接
DISCORD_CHANNEL_ID=消息推送频道ID
DISCORD_ADMIN_ID=管理员的Discord_ID
```

## 🔧 环境安装

### 运行主程序
主程序 `main.py` 会同时启动 **Discord 机器人交互** 和 **后台轮询引擎**：
```bash
python main.py
```

### 运行监控脚本
如果您只需要通过 GitHub Actions 或手动运行单次检查推送：
```bash
python scripts/webhook_push.py
```

## ⚙️ 配置文件说明

### 全局订阅 (`config/users.json`)
此文件决定了发送到 **Webhook 全群公告** 的用户列表。格式如下：
```json
[
  {"username": "elonmusk"},
  {"username": "binance"}
]
```

### 个人订阅 (`data/users_dc_{UID}.json`)
当用户在 Discord 使用 `/followers_add` 命令时，程序会自动在此目录下创建专属配置文件。

## 🤖 Discord 机器人设置

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)。
2. 创建 Application 并添加 Bot。
3. 确保开启了 `Message Content Intent` 权限。
4. 使用 `OAuth2 URL Generator` 生成含有 `applications.commands` 和 `bot` 作用域的链接邀请机器人。
5. 获取 `TOKEN` 和频道 `ID` 填入 `.env`。

## ⚖️ API 限制与轮换说明

Twitter API v2 对 Bearer Token 有严格的速率限制。本项目支持 **多 Token 自动轮换**：

- **如何使用**：在 `TWITTER_BEARER_TOKEN` 中填入多个被英文逗号分隔的 Token。
- **自动逻辑**：当当前 Token 触发 429 (Rate Limit) 错误时，`XCrawler` 会自动切换到下一个可用 Token。
- **全局等待**：如果所有 Token 都已耗尽，程序会自动休眠 15 分钟后重试。

## ☁️ 部署到 Zeabur

Zeabur 是最推荐的部署方式：

1. 在 Zeabur 中新建项目。
2. 绑定您的 GitHub 仓库 `x-scraper`。
3. 在 Zeabur 的 **Variables** 界面填入 `.env` 中的所有环境变量。
4. Zeabur 会根据 `zeabur.json` 和 `Dockerfile` 自动开始构建并运行。
5. **持久化存储**：建议在 Zeabur 挂载 Volume 到 `/app/data` 目录，以防 `processed_ids.json` 丢失导致重复推送。

## 🛠️ 常见问题

- **推文不更新？**：检查 `TWITTER_BEARER_TOKEN` 是否有效，及速率限制情况。
- **Slash 命令没出来？**：重启机器人，Bot 会在启动时自动执行 `tree.sync()`。
- **重复推送？**：确保 `data/processed_ids.json` 在部署环境中是持久保存的。
