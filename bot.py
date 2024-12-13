import telebot
import json
import logging
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Реквизиты:
API_TOKEN = '7459907069:AAGl5sBVFKd8swOLh_Q5zV2YH0NkVzIZH2c'  # Замените на ваш реальный токен
DATA_FILE = 'data.json'  # Путь к файлу данных
USER_DATA_FILE = 'user_data.json'  # Путь к файлу с данными пользователей
BACK_BUTTON = "⬅️ Назад"  # Текст кнопки "Назад"

# Настройка логирования
logging.basicConfig(level=logging.INFO, filename='bot.log', format='%(asctime)s - %(message)s')

# Инициализация бота
bot = telebot.TeleBot(API_TOKEN)

# Загрузка данных
try:
    with open(DATA_FILE, 'r', encoding='utf-8') as file:
        data = json.load(file)
    logging.info("Данные загружены успешно из data.json")
except FileNotFoundError:
    logging.error("Файл data.json не найден!")
    data = {}

# Загрузка или инициализация данных пользователей
try:
    with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
        user_data = json.load(file)
    logging.info("Данные пользователей загружены успешно из user_data.json")
except FileNotFoundError:
    logging.warning("Файл user_data.json не найден, создается новый")
    user_data = {}

# Сохранение состояния пользователей
def save_user_data():
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(user_data, file, ensure_ascii=False, indent=4)
        logging.info("Данные пользователей успешно сохранены.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных: {e}")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    try:
        chat_id = message.chat.id
        user_data[chat_id] = {
            "city": None,
            "district": None,
            "product": None,
            "payment": None,
            "current_step": "start",
            "previous_step": None
        }
        save_user_data()
        bot.send_message(chat_id, "Привет! Выберите город:", reply_markup=city_markup())
        user_data[chat_id]['current_step'] = 'city'
        save_user_data()
    except Exception as e:
        logging.error(f"Ошибка при обработке команды /start: {e}")

# Генерация клавиатуры городов
def city_markup():
    try:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        if 'cities' in data and isinstance(data['cities'], list):
            for city in data['cities']:
                if isinstance(city, dict) and 'name' in city:
                    markup.add(KeyboardButton(city['name']))
                else:
                    logging.warning(f"Город с некорректной структурой: {city}")
        else:
            logging.warning("Некорректная структура для 'cities'")
        return markup
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры для выбора города: {e}")
        return ReplyKeyboardMarkup(resize_keyboard=True)

@bot.message_handler(func=lambda message: message.text in [city['name'] for city in data.get('cities', []) if isinstance(city, dict) and 'name' in city])
def city_handler(message):
    try:
        chat_id = message.chat.id
        city_name = message.text
        logging.info(f"Пользователь {chat_id} выбрал город: {city_name}")

        # Сохраняем выбранный город и переходим к выбору района
        user_data[chat_id]['city'] = city_name
        user_data[chat_id]['previous_step'] = 'city'
        user_data[chat_id]['current_step'] = 'district'
        save_user_data()

        # Генерация клавиатуры для выбора района
        bot.send_message(chat_id, "Выберите район:", reply_markup=district_markup(city_name))
    except Exception as e:
        logging.error(f"Ошибка при обработке выбора города: {e}")

# Генерация клавиатуры районов (с кнопкой "Назад")
def district_markup(city):
    try:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        city_data = next((item for item in data.get('cities', []) if isinstance(item, dict) and item.get('name') == city), None)

        if city_data and 'districts' in city_data:
            for district in city_data['districts']:
                markup.add(KeyboardButton(district))
        else:
            markup.add(KeyboardButton("Ошибка: Город или районы не найдены"))
        
        # Добавление кнопки "Назад"
        return add_back_button(markup, include_back=True)
    
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры для выбора района: {e}")
        return None  # Возвращаем None, если произошла ошибка

# Добавление кнопки "Назад" к клавиатуре
def add_back_button(markup, include_back):
    try:
        if include_back:
            markup.add(KeyboardButton(BACK_BUTTON))  # Добавляем кнопку "Назад"
        return markup
    except Exception as e:
        logging.error(f"Ошибка при добавлении кнопки 'Назад': {e}")
        return markup

