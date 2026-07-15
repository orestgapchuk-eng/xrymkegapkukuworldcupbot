import os
import json
import random
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Завантажуємо токен
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Файли для збереження даних
CARDS_FILE = 'cards.json'
USERS_FILE = 'users_data.json'

# Рідкості та їх ймовірність
RARITIES = {
    'common': 0.50,
    'uncommon': 0.25,
    'rare': 0.15,
    'epic': 0.07,
    'legendary': 0.03
}

RARITY_EMOJI = {
    'common': '⚪',
    'uncommon': '🟢',
    'rare': '🔵',
    'epic': '🟣',
    'legendary': '🟡'
}

def load_cards():
    """Завантажити карти з JSON"""
    try:
        with open(CARDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Файл {CARDS_FILE} не знайдено!")
        return []

def load_users():
    """Завантажити дані користувачів"""
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    """Зберегти дані користувачів"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def get_or_create_user(user_id):
    """Отримати або створити користувача"""
    users = load_users()
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        users[user_id_str] = {
            'username': 'Unknown',
            'cards': {},
            'total_opens': 0,
            'created_at': datetime.now().isoformat(),
            'rarity_count': {'common': 0, 'uncommon': 0, 'rare': 0, 'epic': 0, 'legendary': 0}
        }
        save_users(users)
    
    return users[user_id_str]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    get_or_create_user(user.id)
    
    keyboard = [
        [InlineKeyboardButton("🃏 Відкрити картку", callback_data='open_card')],
        [InlineKeyboardButton("📚 Моя колекція", callback_data='my_cards')],
        [InlineKeyboardButton("📊 Моя статистика", callback_data='my_stats')],
        [InlineKeyboardButton("🏆 Топ гравців", callback_data='top_players')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Привіт, {user.first_name}!\n\n"
        f"Ласкаво просимо до 🏐 Xrymke Gapkuku World Cup Bot!\n\n"
        f"Тут ти можеш колекціонувати унікальні картки, змагатися з іншими гравцями та відслідковувати свій прогрес.\n\n"
        f"Обери дію:",
        reply_markup=reply_markup
    )

async def open_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Відкрити нову картку"""
    query = update.callback_query
    await query.answer()
    
    cards = load_cards()
    users = load_users()
    user_id_str = str(query.from_user.id)
    
    if not cards:
        await query.edit_message_text("❌ Картки не завантажені!")
        return
    
    # Вибираємо картку за рідкістю
    rarity = random.choices(
        list(RARITIES.keys()),
        weights=list(RARITIES.values())
    )[0]
    
    rarity_cards = [c for c in cards if c.get('rarity') == rarity]
    if not rarity_cards:
        rarity_cards = cards
    
    card = random.choice(rarity_cards)
    
    # Оновлюємо дані користувача
    if user_id_str in users:
        card_id = str(card['id'])
        if card_id not in users[user_id_str]['cards']:
            users[user_id_str]['cards'][card_id] = 0
        users[user_id_str]['cards'][card_id] += 1
        users[user_id_str]['total_opens'] += 1
        users[user_id_str]['rarity_count'][rarity] += 1
        save_users(users)
    
    # Формуємо відповідь
    text = (
        f"{RARITY_EMOJI.get(rarity, '❓')} **{card['name']}** {RARITY_EMOJI.get(rarity, '❓')}\n\n"
        f"🏐 Рідкість: {rarity.upper()}\n"
        f"📝 Опис: {card.get('description', 'Немає опису')}\n"
        f"📊 Копій у тебе: {users[user_id_str]['cards'].get(str(card['id']), 0)}"
    )
    
    keyboard = [
        [InlineKeyboardButton("🃏 Ще картку!", callback_data='open_card')],
        [InlineKeyboardButton("📚 Моя колекція", callback_data='my_cards')],
        [InlineKeyboardButton("📊 Статистика", callback_data='my_stats')],
        [InlineKeyboardButton("🏠 Меню", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def my_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показати колекцію користувача"""
    query = update.callback_query
    await query.answer()
    
    user_id_str = str(query.from_user.id)
    users = load_users()
    cards = load_cards()
    
    if user_id_str not in users:
        await query.edit_message_text("❌ Дані не знайдені!")
        return
    
    user_cards = users[user_id_str]['cards']
    if not user_cards:
        text = "📚 У твоїй колекції немає карток. Відкрий свою першу картку! 🃏"
    else:
        text = "📚 **Твоя колекція:**\n\n"
        for card_id, count in sorted(user_cards.items(), key=lambda x: int(x[0])):
            card = next((c for c in cards if str(c['id']) == card_id), None)
            if card:
                text += f"{RARITY_EMOJI.get(card.get('rarity'), '❓')} {card['name']} x{count}\n"
        text += f"\n📊 **Всього карток:** {sum(user_cards.values())}\n"
        text += f"🏐 **Унікальних:** {len(user_cards)}"
    
    keyboard = [
        [InlineKeyboardButton("🃏 Відкрити картку", callback_data='open_card')],
        [InlineKeyboardButton("📊 Статистика", callback_data='my_stats')],
        [InlineKeyboardButton("🏠 Меню", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показати статистику користувача"""
    query = update.callback_query
    await query.answer()
    
    user_id_str = str(query.from_user.id)
    users = load_users()
    
    if user_id_str not in users:
        await query.edit_message_text("❌ Дані не знайдені!")
        return
    
    user = users[user_id_str]
    text = "📊 **Твоя статистика:**\n\n"
    text += f"🎮 Відкрито карток: {user['total_opens']}\n"
    text += f"📚 Унікальних карток: {len(user['cards'])}\n"
    text += f"🏐 Всього в колекції: {sum(user['cards'].values())}\n\n"
    text += "**За рідкостями:**\n"
    for rarity, count in user['rarity_count'].items():
        text += f"{RARITY_EMOJI.get(rarity, '❓')} {rarity.upper()}: {count}\n"
    
    keyboard = [
        [InlineKeyboardButton("🏆 Топ гравців", callback_data='top_players')],
        [InlineKeyboardButton("📚 Колекція", callback_data='my_cards')],
        [InlineKeyboardButton("🏠 Меню", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def top_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показати топ гравців"""
    query = update.callback_query
    await query.answer()
    
    users = load_users()
    
    if not users:
        await query.edit_message_text("❌ Гравців ще немає!")
        return
    
    # Сортуємо за кількістю карток
    sorted_users = sorted(
        users.items(),
        key=lambda x: sum(x[1]['cards'].values()),
        reverse=True
    )[:10]
    
    text = "🏆 **Топ 10 гравців:**\n\n"
    for i, (uid, user) in enumerate(sorted_users, 1):
        total_cards = sum(user['cards'].values())
        unique_cards = len(user['cards'])
        text += f"{i}. 👤 {user.get('username', 'Unknown')} - {total_cards} карток ({unique_cards} унікальних)\n"
    
    keyboard = [
        [InlineKeyboardButton("🃏 Відкрити картку", callback_data='open_card')],
        [InlineKeyboardButton("📊 Моя статистика", callback_data='my_stats')],
        [InlineKeyboardButton("🏠 Меню", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Повернутися в меню"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🃏 Відкрити картку", callback_data='open_card')],
        [InlineKeyboardButton("📚 Моя колекція", callback_data='my_cards')],
        [InlineKeyboardButton("📊 Моя статистика", callback_data='my_stats')],
        [InlineKeyboardButton("🏆 Топ гравців", callback_data='top_players')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🏠 **Головне меню**\n\nОбери дію:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def reload_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезавантажити картки"""
    cards = load_cards()
    await update.message.reply_text(
        f"✅ Картки перезавантажені!\n"
        f"📊 Всього карток: {len(cards)}"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка кнопок"""
    query = update.callback_query
    
    if query.data == 'open_card':
        await open_card(update, context)
    elif query.data == 'my_cards':
        await my_cards(update, context)
    elif query.data == 'my_stats':
        await my_stats(update, context)
    elif query.data == 'top_players':
        await top_players(update, context)
    elif query.data == 'menu':
        await menu(update, context)

def main():
    """Запуск бота"""
    app = Application.builder().token(TOKEN).build()
    
    # Команди
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reload_cards", reload_cards))
    
    # Кнопки
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("🤖 Бот запущений!")
    app.run_polling()

if __name__ == '__main__':
    main()
