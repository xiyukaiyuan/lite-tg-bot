"""
# 项目名称: lite-tg-bot
# 项目简介: 极致轻量的 Telegram 消息双向转发机器人
# 部署遇到问题或者需要定制可以联系我：@zhu2wang
"""

import logging
import os
import sqlite3
from datetime import datetime
from telegram import Update, BotCommand, BotCommandScopeChat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 硬编码配置 ---
BOT_TOKEN = "132456789" # 你的 Telegram Bot Token
ADMIN_USER_ID = 123456789  # 你的 Telegram User ID
DB_FILE = "bot_data.db"

logging.getLogger("httpx").setLevel(logging.WARNING)

# --- 数据库操作 ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 消息映射表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_msg_id INTEGER UNIQUE,
            user_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 黑名单表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocked_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 用户信息记录表（用于通过用户名查 ID）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT,
            full_name TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_user_info(user_id, username, full_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, username, full_name, updated_at) VALUES (?, ?, ?, ?)",
        (user_id, username.lower() if username else None, full_name, now)
    )
    conn.commit()
    conn.close()

def get_user_id_from_db(search_term):
    """通过 ID 或用户名查询用户 ID"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    search_term = str(search_term).lower().replace("@", "")
    
    if search_term.isdigit():
        return int(search_term)
    
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (search_term,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def save_message_mapping(admin_msg_id, user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        "INSERT OR REPLACE INTO message_mappings (admin_msg_id, user_id, updated_at) VALUES (?, ?, ?)",
        (admin_msg_id, user_id, now)
    )
    conn.commit()
    conn.close()

def get_user_id_by_msg_id(admin_msg_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM message_mappings WHERE admin_msg_id = ?", (admin_msg_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def add_to_blacklist(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        "INSERT OR IGNORE INTO blocked_users (user_id, updated_at) VALUES (?, ?)",
        (user_id, now)
    )
    conn.commit()
    conn.close()

def remove_from_blacklist(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM blocked_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_user_blocked(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM blocked_users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# 初始化
init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("您好，管理员。")
    else:
        if is_user_blocked(user_id): return
        await update.message.reply_text("您好！请直接发送消息，我会转达。")

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """拉黑逻辑"""
    if update.effective_user.id != ADMIN_USER_ID: return

    # 仅允许带参数的指令 (/block 123)
    if context.args:
        target_id = get_user_id_from_db(context.args[0])
        if target_id:
            add_to_blacklist(target_id)
            await update.message.reply_text(f"🚫 已拉黑 `{target_id}`。")
        else:
            await update.message.reply_text("⚠️ 找不到该用户。")
    else:
        await update.message.reply_text("⚠️ 请提供要拉黑的用户名或 ID，例如：/block 12345")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """解封逻辑"""
    if update.effective_user.id != ADMIN_USER_ID: return

    # 仅允许带参数的指令 (/unblock 123)
    if context.args:
        target_id = get_user_id_from_db(context.args[0])
        if target_id:
            remove_from_blacklist(target_id)
            await update.message.reply_text(f"✅ 已解除 `{target_id}`。")
        else:
            await update.message.reply_text("⚠️ 找不到该用户。")
    else:
        await update.message.reply_text("⚠️ 请提供要解封的用户名或 ID，例如：/unblock 12345")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """消息处理"""
    user = update.effective_user
    msg = update.message

    if user.id == ADMIN_USER_ID:
        # 正常的回复转发逻辑
        if msg.reply_to_message:
            target_user_id = get_user_id_by_msg_id(msg.reply_to_message.message_id)
            if target_user_id:
                try:
                    await context.bot.copy_message(chat_id=target_user_id, from_chat_id=ADMIN_USER_ID, message_id=msg.message_id)
                except Exception as e:
                    await msg.reply_text(f"❌ 失败：{e}")
        return

    # 普通用户逻辑
    if is_user_blocked(user.id): return
    
    # 记录/更新用户信息，以便后续通过用户名查询
    save_user_info(user.id, user.username, user.full_name)

    try:
        username = f"@{user.username}" if user.username else "无用户名"
        header = f"👤 **来自**: {user.full_name}\n🔗 **用户名**: {username}\n🆔 **ID**: `{user.id}`\n--------------------------------"
        await context.bot.send_message(chat_id=ADMIN_USER_ID, text=header, parse_mode='Markdown')
        forwarded = await context.bot.copy_message(chat_id=ADMIN_USER_ID, from_chat_id=msg.chat_id, message_id=msg.message_id)
        save_message_mapping(forwarded.message_id, user.id)
    except Exception as e:
        print(f"转发失败异常: {e}")  # 正常抛出异常信息

def main():
    """主函数"""
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("block", block_user))
    app.add_handler(CommandHandler("unblock", unblock_user))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print("机器人已启动！")
    # 机器人启动
    app.run_polling()

if __name__ == "__main__":
    main()
