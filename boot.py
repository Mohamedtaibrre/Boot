import logging
import mysql.connector
import traceback
import datetime
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from config import TOKEN, DB_CONFIG, ADMIN_ID

bot = Bot(token=TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)

# إعداد نظام التسجيل
logging.basicConfig(level=logging.INFO, filename="bot.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

# إرسال إشعار للمسؤول عند حدوث خطأ
async def notify_admin(error_msg):
    try:
        await bot.send_message(ADMIN_ID, f"⚠️ *خطأ في البوت!*\n\n```{error_msg}```")
    except:
        logging.error("❌ فشل في إرسال إشعار الخطأ إلى المسؤول")

# عند بدء تشغيل البوت
async def on_startup(_):
    await bot.send_message(ADMIN_ID, "✅ *تم تشغيل البوت بنجاح!*")

# قائمة التحكم الرئيسية
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💰 رصيدي", callback_data="wallet"),
        InlineKeyboardButton("🎁 مكافأة يومية", callback_data="daily_bonus"),
        InlineKeyboardButton("📜 مهامي", callback_data="tasks"),
        InlineKeyboardButton("🛍️ المتجر", callback_data="marketplace"),
        InlineKeyboardButton("📤 سحب", callback_data="withdraw"),
        InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")
    )
    return keyboard

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE telegram_id=%s", (message.from_user.id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (telegram_id, username) VALUES (%s, %s)", 
                       (message.from_user.id, message.from_user.username))
        conn.commit()
        await message.reply("🎉 *تم إنشاء محفظتك بنجاح!*", reply_markup=main_menu())
    else:
        await message.reply("✅ *مرحبًا بك مرة أخرى!*", reply_markup=main_menu())

    cursor.close()
    conn.close()

@dp.callback_query_handler(lambda call: call.data == "wallet")
async def wallet(call: types.CallbackQuery):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE telegram_id=%s", (call.from_user.id,))
    balance = cursor.fetchone()[0]
    await call.message.edit_text(f"💰 *رصيدك الحالي:* `{balance:.2f} COIN`", reply_markup=main_menu())
    cursor.close()
    conn.close()

@dp.callback_query_handler(lambda call: call.data == "tasks")
async def show_tasks(call: types.CallbackQuery):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_name, reward FROM tasks")
    tasks = cursor.fetchall()
    task_text = "🎯 *المهام اليومية:*\n\n" + "\n".join([f"🔹 {t[1]} - 💰 {t[2]:.2f} COIN" for t in tasks])
    await call.message.edit_text(task_text, reply_markup=main_menu())
    cursor.close()
    conn.close()

@dp.callback_query_handler(lambda call: call.data == "marketplace")
async def show_marketplace(call: types.CallbackQuery):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT item_name, price FROM marketplace")
    items = cursor.fetchall()
    shop_text = "🛍️ *العناصر المتاحة في المتجر:*\n\n" + "\n".join([f"🔹 {i[0]} - {i[1]:.2f} COIN" for i in items])
    await call.message.edit_text(shop_text, reply_markup=main_menu())
    cursor.close()
    conn.close()

@dp.callback_query_handler(lambda call: call.data == "withdraw")
async def withdraw(call: types.CallbackQuery):
    await call.message.edit_text("🔗 *أرسل عنوان محفظتك لسحب العملات إليها.*")

@dp.message_handler(lambda message: re.match(r"^0x[a-fA-F0-9]{40}$", message.text))
async def enter_wallet_address(message: types.Message):
    wallet_address = message.text
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE telegram_id=%s", (message.from_user.id,))
    balance = cursor.fetchone()[0]

    if balance <= 0:
        await message.reply("❌ *ليس لديك رصيد كافٍ للسحب!*")
        cursor.close()
        conn.close()
        return

    await message.reply(f"✅ *عنوان المحفظة:* `{wallet_address}`\n💰 *رصيدك:* `{balance:.2f} COIN`\n\n"
                        "✏️ *الآن أرسل المبلغ الذي تريد سحبه:*")

    cursor.execute("INSERT INTO withdrawals (user_id, wallet_address, amount, status) VALUES (%s, %s, %s, 'pending')", 
                   (message.from_user.id, wallet_address, 0))
    conn.commit()
    cursor.close()
    conn.close()

@dp.callback_query_handler(lambda call: call.data == "admin_panel")
async def admin_panel(call: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🏆 تعديل نقاط الإحالة", callback_data="admin_set_referral"),
        InlineKeyboardButton("🎁 تعديل المكافأة اليومية", callback_data="admin_set_daily_bonus"),
        InlineKeyboardButton("🛠️ إضافة مهام جديدة", callback_data="admin_add_task"),
        InlineKeyboardButton("🔥 حرق عملات", callback_data="admin_burn")
    )
    await call.message.edit_text("⚙️ *لوحة تحكم المسؤول*", reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data == "admin_set_referral")
async def admin_set_referral(call: types.CallbackQuery):
    await call.message.edit_text("✏️ *أرسل عدد النقاط الجديدة لكل إحالة:*\n\nمثال: `/set_referral 10`")

@dp.message_handler(lambda message: message.text.startswith("/set_referral"))
async def set_referral_bonus(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    new_bonus = int(message.text.split()[1])

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET referral_bonus=%s WHERE id=1", (new_bonus,))
    conn.commit()
    await message.reply(f"✅ *تم تحديث نقاط الإحالة إلى {new_bonus}!*")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
