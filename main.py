import logging  # Импортируем модуль логирования
from instagrapi import Client  # Импортируем класс Client из библиотеки instagrapi
import time  # Импортируем модуль для работы со временем
import telebot  # Импортируем библиотеку для работы с телеграм-ботом
from telebot import apihelper, types  # Импортируем вспомогательные функции и типы из telebot

# Настройка логирования
logging.basicConfig(level=logging.INFO)  # Устанавливаем уровень логирования на INFO
logger = logging.getLogger(__name__)  # Создаем объект логирования

# Настройка таймаута для TeleBot
apihelper.SESSION_TIME_TO_LIVE = 5 * 60  # Устанавливаем время жизни сессии на 5 минут
apihelper.TIMEOUT = 40  # Устанавливаем таймаут на 40 секунд

# Создаем объект бота Instagram
insta_bot = Client()  # Инициализируем объект клиента Instagram

# Создаем объект телеграм-бота
TELEGRAM_API_KEY = ‘API key’  # Замените на ваш реальный API ключ
tg_bot = telebot.TeleBot(TELEGRAM_API_KEY)  # Инициализируем объект телеграм-бота

# Переменные для хранения учетных данных Instagram
instagram_username = None  # Переменная для хранения имени пользователя Instagram
instagram_password = None  # Переменная для хранения пароля от Instagram

pause_task = False  # Переменная для паузы задания
stop_task = False  # Переменная для остановки задания

def load_commented_posts(filename="commented_posts.txt"):
    try:
        with open(filename, "r") as file:  # Открываем файл в режиме чтения
            return set(line.strip() for line in file)  # Возвращаем множество прокомментированных постов
    except FileNotFoundError:
        return set()  # Если файл не найден, возвращаем пустое множество

def save_commented_post(post_id, filename="commented_posts.txt"):
    with open(filename, "a") as file:  # Открываем файл в режиме добавления
        file.write(post_id + "\n")  # Записываем ID поста в файл

def follow_users_by_hashtag(hashtag, chat_id):
    tg_bot.send_message(chat_id, "Пожалуйста подождите немного, я обрабатываю ваш хэштег")  # Отправляем сообщение пользователю
    show_pause_stop_buttons(chat_id)  # Показываем кнопки паузы и остановки
    global stop_task
    stop_task = False  # Сбрасываем переменную остановки
    try:
        medias = insta_bot.hashtag_medias_recent(hashtag.strip('#'), amount=10)  # Получаем последние 10 постов по хэштегу
        for media in medias:
            if stop_task:
                break  # Если задание остановлено, прерываем цикл
            while pause_task:
                time.sleep(1)  # Если задание на паузе, ждем 1 секунду
            try:
                user_info = insta_bot.media_info(media.id).user  # Получаем информацию о пользователе
                insta_bot.user_follow(user_info.pk)  # Подписываемся на пользователя
                output = f"Пользователь: {user_info.username}\nПодписка успешно выполнена"
                logger.info(output)
                tg_bot.send_message(chat_id, output)  # Отправка сообщения в Telegram
                for _ in range(10):  # Задержка между действиями с возможностью прерывания
                    if stop_task:
                        break  # Если задание остановлено, прерываем цикл
                    while pause_task:
                        time.sleep(1)  # Если задание на паузе, ждем 1 секунду
                    time.sleep(10)  # Задержка в 1 секунду между подписками
            except Exception as e:
                error_output = f"Пользователь: {user_info.username}\nОшибка при подписке\nПричина: {str(e)}"
                logger.error(error_output)
                tg_bot.send_message(chat_id, error_output)  # Отправка сообщения об ошибке в Telegram
                if stop_task:
                    break  # Если задание остановлено, прерываем цикл
    except Exception as e:
        logger.error(f"Error during fetching media: {e}")
        tg_bot.send_message(chat_id, f"Ошибка при получении медиа: {e}")  # Отправка сообщения об ошибке в Telegram
    hide_pause_resume_buttons(chat_id)  # Скрываем кнопки паузы и возобновления
    show_service_choice(chat_id)  # Показываем выбор услуги

