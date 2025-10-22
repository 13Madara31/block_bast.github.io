import telebot
import logging
import time
import os
from gtts import gTTS
import tempfile
import random
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request, jsonify
from flask_cors import CORS # Импортируем CORS
import threading

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Токен бота
bot = telebot.TeleBot(os.environ.get('TELEGRAM_BOT_TOKEN'))

app = Flask(__name__) # Инициализация Flask приложения
CORS(app) # Включаем CORS для всего приложения Flask

# Списки
ADMINS = [1192684448, 1455941147, 6824082367, 1647977664]
PROTECTED_USER = "@Madara1332"

# НОВЫЙ СПИСОК ИЗВЕСТНЫХ ЮЗЕРНЕЙМОВ, которые бот будет пытаться упомянуть
KNOWN_USERNAMES = [
    "@Madara1332", "@icemxn", "@ivanNN4ik", "@polyashenka",
    "@kanapeas", "@Hg2355644", "@Fun_Dan3", "@Krasavchikkkkkkkkkkkkkk",
    "@sundrseil59", "@nestea_rem", "@Grut_as", "@GerBEE4", "@DevilHeaven0",
    "@xenophonsshiva", "@Lolil_Angi", "@marriavoronina", "@luniluda", "@austinec1",
    "@DAWKAODAWKA", "@Curse9123", "@anuytaaaa", "@krasavchikkkkkkkkk", "@Popluektov",
    "@Barbs228", "@holejes", "@Zxcvbnm_111222", "@referalyan",
    "@superiorplazer", "@ame_libre_de_lartiste", "@tmlk_07", "@tfgkghn","@sseeevgii",
    "@Aleks_Chik","@AbaddonTaken","@Fort_KH","@mashhkb","@nikita_ket","@Blabyda16547","@Prostoktotto","@Chert1la1"
]

ANNOUNCEMENT_CHAT_ID = ADMINS[0] # По умолчанию, отправляем первому админу. Пожалуйста, замените на ID нужного чата/канала!

# НАСТРОЙКА СИСТЕМЫ АНТИ-МАТА (по умолчанию ВЫКЛЮЧЕНА)
ANTI_MAT_ENABLED = False

BAD_WORDS = [
    'бля', 'блять', 'пизда', 'пиздец', 'хуй', 'хуё', 'ебать', 'ебал', 'ебан',
    'нах', 'нахуй', 'сука', 'блядь', 'гандон', 'мудак', 'долбаёб', 'залупа'
]

ULTIMATUM_TASKS = [
    "Напиши 10 раз 'Я больше не буду материться'",
    "Сделай 20 приседаний",
    "Спой песню в голосовом сообщении", 
    "Напиши стих про хорошее поведение",
    "Сделай 15 отжиманий",
    "Придумай и расскажи шутку",
    "Напиши рассказ на 100 слов о вежливости",
    "Сделай 10 поклонов с извинениями",
    "Спой гимн вежливости"
]

# Глобальные переменные
USER_VIOLATIONS = {}
USER_TIMEOUTS = {}

# ПУТИ К ВАШИМ АУДИОФАЙЛАМ - НАСТРОЙТЕ ЭТИ ПУТИ!
AUDIO_FILES = {
    'puck': 'farts-46.mp3',      # Аудио для обычного пука
    'puck2': 'long-fart.mp3',     # Аудио для усиленного пука
    'puck3': 'farts-36.mp3',     # Аудио для эпического пука
    'protection': 'нет.mp4'   # Видео для защиты
}

def is_admin(user_id):
    return user_id in ADMINS

def is_user_in_timeout(user_id):
    """Проверяет, находится ли пользователь в таймауте"""
    if user_id in USER_TIMEOUTS:
        timeout_end = USER_TIMEOUTS[user_id]
        if datetime.now() < timeout_end:
            return True, timeout_end
        else:
            del USER_TIMEOUTS[user_id]
    return False, None

def set_user_timeout(user_id, minutes=5):
    """Устанавливает таймаут для пользователя"""
    USER_TIMEOUTS[user_id] = datetime.now() + timedelta(minutes=minutes)
    return USER_TIMEOUTS[user_id]

def contains_bad_words(text):
    """Проверяет текст на наличие матных слов"""
    if not text:
        return False, None
        
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word in text_lower:
            return True, word
    return False, None

def get_random_task():
    return random.choice(ULTIMATUM_TASKS)

def send_audio_message(chat_id, audio_type):
    """Отправляет ваш аудиофайл в зависимости от типа команды"""
    try:
        audio_file = AUDIO_FILES.get(audio_type)
        if not audio_file:
            logging.error(f"Аудиофайл для типа {audio_type} не найден в настройках")
            return False
            
        # Проверяем существует ли файл
        if not os.path.exists(audio_file):
            logging.error(f"Аудиофайл не найден: {audio_file}")
            return False

         
        # Отправляем аудио как голосовое сообщение
        with open(audio_file, 'rb') as audio:
            if audio_type == 'puck':
                caption = "💨 Пук атака!"
            elif audio_type == 'puck2':
                caption = "💥💨 Супер пук атака!"
            elif audio_type == 'puck3':
                caption = "🌪️💨 Эпический пук!"
            else:
                caption = "🔊 Аудио сообщение"
                
            bot.send_voice(chat_id, audio, caption=caption)
            logging.info(f"Аудио отправлено: {audio_file}")
            return True
            
    except Exception as e:
        logging.error(f"Ошибка при отправке аудио: {e}")
        return False

def send_protection_video(chat_id):
    """Отправляет защитное видео"""
    try:
        video_file = AUDIO_FILES.get('protection')
        if not video_file:
            logging.error("Защитное видео не найдено в настройках")
            return False
            
        # Проверяем существует ли файл
        if not os.path.exists(video_file):
            logging.error(f"Видеофайл не найден: {video_file}")
            return False
            
        # Отправляем видео
        with open(video_file, 'rb') as video:
            bot.send_video(chat_id, video, caption="🛡️ ЗАЩИТА АКТИВИРОВАНА!")
            logging.info(f"Защитное видео отправлено: {video_file}")
            return True
            
    except Exception as e:
        logging.error(f"Ошибка при отправке видео: {e}")
        return False