@bot.message_handler(func=lambda message: message.text == BACK_BUTTON)
def back_handler(message):
    try:
        chat_id = message.chat.id
        current_step = user_data[chat_id].get('current_step')
        previous_step = user_data[chat_id].get('previous_step')

        logging.info(f"Пользователь {chat_id} вернулся на шаг: {previous_step}")

        if current_step == 'district':
            bot.send_message(chat_id, "Вернемся к выбору города.", reply_markup=city_markup())
            user_data[chat_id]['current_step'] = 'city'
        elif current_step == 'product':
            bot.send_message(chat_id, "Вернемся к выбору района.", reply_markup=district_markup(user_data[chat_id]['city']))
            user_data[chat_id]['current_step'] = 'district'
        elif current_step == 'payment':
            bot.send_message(chat_id, "Вернемся к выбору товара.", reply_markup=product_markup())
            user_data[chat_id]['current_step'] = 'product'

        save_user_data()
    except Exception as e:
        logging.error(f"Ошибка при обработке кнопки 'Назад': {e}")

# Обработчик выбора района
@bot.message_handler(func=lambda message: message.text in [district for city in data.get('cities', []) for district in city.get('districts', [])])
def district_handler(message):
    try:
        chat_id = message.chat.id
        selected_district = message.text
        selected_city = user_data[chat_id]['city']  # Получаем выбранный город

        # Сохраняем выбранный район в user_data
        user_data[chat_id]['district'] = selected_district
        user_data[chat_id]['previous_step'] = 'district'
        user_data[chat_id]['current_step'] = 'product'
        save_user_data()

        # Сообщение с выбором товара
        bot.send_message(chat_id, "Выберите товар:", reply_markup=product_markup())
    except Exception as e:
        logging.error(f"Ошибка при обработке выбора района: {e}")

# Генерация клавиатуры товаров
def product_markup():
    try:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        if 'products' in data:
            for product in data['products']:
                markup.add(KeyboardButton(f"{product['name']} - {product['price']}₽"))
        return add_back_button(markup, include_back=True)
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры для выбора товара: {e}")
        return ReplyKeyboardMarkup(resize_keyboard=True)

# Обработчик выбора товара
@bot.message_handler(func=lambda message: any(message.text.startswith(p['name']) for p in data.get('products', [])))
def product_handler(message):
    try:
        chat_id = message.chat.id
        selected_product = message.text
        user_data[chat_id]['product'] = selected_product
        user_data[chat_id]['previous_step'] = 'product'
        user_data[chat_id]['current_step'] = 'payment'
        save_user_data()

        # Переход к выбору метода оплаты
        bot.send_message(chat_id, "Выберите способ оплаты:", reply_markup=payment_markup())
    except Exception as e:
        logging.error(f"Ошибка при обработке выбора товара: {e}")
        # Генерация клавиатуры способов оплаты
def payment_markup():
    try:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        if 'payment_methods' in data:
            for method in data['payment_methods']:
                markup.add(KeyboardButton(method['name']))
        return add_back_button(markup, include_back=True)
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры для выбора способа оплаты: {e}")
        return ReplyKeyboardMarkup(resize_keyboard=True)

# Обработчик выбора способа оплаты
@bot.message_handler(func=lambda message: message.text in [method['name'] for method in data.get('payment_methods', [])])
def payment_handler(message):
    try:
        chat_id = message.chat.id
        payment_method_name = message.text
        method_data = next((item for item in data.get('payment_methods', []) if item.get('name') == payment_method_name), None)

        if method_data:
            bot.send_message(chat_id, method_data['details'])
        else:
            bot.send_message(chat_id, "Неизвестный способ оплаты.")
    except Exception as e:
        logging.error(f"Ошибка при обработке выбора способа оплаты: {e}")

# Запуск бота
try:
    bot.polling(none_stop=True)
except Exception as e:
    logging.error(f"Ошибка при запуске бота: {e}")