def like_posts_by_hashtag(hashtag, chat_id):
    tg_bot.send_message(chat_id, "Пожалуйста подождите немного, я обрабатываю ваш хэштег")  # Отправляем сообщение пользователю
    show_pause_stop_buttons(chat_id)  # Показываем кнопки паузы и остановки
    global stop_task
    stop_task = False  # Сбрасываем переменную остановки
    try:
        medias = insta_bot.hashtag_medias_recent(hashtag.strip('#'), amount=10)  # Получаем последние 10 постов по хэштегу
        for media in medias:
            if stop_task:
                break  # Если задание остановлено, прерываем цикл
            while pause_task:
                time.sleep(1)  # Если задание на паузе, ждем 1 секунду
            try:
                user_info = insta_bot.media_info(media.id).user  # Получаем информацию о пользователе
                insta_bot.media_like(media.id)  # Ставим лайк на пост
                media_url = f"https://www.instagram.com/p/{media.code}/"
                output = f"Пользователь: {user_info.username}\nПост: <a href='{media_url}'>{media.id}</a>\nЛайк успешно поставлен"
                logger.info(output)
                tg_bot.send_message(chat_id, output, parse_mode='HTML')  # Отправка сообщения в Telegram
                for _ in range(10):  # Задержка между действиями с возможностью прерывания
                    if stop_task:
                        break  # Если задание остановлено, прерываем цикл
                    while pause_task:
                        time.sleep(1)  # Если задание на паузе, ждем 1 секунду
                    time.sleep(1)  # Задержка в 1 секунду между лайками
            except Exception as e:
                error_output = f"Пост: {media.id}\nОшибка при постановке лайка\nПричина: {str(e)}"
                logger.error(error_output)
                tg_bot.send_message(chat_id, error_output)  # Отправка сообщения об ошибке в Telegram
                if stop_task:
                    break  # Если задание остановлено, прерываем цикл
    except Exception as e:
        logger.error(f"Error during fetching media: {e}")
        tg_bot.send_message(chat_id, f"Ошибка при получении медиа: {e}")  # Отправка сообщения об ошибке в Telegram
    hide_pause_resume_buttons(chat_id)  # Скрываем кнопки паузы и возобновления
    show_service_choice(chat_id)  # Показываем выбор услуги

def comment_on_posts_by_hashtag(hashtag, comment_text, chat_id):
    tg_bot.send_message(chat_id, "Пожалуйста подождите немного, я обрабатываю ваш хэштег")  # Отправляем сообщение пользователю
    show_pause_stop_buttons(chat_id)  # Показываем кнопки паузы и остановки
    commented_posts = load_commented_posts()  # Загружаем список уже прокомментированных постов
    global stop_task
    stop_task = False  # Сбрасываем переменную остановки
    try:
        medias = insta_bot.hashtag_medias_recent(hashtag.strip('#'), amount=10)  # Получаем последние 10 постов по хэштегу
        for media in medias:
            if stop_task:
                break  # Если задание остановлено, прерываем цикл
            while pause_task:
                time.sleep(1)  # Если задание на паузе, ждем 1 секунду
            if media.id in commented_posts:
                logger.info(f"Skipping post: {media.id} (already commented)")
                continue  # Пропускаем пост, если он уже был прокомментирован
            try:
                user_info = insta_bot.media_info(media.id).user  # Получаем информацию о пользователе
                insta_bot.media_comment(media.id, comment_text)  # Оставляем комментарий к посту
                save_commented_post(media.id)  # Сохраняем ID поста в файл
                media_url = f"https://www.instagram.com/p/{media.code}/"
                output = f"Пользователь: {user_info.username}\nПост: <a href='{media_url}'>{media.id}</a>\nКомментарий успешно оставлен"
                logger.info(output)
                tg_bot.send_message(chat_id, output, parse_mode='HTML')  # Отправка сообщения в Telegram
                for _ in range(10):  # Задержка между действиями с возможностью прерывания
                    if stop_task:
                        break  # Если задание остановлено, прерываем цикл
                    while pause_task:
                        time.sleep(1)  # Если задание на паузе, ждем 1 секунду
                    time.sleep(1)  # Задержка в 1 секунду между комментариями
            except Exception as e:
                error_output = f"Пользователь: {user_info.username}\nПост: {media.id}\nОшибка при комментировании\nПричина: {str(e)}"
                logger.error(error_output)
                tg_bot.send_message(chat_id, error_output)  # Отправка сообщения об ошибке в Telegram
                if stop_task:
                    break  # Если задание остановлено, прерываем цикл
    except Exception as e:
        logger.error(f"Error during fetching media: {e}")
        tg_bot.send_message(chat_id, f"Ошибка при получении медиа: {e}")  # Отправка сообщения об ошибке в Telegram
    hide_pause_resume_buttons(chat_id)  # Скрываем кнопки паузы и возобновления
    show_service_choice(chat_id)  # Показываем выбор услуги