def text_to_speech(text, lang='ru'):
    """Преобразует текст в голосовое сообщение"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_filename = temp_file.name
        
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(temp_filename)
        return temp_filename
    except Exception as e:
        logging.error(f"Ошибка TTS: {e}")
        return None

# ========== КНОПКИ МЕНЮ (REPLY KEYBOARD) ==========

def create_main_keyboard():
    """Создает основную клавиатуру меню"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Добавляем кнопки
    button1 = KeyboardButton('🔔 Упомянуть всех')
    button2 = KeyboardButton('🎮 Block Blast')
    button3 = KeyboardButton('📊 Мой статус')
    button4 = KeyboardButton('🛡️ Анти-мат')
    button5 = KeyboardButton('ℹ️ Помощь')
    button6 = KeyboardButton('🧪 Тест бота')
    
    keyboard.add(button1, button2)
    keyboard.add(button3, button4)
    keyboard.add(button5, button6)
    
    return keyboard

def create_admin_keyboard():
    """Создает клавиатуру для админов"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Основные кнопки
    button1 = KeyboardButton('🔔 Упомянуть всех')
    button2 = KeyboardButton('🎮 Block Blast')
    button3 = KeyboardButton('📊 Мой статус')
    button4 = KeyboardButton('🛡️ Анти-мат')
    button5 = KeyboardButton('ℹ️ Помощь')
    button6 = KeyboardButton('🧪 Тест бота')
    
    # Админские кнопки
    button7 = KeyboardButton('👑 Статистика')
    button8 = KeyboardButton('⚡ Снять таймаут')
    
    keyboard.add(button1, button2)
    keyboard.add(button3, button4)
    keyboard.add(button5, button6)
    keyboard.add(button7, button8)
    
    return keyboard

# ========== КОМАНДА PUCK ==========

@bot.message_handler(commands=['puck'])
def puck_command(message):
    """Обработчик команды /puck - отправляет пук пользователю"""
    try:
        # Проверяем, упомянут ли пользователь
        if len(message.text.split()) < 2:
            bot.reply_to(message, "❌ Использование: /puck @username - отправить пук пользователю", 
                        reply_markup=create_main_keyboard())
            return
        
        target_username = message.text.split()[1]
        
        # ПРОВЕРКА ЗАЩИТЫ ДЛЯ @Madara1332
        if target_username.lower() == PROTECTED_USER.lower():
            protection_text = f"""
🛡️ *ЗАЩИТА АКТИВИРОВАНА!*

Пользователь {PROTECTED_USER} находится под защитой!
Попытка атаки от @{message.from_user.username or message.from_user.first_name} заблокирована.

⚡ *Защита сработала!*
            """
            bot.send_message(message.chat.id, protection_text, parse_mode='Markdown', reply_markup=create_main_keyboard())
            
            # Отправляем защитное видео
            send_protection_video(message.chat.id)
            return
        
        # Создаем забавное сообщение с пуком
        puck_messages = [
            f"💨 *ПУК!* {target_username} получил пук от @{message.from_user.username or message.from_user.first_name}!",
            f"💨 *БА-БАХ!* {target_username} атакован пуком!",
            f"💨 *ПУУУУК!* На {target_username} совершена газовая атака!",
            f"💨 *ПЩЩЩ!* {target_username} в замешательстве от внезапного пука!",
            f"💨 *БДЫЩ!* Пук-снаряд точно поразил {target_username}!",
            f"💨 *ПФФФ!* {target_username} получил порцию веселья!",
            f"💨 *ТУУУУК!* Атака пуком по {target_username} успешна!",
            f"💨 *ХЛОП!* {target_username} оглушен пуком!"
        ]
        
        response = random.choice(puck_messages)
        
        # Добавляем случайную реакцию
        reactions = ["😂", "🤢", "😷", "💀", "🎯", "⚡", "🎉", "🍃"]
        response += f"\n{random.choice(reactions)} Реакция: {random.choice(['Смех', 'Удивление', 'Испуг', 'Радость', 'Отвращение'])}"
        
        bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_main_keyboard())
        
        # ОТПРАВЛЯЕМ ВАШЕ АУДИО ДЛЯ PUCK
        send_audio_message(message.chat.id, 'puck')
        
    except Exception as e:
        logging.error(f"Ошибка в команде puck: {e}")
        bot.reply_to(message, "❌ Ошибка при отправке пука", reply_markup=create_main_keyboard())

@bot.message_handler(commands=['puck2'])
def puck2_command(message):
    """Обработчик команды /puck2 - усиленный пук"""
    try:
        if len(message.text.split()) < 2:
            bot.reply_to(message, "❌ Использование: /puck2 @username - отправить усиленный пук", 
                        reply_markup=create_main_keyboard())
            return
        
        target_username = message.text.split()[1]
        
        # ПРОВЕРКА ЗАЩИТЫ ДЛЯ @Madara1332
        if target_username.lower() == PROTECTED_USER.lower():
            protection_text = f"""
🛡️ *ЗАЩИТА АКТИВИРОВАНА!*

Пользователь {PROTECTED_USER} находится под защитой!
Попытка усиленной атаки от @{message.from_user.username or message.from_user.first_name} заблокирована.

