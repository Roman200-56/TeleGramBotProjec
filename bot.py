import telebot
import openai
import sqlite3
import requests

# --- ТВОИ ТОКЕНЫ ---
TELEGRAM_TOKEN = '7753608741:AAGuR4R7wwwPKLgViJ-_nwnBLVk-FJ4r7KQ'
OPENAI_API_KEY = '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'
WEATHER_API_KEY = 'd7e728fd470cf320b445cd02e20d135f'
YOUTUBE_API_KEY = 'AIzaSyB3b6v9KDVlzjZNK63hcWfXcREULQ9e1n0'

# Настройка API
bot = telebot.TeleBot('7753608741:AAGuR4R7wwwPKLgViJ-_nwnBLVk-FJ4r7KQ')
openai.api_key = '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'

# База данных для расписаний
conn = sqlite3.connect('schedule.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS schedules (
    user_id INTEGER PRIMARY KEY,
    schedule TEXT
)
''')
conn.commit()

# --- Команды ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я умный бот.\nВот, что я умею:\n\n/weather — Погода\n/youtube — Найти видео\n/set_schedule — Задать расписание\n/my_schedule — Мое расписание\n/ask — Задать вопрос ChatGPT")

# --- ПОГОДА ---
@bot.message_handler(commands=['weather'])
def weather(message):
    bot.reply_to(message, "Напиши название города, чтобы узнать погоду:")

    bot.register_next_step_handler(message, get_weather)

def get_weather(message):
    city = message.text
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        bot.reply_to(message, f"Погода в {city}:\n{description.capitalize()}, {temp}°C")
    else:
        bot.reply_to(message, "Не удалось найти город. Попробуй ещё раз.")

# --- YOUTUBE ---
@bot.message_handler(commands=['youtube'])
def youtube(message):
    bot.reply_to(message, "Напиши запрос для поиска видео на YouTube:")

    bot.register_next_step_handler(message, search_youtube)

def search_youtube(message):
    query = message.text
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&key={YOUTUBE_API_KEY}&maxResults=1"
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        if result['items']:
            video_id = result['items'][0]['id']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            bot.reply_to(message, f"Вот, что я нашёл:\n{video_url}")
        else:
            bot.reply_to(message, "Видео не найдено.")
    else:
        bot.reply_to(message, "Ошибка при поиске видео.")

# --- РАСПИСАНИЕ ---
@bot.message_handler(commands=['set_schedule'])
def set_schedule(message):
    bot.reply_to(message, "Напиши своё расписание, и я его запомню:")

    bot.register_next_step_handler(message, save_schedule)

def save_schedule(message):
    user_id = message.from_user.id
    schedule_text = message.text

    cursor.execute('REPLACE INTO schedules (user_id, schedule) VALUES (?, ?)', (user_id, schedule_text))
    conn.commit()

    bot.reply_to(message, "Я сохранил твоё расписание!")

@bot.message_handler(commands=['my_schedule'])
def my_schedule(message):
    user_id = message.from_user.id
    cursor.execute('SELECT schedule FROM schedules WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        bot.reply_to(message, f"Вот твоё расписание:\n\n{result[0]}")
    else:
        bot.reply_to(message, "Ты ещё не установил расписание. Напиши /set_schedule чтобы добавить его.")

# --- CHATGPT ---
@bot.message_handler(commands=['ask'])
def ask(message):
    bot.reply_to(message, "Напиши свой вопрос для ChatGPT:")

    bot.register_next_step_handler(message, ask_gpt)

def ask_gpt(message):
    user_input = message.text
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # Быстрая версия
            messages=[{"role": "user", "content": user_input}],
            max_tokens=400
        )
        answer = response['choices'][0]['message']['content']
        bot.reply_to(message, answer)
    except Exception as e:
        bot.reply_to(message, "Произошла ошибка при обращении к ChatGPT.")

# --- Запуск ---
bot.polling(non_stop=True)

