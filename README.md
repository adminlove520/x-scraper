# 🐦 X-Scraper - 高性能 Twitter/X.com 监控与采集工具

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Discord](https://img.shields.io/badge/Discord-Bot-7289DA.svg)](https://discord.com/)

X-Scraper 是一款企业级 Twitter/X.com 监控解决方案，专为高效、稳定的数据采集设计。本项目已全面重构，支持官方 API v2 (Bearer Token) **多账号轮换**、Discord 机器人实时推送、以及 GitHub Actions 自动化监控。

## 🚀 核心特性

- **🎯 X.com 官方支持**：采用 Twitter API v2 (Bearer Token)，**支持多 Token 自动轮换**，有效规避频率限制。
- **🤖 Discord 机器人**：
    - 支持 Slash Commands（斜杠命令）。
    - 个人专属订阅列表，新推文自动 **@提醒**。
    - **关注列表监控**：所监控用户新关注了谁，第一时间提醒。
    - 实时粉丝排行 (TOP 10) 与热门推文概览。
- **🌐 多模态推送**：同时支持全群 Webhook 公告与个人专属 Bot 提醒。
- **⚡ 自动化任务**：通过 GitHub Actions 实现定时监控，无需服务器即可运行全球公告。
- **☁️ 极简部署**：一键部署至 Zeabur 或 Docker 环境。
- **🔧 灵活配置**：单人单档配置，各订阅列表互不干扰。

## 📋 目录

- [安装指南](docs/DEPLOYMENT_GUIDE_ZH.md#️-安装指南)
- [快速开始](docs/DEPLOYMENT_GUIDE_ZH.md#-快速开始)
- [Discord 机器人命令](#-discord-机器人命令)
- [部署说明](docs/DEPLOYMENT_GUIDE_ZH.md#-部署说明)
- [项目结构](#-项目结构)
- [许可证](#-许可证)
- [更新日志](CHANGELOG.md)

## 🛠️ 安装指南

### 前置要求

- Python 3.8 或更高版本
- 获取 Twitter Bearer Token (前往 [Twitter Developer Portal](https://developer.twitter.com/))
- Discord Bot Token 及 Webhook URL (可选)

### 第一步：克隆仓库

```bash
git clone https://github.com/adminlove520/x-scraper.git
cd x-scraper
```

### 第二步：配置环境

复制 `.env.example` 为 `.env` 并填写相关信息：

```bash
# Twitter API
TWITTER_BEARER_TOKEN=你的_Bearer_Token

# Discord
DISCORD_TOKEN=你的_Bot_Token
DISCORD_WEBHOOK_URL=你的_Webhook_URL
DISCORD_CHANNEL_ID=消息推送的频道ID
```

### 第三步：安装依赖

```bash
pip install -r requirements.txt
```

## 🚀 快速开始

### 启动服务

直接运行主程序，即可同时启动 Discord 机器人和后台监控引擎：

```bash
python main.py
```

### 手动检查推文 (通过脚本)

如果你只想运行一次全局监控推送：

```bash
python scripts/webhook_push.py
```

## 🤖 Discord 机器人命令

在 Discord 频道中使用以下斜杠命令：

- `/followers_add @用户名`：为自己增加一个推特订阅。
- `/followers_delete @用户名`：删除已有的推特订阅。
- `/admin_followers_list`：查看你当前订阅的所有用户列表。
- `/followtop10`：查看你订阅的用户中，粉丝数最高的前 10 名（附带详情）。
- `/top10`：查看当前订阅用户中的热门推文汇总。

#### 管理员命令 (仅限配置了 DISCORD_ADMIN_ID 的用户)
- `/admin_all_stats`：查看全站所有用户的订阅统计。
- `/admin_view_user @用户`：查看指定 Discord 用户的监控列表。
- `/admin_delete_for_user @用户 @推特账号`：强制删除指定用户的监控。

## ☁️ 部署说明

### Zeabur 部署
本项目完全兼容 Zeabur。只需连接 GitHub 仓库，Zeabur 会自动识别 `Dockerfile` 并完成部署。

### 容器化部署
如果你有自己的服务器：

```bash
docker build -t x-scraper .
docker run -d --env-file .env x-scraper
```

## 📁 项目结构

```
x-scraper/
├── app/
│   ├── core/           # 核心配置与日志
│   ├── crawlers/       # X API 采集器
│   ├── pushers/        # Discord Bot 与 Webhook 推送
│   └── engine.py       # 核心调度引擎
├── config/
│   └── users.json      # 全局 Webhook 订阅列表
├── data/
│   ├── users_dc_*.json # Discord 用户个人订阅
│   └── processed_ids.json # 已推送推文记录
├── scripts/
│   └── webhook_push.py # 独立推送脚本
├── main.py             # 主程序入口
├── Dockerfile          # Docker 配置文件
└── zeabur.json         # Zeabur 部署配置
```

## ⚠️ 法律与道德声明

- **尊重频率限制**：请勿频繁请求 API，以免封号。
- **仅限公开数据**：本工具仅采集公开推文。
- **合规使用**：请遵守 Twitter 的服务条款与相关法律法规。

## 📄 许可证

本项目基于 MIT 许可证开源 - 详见 [LICENSE](LICENSE) 文件。