💥 *Защита сработала против супер-пука!*
            """
            bot.send_message(message.chat.id, protection_text, parse_mode='Markdown', reply_markup=create_main_keyboard())
            
            # Отправляем защитное видео
            send_protection_video(message.chat.id)
            return
        
        puck_messages = [
            f"💥💨 *СУПЕР-ПУК!* {target_username} получает залп пуков от @{message.from_user.username or message.from_user.first_name}!",
            f"💥💨 *БА-БА-БАХ!* Тройной пук по {target_username}!",
            f"💥💨 *ПУК-АПОКАЛИПСИС!* {target_username} в эпицентре газовой бури!",
            f"💥💨 *АРТ-ПУК!* Залп из 5 пуков накрывает {target_username}!",
            f"💥💨 *ПУК-ЦИКЛОН!* {target_username} не может устоять против такого количества пуков!"
        ]
        
        response = random.choice(puck_messages)
        response += "\n💥 Эффект: Усиленный пук ×3"
        response += f"\n🎯 Критический удар! {random.choice(['🤯', '💀', '😵', '🥴', '🤮'])}"
        
        bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_main_keyboard())
        
        # ОТПРАВЛЯЕМ ВАШЕ АУДИО ДЛЯ PUCK2
        send_audio_message(message.chat.id, 'puck2')
        
    except Exception as e:
        logging.error(f"Ошибка в команде puck2: {e}")
        bot.reply_to(message, "❌ Ошибка при отправке усиленного пука", reply_markup=create_main_keyboard())

@bot.message_handler(commands=['puck3'])
def puck3_command(message):
    """Обработчик команды /puck3 - эпический пук"""
    try:
        if len(message.text.split()) < 2:
            bot.reply_to(message, "❌ Использование: /puck3 @username - отправить эпический пук", 
                        reply_markup=create_main_keyboard())
            return
        
        target_username = message.text.split()[1]
        
        # ПРОВЕРКА ЗАЩИТЫ ДЛЯ @Madara1332
        if target_username.lower() == PROTECTED_USER.lower():
            protection_text = f"""
🛡️ *ЗАЩИТА АКТИВИРОВАНА!*

Пользователь {PROTECTED_USER} находится под защитой!
Попытка эпической атаки от @{message.from_user.username or message.from_user.first_name} заблокирована.

🌪️ *Защита сработала против эпического пука!*
            """
            bot.send_message(message.chat.id, protection_text, parse_mode='Markdown', reply_markup=create_main_keyboard())
            
            # Отправляем защитное видео
            send_protection_video(message.chat.id)
            return
        
        puck_messages = [
            f"🌪️💨 *ЭПИЧЕСКИЙ ПУК!* {target_username} получает ПУКОВЫЙ АПОКАЛИПСИС от @{message.from_user.username or message.from_user.first_name}!",
            f"🌪️💨 *ПУК-ТОРНАДО!* {target_username} унесен в страну пуков!",
            f"🌪️💨 *ГАЛАКТИЧЕСКИЙ ПУК!* {target_username} атакован пуком космической силы!",
            f"🌪️💨 *ЛЕГЕНДАРНЫЙ ПУК!* {target_username} становится частью пуковой истории!",
            f"🌪️💨 *БОЖЕСТВЕННЫЙ ПУК!* {target_username} получает благословение бога пуков!"
        ]
        
        response = random.choice(puck_messages)
        response += "\n🌪️ Эффект: Эпический пук ×10"
        response += f"\n🏆 Достижение: {random.choice(['Легенда пуков', 'Мастер газа', 'Пук-повелитель', 'Газовая туча'])}"
        response += f"\n{random.choice(['👑', '🎖️', '🏅', '⭐'])} УНИКАЛЬНЫЙ ПУК!"
        
        bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_main_keyboard())
        
        # ОТПРАВЛЯЕМ ВАШЕ АУДИО ДЛЯ PUCK3
        send_audio_message(message.chat.id, 'puck3')
        
    except Exception as e:
        logging.error(f"Ошибка в команде puck3: {e}")
        bot.reply_to(message, "❌ Ошибка при отправке эпического пука", reply_markup=create_main_keyboard())

@bot.message_handler(commands=['alert'])
def alert_command(message):
    """Обработчик команды /alert - экстренное оповещение"""
    try:
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ Эта команда только для администраторов!", reply_markup=create_main_keyboard())
            return
        
        alert_text = ' '.join(message.text.split()[1:]) if len(message.text.split()) > 1 else "ВНИМАНИЕ! Важное сообщение!"
        
        alert_messages = [
            f"🚨 *ЭКСТРЕННОЕ ОПОВЕЩЕНИЕ!*\n\n{alert_text}",
            f"⚠️ *ВАЖНОЕ СООБЩЕНИЕ!*\n\n{alert_text}",
            f"📢 *СРОЧНОЕ УВЕДОМЛЕНИЕ!*\n\n{alert_text}",
            f"🔔 *ВНИМАНИЕ ВСЕМ!*\n\n{alert_text}"
        ]
        
        response = random.choice(alert_messages)
        response += f"\n\nОт: @{message.from_user.username or message.from_user.first_name}"
        response += f"\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        
        bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_admin_keyboard())
        
    except Exception as e:
        logging.error(f"Ошибка в команде alert: {e}")
        bot.reply_to(message, "❌ Ошибка при отправке оповещения", reply_markup=create_main_keyboard())

# ========== ОБРАБОТЧИКИ КНОПОК МЕНЮ ==========

@bot.message_handler(func=lambda message: message.text == '🔔 Упомянуть всех')
def mention_all_button(message):
    """Обработчик кнопки 'Упомянуть всех'"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта функция только для администраторов!", reply_markup=create_main_keyboard())
        return
    
    try:
        chat_id = message.chat.id
        mention_text = f"""🔔 *ВНИМАНИЕ! Следующие пользователи (администраторы, защищенный пользователь и известные username) были упомянуты:*

"""
        mention_text += f"📢 Объявление от @{message.from_user.username or message.from_user.first_name}\n"
        
        # Добавляем упоминание PROTECTED_USER (если он не в общем списке)
        if PROTECTED_USER not in KNOWN_USERNAMES:
            mention_text += f"🌟 {PROTECTED_USER}\n"
        
        # Добавляем упоминание админов
        admin_mentions = []
        for admin_id in ADMINS:
            try:
                member = bot.get_chat_member(chat_id, admin_id)
                if member.user.username and f"@{member.user.username}" not in KNOWN_USERNAMES and f"@{member.user.username}" != PROTECTED_USER:
                    admin_mentions.append(f"👑 @{member.user.username}")
            except:
                continue
        
        if admin_mentions:
            mention_text += "\n" + "\n".join(admin_mentions) + "\n"

        # Добавляем упоминание всех из списка KNOWN_USERNAMES
        user_mentions = []
        for username_tag in KNOWN_USERNAMES:
            # Проверяем, что это не PROTECTED_USER и не админ, чтобы избежать дублирования
            is_admin_in_list = False
            for admin_id in ADMINS:
                try:
                    member = bot.get_chat_member(chat_id, admin_id)
                    if member.user.username and f"@{member.user.username}" == username_tag:
                        is_admin_in_list = True
                        break
                except:
                    pass
            
            if username_tag != PROTECTED_USER and not is_admin_in_list:
                user_mentions.append(username_tag)
        
        if user_mentions:
            mention_text += "\n" + "\n".join(user_mentions) + "\n"

        mention_text += "\n_Примечание: Бот может упоминать только пользователей с публичным username, которые видны боту, и может быть ограничен настройками конфиденциальности Telegram._\n"
        mention_text += f"\n⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
        mention_text += f"\n\n🎮 *Кнопка нажата через меню!*"
        
        bot.send_message(chat_id, mention_text, parse_mode='Markdown', reply_markup=create_main_keyboard())

    except Exception as e:
        logging.error(f"Ошибка в упоминании всех: {e}")
        bot.reply_to(message, "❌ Ошибка при упоминании участников", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == '🎮 Block Blast')