def show_pause_stop_buttons(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)  # Создаем разметку для кнопок
    pause_button = types.KeyboardButton('Пауза')  # Создаем кнопку "Пауза"
    stop_button = types.KeyboardButton('Стоп')  # Создаем кнопку "Стоп"
    markup.add(pause_button, stop_button)  # Добавляем кнопки в разметку
    tg_bot.send_message(chat_id, "Вы можете приостановить или остановить выполнение задания:", reply_markup=markup)  # Отправляем сообщение с кнопками

def show_resume_button(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)  # Создаем разметку для кнопок
    resume_button = types.KeyboardButton('Продолжить')  # Создаем кнопку "Продолжить"
    stop_button = types.KeyboardButton('Стоп')  # Создаем кнопку "Стоп"
    markup.add(resume_button, stop_button)  # Добавляем кнопки в разметку
    tg_bot.send_message(chat_id, "Задание приостановлено. Нажмите 'Продолжить' для возобновления или 'Стоп' для остановки.", reply_markup=markup)  # Отправляем сообщение с кнопками

def hide_pause_resume_buttons(chat_id):
    markup = types.ReplyKeyboardRemove()  # Создаем разметку для удаления кнопок
    tg_bot.send_message(chat_id, "Задание завершено.", reply_markup=markup)  # Отправляем сообщение об окончании задания и удаляем кнопки

def show_service_choice(chat_id):
    msg = tg_bot.send_message(chat_id, "Выберите услугу:\n1. Подписка по хэштегу\n2. Лайки по хэштегу\n3. Комментарии по хэштегу\nВведите номер услуги:")  # Отправляем сообщение с выбором услуги
    tg_bot.register_next_step_handler(msg, handle_service_choice)  # Регистрируем следующий шаг для обработки выбора услуги

@tg_bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = tg_bot.reply_to(message, "Привет! Пожалуйста, введите ваш логин от Instagram:")  # Отправляем сообщение с запросом логина
    tg_bot.register_next_step_handler(msg, get_instagram_username)  # Регистрируем следующий шаг для получения логина

@tg_bot.message_handler(func=lambda message: message.text == 'Пауза')
def pause(message):
    global pause_task
    pause_task = True  # Ставим задание на паузу
    show_resume_button(message.chat.id)  # Показываем кнопку "Продолжить"

@tg_bot.message_handler(func=lambda message: message.text == 'Продолжить')
def resume(message):
    global pause_task
    pause_task = False  # Возобновляем задание
    show_pause_stop_buttons(message.chat.id)  # Показываем кнопки "Пауза" и "Стоп"

@tg_bot.message_handler(func=lambda message: message.text == 'Стоп')
def stop(message):
    global stop_task
    stop_task = True  # Останавливаем задание

def get_instagram_username(message):
    global instagram_username
    instagram_username = message.text  # Сохраняем введенный логин
    msg = tg_bot.reply_to(message, "Введите ваш пароль от Instagram:")  # Отправляем сообщение с запросом пароля
    tg_bot.register_next_step_handler(msg, get_instagram_password)  # Регистрируем следующий шаг для получения пароля

