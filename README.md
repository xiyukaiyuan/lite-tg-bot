# Telegram 转发机器人

这是一个轻量的 Telegram 消息转发机器人。支持将对方的私聊消息实时转发给指定的管理员，管理员可以通过回复消息的方式与对方进行沟通。支持拉黑与解封用户。

## 功能特性

- 消息双向转发
- 基于 SQLite 记录消息与用户的映射关系
- 支持通过带参数指令拉黑或解封指定用户（支持数字 ID 或用户名）
- 运行日志脱敏处理，防止泄露聊天内容
- 代码极致精简，去除了所有不必要的 UI 菜单和交互状态机

## 环境要求

- Python 3.8 或以上版本
- python-telegram-bot (v20+)

## 部署步骤

*推荐使用 [雨云服务器](https://www.rainyun.com/?ref=MjM1MjI=) 部署本项目，稳定高效还便宜。*

1. 安装依赖

   使用以下命令安装运行依赖库：
   ```bash
   pip install python-telegram-bot
   ```

2. 配置文件

   打开 `main.py` 文件，修改头部的硬编码配置：
   - `BOT_TOKEN`: 你的 Telegram Bot Token
   - `ADMIN_USER_ID`: 管理员接收消息的 Telegram 纯数字 ID

   **获取参数的方法：**
   * **BOT_TOKEN**：在 Telegram 中搜索并进入 `@BotFather`，发送 `/newbot` 指令，按照提示创建机器人后，BotFather 会返回一串 HTTP API Token（即 BOT_TOKEN）。
   * **ADMIN_USER_ID**：这就是你本人的 Telegram 数字 ID。如果在官方客户端中无法查看，可以向 `@userinfobot` 发送任意消息获取；另外，如果你使用的是第三方客户端（如 Nekogram 或 64Gram 等），通常可以直接在个人资料页看到纯数字的 ID。

3. 启动程序 (前台测试)

   执行以下命令运行机器人：
   ```bash
   python main.py
   ```
   控制台输出“机器人已启动！”即代表服务连接成功。按 `Ctrl+C` 可停止运行。

4. 后台运行 (进程保活)

   在 SSH 终端直接运行通常会在关闭窗口时导致进程结束。建议使用 `nohup` 或 `screen` 让其在后台保持运行：

   - **使用 nohup（推荐）**
     ```bash
     nohup python main.py >/dev/null 2>&1 &
     ```
     执行后可直接关闭 SSH 窗口，机器人将持续在后台运行。

   - **使用 screen**
     ```bash
     screen -S tgbot
     python main.py
     ```
     执行后按 `Ctrl+A` 然后按 `D` 即可挂起后台，关闭 SSH 也不会影响程序。若需恢复查看，输入 `screen -r tgbot` 即可。

## 指令说明

管理员可直接发送以下指令进行操作：

- `/block <用户名或ID>`
  拉黑指定用户。被拉黑的用户发送的消息将被忽略。
  示例：`/block 12345` 或 `/block testuser`

- `/unblock <用户名或ID>`
  解除指定用户的拉黑状态。
  示例：`/unblock 12345` 或 `/unblock testuser`

## 数据库说明

第一次运行程序后，会在同级目录下自动生成 `bot_data.db` 数据库文件。该文件包含维持机器人运行必需的三张表：

- message_mappings：消息溯源表，用于识别管理员回复的消息属于哪个用户。
- users：用户信息表，缓存用户名与数字 ID 的对应关系，实现通过字母用户名进行拉黑。
- blocked_users：黑名单数据表。

若需迁移服务器或备份，请连同此 `.db` 文件一起打包和拷贝。

## 服务器推荐

### 如果需要云服务器来全天候运行本机器人程序，推荐使用：[雨云](https://www.rainyun.com/?ref=MjM1MjI=)