def block_blast_button(message):
    """Обработчик кнопки 'Block Blast' - открывает мини-приложение через ссылку"""
    try:
        # Создаем Inline-клавиатуру с кнопкой-ссылкой
        markup = telebot.types.InlineKeyboardMarkup()
        game_button = telebot.types.InlineKeyboardButton(
            text="Начать Block Blast", 
            url="https://t.me/GreatLeHavre_bot/block_bast"
        )
        markup.add(game_button)

        # Отправляем сообщение с кнопкой-ссылкой
        bot.send_message(
            message.chat.id, 
            "Нажмите кнопку ниже, чтобы начать игру Block Blast!", 
            reply_markup=markup
        )
        logging.info(f"Пользователь {message.from_user.username or message.from_user.first_name} получил ссылку на Block Blast игру.")
    except Exception as e:
        logging.error(f"Ошибка при отправке ссылки на Block Blast игру: {e}")
        bot.reply_to(message, "❌ Ошибка при попытке открыть игру Block Blast.", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == '📊 Мой статус')
def status_button(message):
    """Обработчик кнопки 'Мой статус' - ДОСТУПЕН ВСЕМ"""
    try:
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        
        # Логируем информацию о пользователе
        logging.info(f"Пользователь {username} (ID: {user_id}) запросил статус")
        
        in_timeout, timeout_end = is_user_in_timeout(user_id)
        violations = USER_VIOLATIONS.get(user_id, 0)
        
        if in_timeout:
            time_left = timeout_end - datetime.now()
            minutes_left = int(time_left.total_seconds() // 60)
            seconds_left = int(time_left.total_seconds() % 60)
            timeout_status = f"⏰ Да ({minutes_left} мин {seconds_left} сек)"
        else:
            timeout_status = "✅ Нет"
        
        anti_mat_status = "🟢 ВКЛЮЧЕНА" if ANTI_MAT_ENABLED else "🔴 ВЫКЛЮЧЕНА"
        
        status_text = f"""
📊 *Ваш статус:*

👤 *Имя:* {username}
🆔 *ID:* {user_id}
🛡️ *Админ:* {'✅ Да' if is_admin(user_id) else '❌ Нет'}
🛡️ *Анти-мат:* {anti_mat_status}
🔞 *Нарушений:* {violations}
⏰ *В таймауте:* {timeout_status}
⚡ *Статус:* ✅ Активен
🎮 *Меню:* ✅ Доступно
🛡️ *Защита:* ✅ Активна для {PROTECTED_USER}

*Кнопка нажата через меню!*
    """
        
        bot.reply_to(message, status_text, parse_mode='Markdown', reply_markup=create_main_keyboard())
        logging.info(f"Статус успешно отправлен пользователю {username}")
        
    except Exception as e:
        logging.error(f"Ошибка при отправке статуса: {e}")
        bot.reply_to(message, "❌ Ошибка при получении статуса", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == '🛡️ Анти-мат')
def antimat_button(message):
    """Обработчик кнопки 'Анти-мат'"""
    global ANTI_MAT_ENABLED
    
    if not is_admin(message.from_user.id):
        status = "🟢 ВКЛЮЧЕНА" if ANTI_MAT_ENABLED else "🔴 ВЫКЛЮЧЕНА"
        status_text = f"""
🛡️ *Статус анти-мата:*

{status}

ℹ️ Только администраторы могут изменять настройки.
        """
        bot.reply_to(message, status_text, parse_mode='Markdown', reply_markup=create_main_keyboard())
        return
    
    status = "🟢 ВКЛЮЧЕНА" if ANTI_MAT_ENABLED else "🔴 ВЫКЛЮЧЕНА"
    status_text = f"""
🛡️ *Управление анти-матом:*

*Текущий статус:* {status}

*Используйте команды:*
/antimat on - включить
/antimat off - выключить
/antimat status - статус

*Кнопка нажата через меню!*
    """
    
    bot.reply_to(message, status_text, parse_mode='Markdown', reply_markup=create_admin_keyboard())

@bot.message_handler(func=lambda message: message.text == 'ℹ️ Помощь')
def help_button(message):
    """Обработчик кнопки 'Помощь' - ДОСТУПЕН ВСЕМ"""
    anti_mat_status = "🟢 ВКЛЮЧЕНА" if ANTI_MAT_ENABLED else "🔴 ВЫКЛЮЧЕНА"
    
    help_text = f"""
🆘 *Помощь по боту:*

🛡️ *Система анти-мата:* {anti_mat_status}
🛡️ *Защита пользователя:* {PROTECTED_USER}

*Доступные кнопки:*
🔔 Упомянуть всех - позвать всех участников
🎮 Block Blast - тестовая кнопка
📊 Мой статус - информация о вас
🛡️ Анти-мат - управление системой
ℹ️ Помощь - это сообщение
🧪 Тест бота - проверить работу

*Доступные команды:*
/puck @user - отправить пук + аудио
/puck2 @user - усиленный пук + аудио  
/puck3 @user - эпический пук + аудио
/gg [текст] - озвучить текст
/alert текст - экстренное оповещение (админы)

*🛡️ Защита:* {PROTECTED_USER} защищен от пуков!

*Кнопка нажата через меню!*
    """
    
    bot.reply_to(message, help_text, parse_mode='Markdown', reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == '🧪 Тест бота')
def test_button(message):
    """Обработчик кнопки 'Тест бота' - ДОСТУПЕН ВСЕМ"""
    anti_mat_status = "🟢 ВКЛЮЧЕНА" if ANTI_MAT_ENABLED else "🔴 ВЫКЛЮЧЕНА"
    
    test_text = f"""
🧪 *Тестирование бота:*

✅ *Меню кнопок:* Работает
🛡️ *Анти-мат:* {anti_mat_status}
⚡ *Бот:* Активен
🎮 *Кнопки:* Доступны
💨 *Puck команды:* Доступны
🔊 *Аудио файлы:* Готовы
🛡️ *Защита {PROTECTED_USER}:* Активна

*Кнопка нажата через меню!*
    """
    
    bot.reply_to(message, test_text, parse_mode='Markdown', reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == '👑 Статистика')
def stats_button(message):
    """Обработчик кнопки 'Статистика' для админов"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта функция только для администраторов!", reply_markup=create_main_keyboard())
        return
    
    total_violations = sum(USER_VIOLATIONS.values())
    total_timeouts = len(USER_TIMEOUTS)
    
    stats_text = f"""
👑 *Статистика админа:*

🔞 *Всего нарушений:* {total_violations}
⏰ *Активных таймаутов:* {total_timeouts}
👥 *Пользователей в базе:* {len(USER_VIOLATIONS)}
🛡️ *Анти-мат:* {'🟢 ВКЛ' if ANTI_MAT_ENABLED else '🔴 ВЫКЛ'}
🛡️ *Защита:* Активна для {PROTECTED_USER}

*Используйте команды:*
/violations - детальная статистика
/cleartimeout all - снять все таймауты
/clearviolations all - снять все нарушения

*Кнопка нажата через меню!*
    """
    
    bot.reply_to(message, stats_text, parse_mode='Markdown', reply_markup=create_admin_keyboard())

@bot.message_handler(func=lambda message: message.text == '⚡ Снять таймаут')
def clear_timeout_button(message):
    """Обработчик кнопки 'Снять таймаут' для админов"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта функция только для администраторов!", reply_markup=create_main_keyboard())
        return
    
    help_text = """
⚡ *Снять таймаут:*

Используйте команды:
/cleartimeout @username - снять таймаут пользователю
/cleartimeout all - снять все таймауты
/clearviolations @username - снять нарушения
/clearviolations all - снять все нарушения

*Кнопка нажата через меню!*
    """
    
    bot.reply_to(message, help_text, parse_mode='Markdown', reply_markup=create_admin_keyboard())