def get_instagram_password(message):
    global instagram_password
    instagram_password = message.text  # Сохраняем введенный пароль
    tg_bot.reply_to(message, "Пожалуйста подождите немного, я сейчас авторизуюсь")  # Отправляем сообщение о начале авторизации
    authenticate_instagram(message)  # Начинаем процесс авторизации

def authenticate_instagram(message):
    global insta_bot, instagram_username, instagram_password
    try:
        insta_bot.login(username=instagram_username, password=instagram_password)  # Пытаемся авторизоваться
        show_service_choice(message.chat.id)  # Показываем выбор услуги
    except Exception as e:
        if 'two-factor authentication required' in str(e):
            msg = tg_bot.reply_to(message, "Two-factor authentication required. Please enter the verification code:")  # Запрашиваем код двухфакторной аутентификации
            tg_bot.register_next_step_handler(msg, get_2fa_code)  # Регистрируем следующий шаг для получения кода
        else:
            tg_bot.reply_to(message, f"Ошибка авторизации: {e}")  # Отправляем сообщение об ошибке авторизации

def get_2fa_code(message):
    verification_code = message.text  # Сохраняем введенный код
    global insta_bot, instagram_username, instagram_password
    try:
        insta_bot.login(username=instagram_username, password=instagram_password, verification_code=verification_code)  # Пытаемся авторизоваться с кодом
        show_service_choice(message.chat.id)  # Показываем выбор услуги
    except Exception as e:
        tg_bot.reply_to(message, f"Ошибка авторизации с 2FA: {e}")  # Отправляем сообщение об ошибке авторизации

def handle_service_choice(message):
    try:
        service_choice = int(message.text)  # Преобразуем текстовое сообщение в число
        msg = tg_bot.reply_to(message, "Введите хэштег для выполнения услуги:")  # Запрашиваем хэштег
        tg_bot.register_next_step_handler(msg, lambda m: handle_hashtag(m, service_choice, message.chat.id))  # Регистрируем следующий шаг для получения хэштега
    except ValueError:
        tg_bot.reply_to(message, "Неверный выбор услуги. Пожалуйста, введите номер услуги (1, 2 или 3).")  # Отправляем сообщение об ошибке выбора
        show_service_choice(message.chat.id)  # Показываем выбор услуги

def handle_hashtag(message, service_choice, chat_id):
    user_hashtag = message.text  # Сохраняем введенный хэштег
    if service_choice == 1:
        follow_users_by_hashtag(user_hashtag, chat_id)  # Выполняем подписку по хэштегу
    elif service_choice == 2:
        like_posts_by_hashtag(user_hashtag, chat_id)  # Ставим лайки по хэштегу
    elif service_choice == 3:
        msg = tg_bot.reply_to(message, "Введите текст комментария:")  # Запрашиваем текст комментария
        tg_bot.register_next_step_handler(msg, lambda m: handle_comment(m, user_hashtag, chat_id))  # Регистрируем следующий шаг для получения комментария
    else:
        output = "Неверный выбор услуги. Пожалуйста, запустите программу снова и выберите правильный номер услуги."
        tg_bot.reply_to(message, output)  # Отправляем сообщение об ошибке выбора

def handle_comment(message, user_hashtag, chat_id):
    comment_text = message.text  # Сохраняем введенный комментарий
    comment_on_posts_by_hashtag(user_hashtag, comment_text, chat_id)  # Оставляем комментарии по хэштегу

# Запуск телеграм-бота с обработкой таймаутов
while True:
    try:
        tg_bot.polling(none_stop=True, interval=0, timeout=40)  # Запуск телеграм-бота с постоянным опросом
    except Exception as e:
        logger.error(f"Error occurred: {e}")  # Логирование ошибки
        time.sleep(15)  # Ожидание 15 секунд перед повторным запуском



