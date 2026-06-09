import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

with open("data.json", "r", encoding="utf-8") as f:
    DB = json.load(f)

MAIN_MENU_TEXT = (
    "🏥 *مرحباً في بوت التدريب الصيدلاني*\n\n"
    "📚 يمكنك من خلال هذا البوت:\n"
    "• تصفح الأدوية حسب النظام الجسدي\n"
    "• معرفة آلية عمل كل دواء\n"
    "• الاطلاع على الجرعات والآثار الجانبية\n"
    "• الاستماع لشرح صوتي\n\n"
    "اختر من القائمة 👇"
)

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 الأنظمة الدوائية", callback_data="systems")],
        [InlineKeyboardButton("🔍 بحث عن دواء", callback_data="search")],
        [InlineKeyboardButton("ℹ️ مساعدة", callback_data="help")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        MAIN_MENU_TEXT, parse_mode='Markdown',
        reply_markup=main_keyboard()
    )

async def show_systems(query, context):
    keyboard = []
    for sys_id, sys_data in DB["systems"].items():
        drug_count = len(sys_data["drugs"])
        keyboard.append([InlineKeyboardButton(
            f"{sys_data['name']} ({drug_count} أدوية)",
            callback_data=f"sys_{sys_id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main")])
    await query.edit_message_text(
        "📚 *اختر النظام الجسدي:*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_system_drugs(query, context, sys_id):
    system = DB["systems"].get(sys_id)
    if not system:
        await query.edit_message_text("❌ النظام غير موجود")
        return
    keyboard = []
    for drug_id, drug in system["drugs"].items():
        keyboard.append([InlineKeyboardButton(
            f"💊 {drug['name']}", callback_data=f"drug_{sys_id}_{drug_id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="systems")])
    await query.edit_message_text(
        f"{system['name']}\n\n*اختر الدواء:*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_drug_menu(query, context, sys_id, drug_id):
    drug = DB["systems"][sys_id]["drugs"].get(drug_id)
    if not drug:
        await query.edit_message_text("❌ الدواء غير موجود")
        return
    audio_label = "🔊 شرح صوتي ✅" if drug.get("audio") else "🔊 شرح صوتي (قريباً)"
    keyboard = [
        [InlineKeyboardButton("📋 معلومات عامة", callback_data=f"info_{sys_id}_{drug_id}")],
        [InlineKeyboardButton("⚙️ آلية العمل MOA", callback_data=f"moa_{sys_id}_{drug_id}")],
        [InlineKeyboardButton("⚠️ الآثار الجانبية", callback_data=f"se_{sys_id}_{drug_id}")],
        [InlineKeyboardButton("💊 الجرعة", callback_data=f"dose_{sys_id}_{drug_id}")],
        [InlineKeyboardButton(audio_label, callback_data=f"audio_{sys_id}_{drug_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"sys_{sys_id}")]
    ]
    await query.edit_message_text(
        f"💊 *{drug['name']}*\n\n📂 *الصنف:* {drug['class']}\n\nاختر ما تريد معرفته 👇",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_drug_detail(query, context, section, sys_id, drug_id):
    drug = DB["systems"][sys_id]["drugs"].get(drug_id)
    back = [[InlineKeyboardButton("🔙 رجوع للدواء", callback_data=f"drug_{sys_id}_{drug_id}")]]
    sections = {
        "info": (
            "📋 *معلومات عامة*",
            f"💊 *الدواء:* {drug['name']}\n\n"
            f"📂 *الصنف الدوائي:*\n{drug['class']}\n\n"
            f"✅ *الاستخدامات (Indications):*\n{drug['indications']}"
        ),
        "moa": (
            "⚙️ *آلية العمل - Mechanism of Action*",
            f"💊 *{drug['name']}*\n\n{drug['mechanism']}"
        ),
        "se": (
            "⚠️ *الآثار الجانبية - Side Effects*",
            f"💊 *{drug['name']}*\n\n{drug['side_effects']}"
        ),
        "dose": (
            "💊 *الجرعة - Dosage*",
            f"💊 *{drug['name']}*\n\n{drug['dose']}"
        )
    }
    if section in sections:
        title, body = sections[section]
        await query.edit_message_text(
            f"{title}\n\n{body}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(back)
        )

async def send_audio_explanation(query, context, sys_id, drug_id):
    drug = DB["systems"][sys_id]["drugs"].get(drug_id)
    back = [[InlineKeyboardButton("🔙 رجوع للدواء", callback_data=f"drug_{sys_id}_{drug_id}")]]
    if drug.get("audio"):
        await query.message.reply_audio(
            audio=drug["audio"],
            caption=f"🔊 شرح صوتي: {drug['name']}"
        )
        await query.edit_message_text(
            f"✅ تم إرسال الشرح الصوتي لـ *{drug['name']}*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(back)
        )
    else:
        await query.edit_message_text(
            f"⏳ *الشرح الصوتي لـ {drug['name']}*\n\nسيتوفر قريباً 🎙️",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(back)
        )

async def show_help(query, context):
    text = (
        "ℹ️ *دليل الاستخدام*\n\n"
        "1️⃣ اضغط *الأنظمة الدوائية*\n"
        "2️⃣ اختر النظام (قلبي، تنفسي، عصبي...)\n"
        "3️⃣ اختر الدواء\n"
        "4️⃣ ستظهر لك خيارات:\n"
        "   • 📋 معلومات عامة واستخدامات\n"
        "   • ⚙️ آلية عمل الدواء (MOA)\n"
        "   • ⚠️ الآثار الجانبية\n"
        "   • 💊 الجرعة الصحيحة\n"
        "   • 🔊 شرح صوتي\n\n"
        "🔍 أو استخدم *البحث* لإيجاد دواء مباشرة\n\n"
        "📝 للعودة للبداية اكتب /start"
    )
    await query.edit_message_text(
        text, parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main")
        ]])
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "main":
        await query.edit_message_text(MAIN_MENU_TEXT, parse_mode='Markdown', reply_markup=main_keyboard())
    elif data == "systems":
        await show_systems(query, context)
    elif data == "help":
        await show_help(query, context)
    elif data == "search":
        context.user_data["searching"] = True
        await query.edit_message_text(
            "🔍 *البحث عن دواء*\n\nاكتب اسم الدواء بالعربية أو الإنجليزية:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="main")
            ]])
        )
    elif data.startswith("sys_"):
        await show_system_drugs(query, context, data[4:])
    elif data.startswith("drug_"):
        parts = data.split("_", 2)
        await show_drug_menu(query, context, parts[1], parts[2])
    elif data.startswith("audio_"):
        parts = data.split("_", 2)
        await send_audio_explanation(query, context, parts[1], parts[2])
    else:
        parts = data.split("_", 2)
        if len(parts) == 3:
            await show_drug_detail(query, context, parts[0], parts[1], parts[2])

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("searching"):
        await update.message.reply_text("اكتب /start للبدء 🏥")
        return
    query_text = update.message.text.lower().strip()
    results = []
    for sys_id, system in DB["systems"].items():
        for drug_id, drug in system["drugs"].items():
            if (query_text in drug["name"].lower() or
                query_text in drug["class"].lower()):
                results.append((sys_id, drug_id, drug["name"], system["name"]))
    context.user_data["searching"] = False
    if results:
        keyboard = []
        for sid, did, name, sname in results:
            keyboard.append([InlineKeyboardButton(
                f"💊 {name} | {sname}", callback_data=f"drug_{sid}_{did}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main")])
        await update.message.reply_text(
            f"🔍 *نتائج البحث عن: {query_text}*\n\nوُجد {len(results)} نتيجة:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            f"❌ لم يُوجد دواء باسم: *{query_text}*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main")
            ]])
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("✅ البوت يعمل...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