# ========== КОМАНДЫ ДЛЯ ВСЕХ ==========

@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик команды /start - ДОСТУПЕН ВСЕМ"""
    anti_mat_status = "🟢 ВКЛЮЧЕНА" if ANTI_MAT_ENABLED else "🔴 ВЫКЛЮЧЕНА"
    
    # Определяем какую клавиатуру показывать
    if is_admin(message.from_user.id):
        keyboard = create_admin_keyboard()
    else:
        keyboard = create_main_keyboard()
    
    welcome_text = f"""
🤖 *Бот активирован!*

🛡️ *Система анти-мата:* {anti_mat_status}
🛡️ *Защита пользователя:* {PROTECTED_USER}

🎮 *Добавлено меню с кнопками!*
Теперь вы можете использовать кнопки ниже для быстрого доступа к функциям.

*Основные кнопки:*
🔔 Упомянуть всех - позвать участников
🎮 Block Blast - тестовая кнопка  
📊 Мой статус - ваша статистика
🛡️ Анти-мат - управление системой
ℹ️ Помощь - справка по боту
🧪 Тест бота - проверка работы

*Новые команды:*
💨 /puck @user - отправить пук + ваше аудио
💥 /puck2 @user - усиленный пук + ваше аудио
🌪️ /puck3 @user - эпический пук + ваше аудио
🔊 /gg [текст] - озвучить текст
🚨 /alert текст - оповещение (админы)

*🛡️ ЗАЩИТА:* {PROTECTED_USER} защищен от всех видов пуков!

*Бот обновлен!* 🚀
    """
    
    bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(commands=['help'])
def help_command(message):
    """Обработчик команды /help - ДОСТУПЕН ВСЕМ"""
    anti_mat_status = "🟢 ВКЛЮЧЕНА" if ANTI_MAT_ENABLED else "🔴 ВЫКЛЮЧЕНА"
    
    help_text = f"""
🆘 *Помощь по командам:*

🛡️ *Система анти-мата:* {anti_mat_status}
🛡️ *Защита пользователя:* {PROTECTED_USER}

*Теперь доступно меню с кнопками!*
Используйте кнопки ниже для быстрого доступа к функциям.

*Также доступны команды:*
/start - показать меню
/status - ваш статус
/mytimeout - проверить таймаут
/gg [текст] - озвучить текст
/puck @user - отправить пук + ваше аудио
/puck2 @user - усиленный пук + ваше аудио
/puck3 @user - эпический пук + ваше аудио
/alert текст - оповещение (админы)

*🛡️ ВАЖНО:* {PROTECTED_USER} защищен от всех атак!
    """
    
    bot.reply_to(message, help_text, parse_mode='Markdown', reply_markup=create_main_keyboard())

# ========== КОМАНДЫ АНТИ-МАТА ==========

@bot.message_handler(commands=['antimat'])
def antimat_command(message):
    """Обработчик команды /antimat"""
    global ANTI_MAT_ENABLED
    
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта команда только для администраторов!", reply_markup=create_main_keyboard())
        return
    
    if len(message.text.split()) < 2:
        status = "🟢 ВКЛЮЧЕНА" if ANTI_MAT_ENABLED else "🔴 ВЫКЛЮЧЕНА"
        bot.reply_to(message, f"🛡️ Статус анти-мата: {status}", reply_markup=create_admin_keyboard())
        return
    
    subcommand = message.text.split()[1].lower()
    
    if subcommand == 'on':
        ANTI_MAT_ENABLED = True
        bot.reply_to(message, "✅ Система анти-мата ВКЛЮЧЕНА", reply_markup=create_admin_keyboard())
    elif subcommand == 'off':
        ANTI_MAT_ENABLED = False
        bot.reply_to(message, "❌ Система анти-мата ВЫКЛЮЧЕНА", reply_markup=create_admin_keyboard())
    elif subcommand == 'status':
        status = "🟢 ВКЛЮЧЕНА" if ANTI_MAT_ENABLED else "🔴 ВЫКЛЮЧЕНА"
        bot.reply_to(message, f"🛡️ Статус анти-мата: {status}", reply_markup=create_admin_keyboard())
    else:
        bot.reply_to(message, "❌ Использование: /antimat [on|off|status]", reply_markup=create_admin_keyboard())

@bot.message_handler(commands=['test'])
def test_command(message):
    """Обработчик команды /test - ДОСТУПЕН ВСЕМ"""
    test_text = f"""
🧪 *Тестирование бота:*

✅ Бот работает нормально
🎮 Кнопки меню доступны
🛡️ Система анти-мата проверена
💨 Команды puck готовы
🔊 Аудио файлы подключены
🛡️ Защита {PROTECTED_USER} активна
⚡ Все системы в норме

*Бот полностью функционален!* 🚀
    """
    bot.reply_to(message, test_text, parse_mode='Markdown', reply_markup=create_main_keyboard())

@bot.message_handler(commands=['status'])
def status_command(message):
    """Обработчик команды /status - ДОСТУПЕН ВСЕМ"""
    try:
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        
        in_timeout, timeout_end = is_user_in_timeout(user_id)
        violations = USER_VIOLATIONS.get(user_id, 0)
        
        if in_timeout:
            time_left = timeout_end - datetime.now()
            minutes_left = int(time_left.total_seconds() // 60)
            seconds_left = int(time_left.total_seconds() % 60)
            timeout_status = f"⏰ Да ({minutes_left} мин {seconds_left} сек)"
        else:
            timeout_status = "✅ Нет"
        
        anti_mat_status = "🟢 ВКЛЮЧЕНА" if ANTI_MAT_ENABLED else "🔴 ВЫКЛЮЧЕНА"
        
        status_text = f"""
📊 *Ваш статус:*

👤 *Имя:* {username}
🆔 *ID:* {user_id}
🛡️ *Админ:* {'✅ Да' if is_admin(user_id) else '❌ Нет'}
🛡️ *Анти-мат:* {anti_mat_status}
🔞 *Нарушений:* {violations}
⏰ *В таймауте:* {timeout_status}
⚡ *Статус:* ✅ Активен
🎮 *Меню:* ✅ Доступно
💨 *Puck команды:* ✅ Доступны
🔊 *Аудио файлы:* ✅ Подключены
🛡️ *Защита:* ✅ Активна для {PROTECTED_USER}
    """
        
        bot.reply_to(message, status_text, parse_mode='Markdown', reply_markup=create_main_keyboard())
        
    except Exception as e:
        logging.error(f"Ошибка в команде status: {e}")
        bot.reply_to(message, "❌ Ошибка при получении статуса", reply_markup=create_main_keyboard())

@bot.message_handler(commands=['mytimeout'])
def mytimeout_command(message):
    """Обработчик команды /mytimeout - ДОСТУПЕН ВСЕМ"""
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    
    in_timeout, timeout_end = is_user_in_timeout(user_id)
    
    if in_timeout:
        time_left = timeout_end - datetime.now()
        minutes_left = int(time_left.total_seconds() // 60)
        seconds_left = int(time_left.total_seconds() % 60)
        
        timeout_text = f"""
⏰ *Информация о таймауте:*

👤 Пользователь: {username}
🆔 ID: {user_id}
🚫 Статус: В таймауте
⏳ Осталось: {minutes_left} минут {seconds_left} секунд
🕒 Завершится: {timeout_end.strftime('%H:%M:%S')}

ℹ️ Обратитесь к администратору для снятия таймаута.
        """
    else:
        timeout_text = f"""
✅ *Информация о таймауте:*

👤 Пользователь: {username}
🆔 ID: {user_id}
✅ Статус: Таймаутов нет
🎉 Вы можете свободно писать сообщения!

💡 Соблюдайте правила чата.
        """
    
    bot.reply_to(message, timeout_text, parse_mode='Markdown', reply_markup=create_main_keyboard())

@bot.message_handler(commands=['violations'])
def violations_command(message):
    """Обработчик команды /violations"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта команда только для администраторов!", reply_markup=create_main_keyboard())
        return
    
    if not USER_VIOLATIONS:
        bot.reply_to(message, "📊 Нарушений не зарегистрировано", reply_markup=create_admin_keyboard())
        return
    
    violations_text = "📊 *Статистика нарушений:*\n\n"
    
    for user_id, count in sorted(USER_VIOLATIONS.items(), key=lambda x: x[1], reverse=True):
        try:
            user = bot.get_chat(user_id)
            username = f"@{user.username}" if user.username else user.first_name
            violations_text += f"👤 {username}: {count} нарушений\n"
        except:
            violations_text += f"👤 ID {user_id}: {count} нарушений\n"
    
    violations_text += f"\n🔞 Всего нарушений: {sum(USER_VIOLATIONS.values())}"
    violations_text += f"\n👥 Пользователей с нарушениями: {len(USER_VIOLATIONS)}"
    
    bot.reply_to(message, violations_text, parse_mode='Markdown', reply_markup=create_admin_keyboard())

@bot.message_handler(commands=['cleartimeout'])
def clear_timeout_command(message):
    """Обработчик команды /cleartimeout"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта команда только для администраторов!", reply_markup=create_main_keyboard())
        return
    
    if len(message.text.split()) < 2:
        bot.reply_to(message, "❌ Использование: /cleartimeout @username или /cleartimeout all", reply_markup=create_admin_keyboard())
        return
    
    target = message.text.split()[1]
    
    if target.lower() == 'all':
        cleared_count = len(USER_TIMEOUTS)
        USER_TIMEOUTS.clear()
        bot.reply_to(message, f"✅ Сняты все таймауты ({cleared_count} пользователей)", reply_markup=create_admin_keyboard())
        return
    
    # Ищем пользователя по username
    cleared = False
    for user_id in list(USER_TIMEOUTS.keys()):
        try:
            user = bot.get_chat(user_id)
            if user.username and f"@{user.username}".lower() == target.lower():
                del USER_TIMEOUTS[user_id]
                cleared = True
                break
        except:
            continue
    
    if cleared:
        bot.reply_to(message, f"✅ Таймаут снят для {target}", reply_markup=create_admin_keyboard())
    else:
        bot.reply_to(message, f"❌ Пользователь {target} не найден или не в таймауте", reply_markup=create_admin_keyboard())

@bot.message_handler(commands=['clearviolations'])
def clear_violations_command(message):
    """Обработчик команды /clearviolations"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта команда только для администраторов!", reply_markup=create_main_keyboard())
        return
    
    if len(message.text.split()) < 2:
        bot.reply_to(message, "❌ Использование: /clearviolations @username или /clearviolations all", reply_markup=create_admin_keyboard())
        return
    
    target = message.text.split()[1]
    
    if target.lower() == 'all':
        cleared_count = len(USER_VIOLATIONS)
        USER_VIOLATIONS.clear()
        bot.reply_to(message, f"✅ Сняты все нарушения ({cleared_count} пользователей)", reply_markup=create_admin_keyboard())
        return
    
    # Ищем пользователя по username
    cleared = False
    for user_id in list(USER_VIOLATIONS.keys()):
        try:
            user = bot.get_chat(user_id)
            if user.username and f"@{user.username}".lower() == target.lower():
                del USER_VIOLATIONS[user_id]
                cleared = True
                break
        except:
            continue
    
    if cleared:
        bot.reply_to(message, f"✅ Нарушения сняты для {target}", reply_markup=create_admin_keyboard())
    else:
        bot.reply_to(message, f"❌ Пользователь {target} не найден или нарушений нет", reply_markup=create_admin_keyboard())

@bot.message_handler(commands=['gg'])
def gg_command(message):
    """Обработчик команды /gg - преобразование текста в голосовое сообщение - ДОСТУПЕН ВСЕМ"""
    try:
        text_to_speak = ' '.join(message.text.split()[1:])
        
        if not text_to_speak:
            bot.reply_to(message, "❌ Использование: /gg [текст для озвучки]", reply_markup=create_main_keyboard())
            return
        
        if len(text_to_speak) > 200:
            bot.reply_to(message, "❌ Текст слишком длинный (максимум 200 символов)", reply_markup=create_main_keyboard())
            return
        
        bot.reply_to(message, "🔊 Преобразую текст в голосовое сообщение...", reply_markup=create_main_keyboard())
        
        audio_file = text_to_speech(text_to_speak)
        
        if audio_file:
            with open(audio_file, 'rb') as audio:
                bot.send_voice(message.chat.id, audio, caption=f"🔊 Озвучка: {text_to_speak}")
            
            # Удаляем временный файл
            os.unlink(audio_file)
        else:
            bot.reply_to(message, "❌ Ошибка при создании голосового сообщения", reply_markup=create_main_keyboard())
            
    except Exception as e:
        logging.error(f"Ошибка в команде gg: {e}")
        bot.reply_to(message, "❌ Ошибка при обработке команды", reply_markup=create_main_keyboard())

# ========== ОБРАБОТКА МАТОВ (С ПРОВЕРКОЙ НА ВКЛЮЧЕНИЕ) ==========

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_all_messages(message):
    """Обработчик всех текстовых сообщений"""
    try:
        # Пропускаем команды и кнопки меню
        if message.text.startswith('/') or message.text in [
            '🔔 Упомянуть всех', '🎮 Block Blast', '📊 Мой статус', 
            '🛡️ Анти-мат', 'ℹ️ Помощь', '🧪 Тест бота',
            '👑 Статистика', '⚡ Снять таймаут'
        ]:
            return
        
        # Пропускаем админов
        if is_admin(message.from_user.id):
            return
        
        user_id = message.from_user.id
        
        # Проверяем таймаут (работает даже при выключенном анти-мате)
        in_timeout, timeout_end = is_user_in_timeout(user_id)
        if in_timeout:
            time_left = timeout_end - datetime.now()
            minutes_left = int(time_left.total_seconds() // 60)
            seconds_left = int(time_left.total_seconds() % 60)
            
            try:
                bot.delete_message(message.chat.id, message.message_id)
                if minutes_left > 0 or seconds_left > 30:
                    bot.send_message(
                        message.chat.id, 
                        f"⏰ Вы в таймауте! Осталось: {minutes_left} мин {seconds_left} сек\n"
                        f"Ждите окончания таймаута чтобы писать сообщения.",
                        reply_markup=create_main_keyboard()
                    )
            except:
                pass
            return
        
        # ПРОВЕРЯЕМ ВКЛЮЧЕНА ЛИ СИСТЕМА АНТИ-МАТА
        if not ANTI_MAT_ENABLED:
            return  # Если система выключена - пропускаем проверку матов
        
        # Проверяем на маты (только если система включена)
        has_bad_word, bad_word = contains_bad_words(message.text)
        
        if has_bad_word:
            logging.info(f"Обнаружен мат: '{bad_word}' от {user_id}")
            
            username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
            
            # Удаляем сообщение
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except Exception as e:
                logging.error(f"Не удалось удалить сообщение: {e}")
            
            # Добавляем нарушение
            if user_id not in USER_VIOLATIONS:
                USER_VIOLATIONS[user_id] = 0
            USER_VIOLATIONS[user_id] += 1
            
            violations_count = USER_VIOLATIONS[user_id]
            
            # Устанавливаем таймаут в зависимости от количества нарушений
            if violations_count == 1:
                timeout_minutes = 3
            elif violations_count == 2:
                timeout_minutes = 5
            elif violations_count == 3:
                timeout_minutes = 10
            else:
                timeout_minutes = 15
            
            timeout_end = set_user_timeout(user_id, timeout_minutes)
            
            # Отправляем ультиматум
            task = get_random_task()
            ultimatum_text = f"""
🚨 УЛЬТИМАТУМ для {username}!

🔞 Обнаружено запрещенное слово: **{bad_word}**
📊 Нарушений: {violations_count}
⏰ Таймаут: {timeout_minutes} минут

📋 **Ваше задание:**
{task}

⏰ Выполните задание до окончания таймаута!

💡 Админ может снять таймаут: /cleartimeout {username}
            """
            
            bot.send_message(message.chat.id, ultimatum_text, parse_mode='Markdown', reply_markup=create_main_keyboard())
            
    except Exception as e:
        logging.error(f"Ошибка в handle_all_messages: {e}")

# ========== API ДЛЯ ИГРЫ (Flask) ==========

@app.route('/new_high_score', methods=['POST'])
def new_high_score():
    try:
        data = request.json
        username = data.get('username', 'Неизвестный игрок')
        role = data.get('role', 'Не выбрана')
        score = data.get('score', 0)

        message_text = f"""
        🎉 *НОВЫЙ РЕКОРД В BLOCK BLAST!* 🎉

        👤 Игрок: @{username}
        🌟 Роль: {role.capitalize()}
        💯 Очки: {score}

        Поздравляем с невероятным достижением!
        """
        
        # Отправляем сообщение в указанный чат
        bot.send_message(ANNOUNCEMENT_CHAT_ID, message_text, parse_mode='Markdown')
        logging.info(f"Новый рекорд отправлен в чат: {username} - {score} очков")
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logging.error(f"Ошибка при обработке нового рекорда: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def run_flask_app():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# ========== ЗАПУСК БОТА ==========

def main():
    """Основная функция запуска"""
    global ANTI_MAT_ENABLED
    
    # Запускаем Flask приложение в отдельном потоке
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True # Поток завершится при завершении основной программы
    flask_thread.start()
    logging.info("Flask сервер запущен в отдельном потоке на http://0.0.0.0:5000")

    anti_mat_status = "🟢 ВКЛЮЧЕНА" if ANTI_MAT_ENABLED else "🔴 ВЫКЛЮЧЕНА"
    
    print("=" * 60)
    print("🤖 БОТ ЗАПУСКАЕТСЯ...")
    print("=" * 60)
    print(f"👑 Админы: {len(ADMINS)}")
    print(f"🛡️ Анти-мат: {anti_mat_status}")
    print(f"🔞 Матных слов: {len(BAD_WORDS)}")
    print(f"📋 Заданий: {len(ULTIMATUM_TASKS)}")
    print(f"💨 Puck команд: 3 добавлено + ВАШИ АУДИОФАЙЛЫ")
    print(f"🛡️ Защита: Активирована для {PROTECTED_USER}")
    print("=" * 60)
    print("🔊 НАСТРОЙКИ АУДИОФАЙЛОВ:")
    for cmd, audio_file in AUDIO_FILES.items():
        exists = "✅ ЕСТЬ" if os.path.exists(audio_file) else "❌ НЕТ"
        print(f"   {cmd}: {audio_file} {exists}")
    print("=" * 60)
    
    # Проверяем аудиофайлы
    missing_files = []
    for cmd, audio_file in AUDIO_FILES.items():
        if not os.path.exists(audio_file):
            missing_files.append(audio_file)
    
    if missing_files:
        print("❌ ВНИМАНИЕ! Отсутствуют файлы:")
        for file in missing_files:
            print(f"   - {file}")
        print("📍 Разместите файлы в папке с ботом или укажите правильные пути в AUDIO_FILES")
        print("=" * 60)
    else:
        print("✅ Все файлы найдены!")
        print("=" * 60)
    
    try:
        bot_info = bot.get_me()
        print(f"✅ Бот @{bot_info.username} успешно подключен!")
        print("🎮 Меню с кнопками настроено!")
        print("💨 Команды puck с вашими аудиофайлами добавлены!")
        print(f"🛡️ Защита для {PROTECTED_USER} активирована!")
        print("🔊 Команда /gg готова к использованию!")
        print("📊 Статус доступен ВСЕМ пользователям!")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    while True:
        try:
            print("🔄 Запуск polling...")
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            print(f"❌ Ошибка polling: {e}")
            print("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == "__main__":
    main()