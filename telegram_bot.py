from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import aiogram.utils.markdown as md
from aiogram.types import ParseMode
from config import TOKEN
import configparser as cfg
import hhrequest as hr
import sqlite3 as sql
import json

# Переменная в которой хранится telegram bot
bot = Bot(token=TOKEN)
# Обработчик сообщений для бота
dp = Dispatcher(bot)
# Словарь с запросами загружается при отработки команды /list all
telbot: dict = {}
# Словарь с текущими запросами, которые не были отправлены на обработку
current_telbot: dict = {}
# Путь к файлу БД
sqlite_db: str = ""
# Путь к каталогу с файлами результатов запросов
file_folder: str = ""


@dp.message_handler(commands=['submit'])
async def process_start_command(message: types.Message):
    '''
        Функция обработки команды /start
    :param message: сообщение, полученное от пользователя
    '''
    user_id = message.from_user.id
    markup=types.ReplyKeyboardRemove()
    # Если текущий запрос сформирован, то отправляем его на обработку.
    # Для этого создаем запись в БД со статусом 0
    if current_telbot[user_id][0] and current_telbot[user_id][1]:
        add_request(current_telbot, message)
        # Посылаем сообщение пользователю
        await bot.send_message(message.chat.id,
                               md.text("Ваш запрос направлен на обработку.\nИспользуйте команду ",
                               md.bold("/list")," для проверки состояния вашего запроса."),
                               reply_markup = markup,
                               parse_mode = ParseMode.MARKDOWN)
    else:
        # Если текущий запрос сформирован не полностью, то посылаем сообщение об этом пользователю
        await message.reply("Ваш запрос сформирован не полностью. Должет быть указан регион и текст запроса.")


@dp.message_handler(commands=['help','start'])
async def process_help_command(message: types.Message):
    '''
        Функция обработки команды /help
    :param message: сообщение от пользователя
    '''
    markup=types.ReplyKeyboardRemove()
    # Посылаем пользователю список доступных команд
    await bot.send_message(
            message.chat.id,
            md.text(
                md.text("Cписок доступных команд:"),
                md.text(md.bold("\n/help"), " - вывод справочной информации"),
                md.text(md.bold("\n/start"), " - вывод справочной информации"),
                md.text(md.bold("\n/submit"), "- начать обработку запроса"),
                md.text(md.bold("\n/region"), "- с параметром - установить регион, без параметров - вывести текущий регион"),
                md.text(md.bold("\n/request"), "- с параметром - определить запрос, без параметров - вывести текущий запрос"),
                md.text(md.bold("\n/list"), "- вывести список всех запросов"),
                md.text(md.bold("\n/display"), "- с параметром - вывести результаты конкрентого запроса, без параметров - текущего запроса")

            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )


@dp.message_handler(commands=['region'])
async def process_start_command(message: types.Message):
    '''
        Функция обработки команды /region {param}
    :param message: сообщение от пользователя
    '''
    params = message.get_args()
    # Проверяем были ли заданы какие-нибудь аргументы
    if params:
        # Проверяем регион на правильность
        o_hhr = hr.HHRequest(None)
        try:
            o_hhr.set_region(params)
        except ValueError as ex:
            await message.reply(f"Регион: {params} не может быть установлен")
            return

        if current_telbot.get(message.from_user.id):
            current_telbot[message.from_user.id][0] = params
        else:
            current_telbot[message.from_user.id] = [params, None]

        await message.reply("Регион установлен.")
    else:
        # При отсутствии аргументов выводим текущее значение региона
        if current_telbot.get(message.from_user.id):
            if current_telbot[message.from_user.id][0]:
                await message.reply(f"Регион: {current_telbot[message.from_user.id][0]}")
            else:
                await message.reply("Регион не был установлен.")
        else:
            await message.reply("Регион не был установлен.")


@dp.message_handler(commands=['request'])
async def process_start_command(message: types.Message):
    '''
         Функция обработки команды /request {param}
    :param message: сообщение от пользователя
    '''
    params = message.get_args()
    # Если у сообщения есть параметр, то считаем его запросом
    markup=types.ReplyKeyboardRemove()
    if params:
        if current_telbot.get(message.from_user.id):
            current_telbot[message.from_user.id][1] = params
        else:
            current_telbot[message.from_user.id] = [None, params]
        await message.reply("Запрос установлен.")
    else:
        # Если у сообщения параметра нет, то выводим текущее значение запроса
        if current_telbot.get(message.from_user.id):
            if current_telbot[message.from_user.id][1]:
                await bot.send_message(message.chat.id,
                                       md.text("Текущий запрос: ",
                                               md.bold(current_telbot[message.from_user.id][1])),
                                       reply_markup=markup,
                                       parse_mode=ParseMode.MARKDOWN,)
            else:
                await message.reply("Запрос не был установлен.")
        else:
            await message.reply("Запрос не был установлен.")


@dp.message_handler(commands=['list'])
async def process_start_command(message: types.Message):
    '''
        Функция обработки команды /list
    :param message:
    '''
    params: str = message.get_args()
    # Если указан параметр, то выбираем все запросы из БД для этого пользователя
    markup = types.ReplyKeyboardRemove()
    # Читаем все запросы из БД
    get_all_requests(message)
    request_number: int = 1
    if telbot.get(message.from_user.id):
        await bot.send_message(message.chat.id, md.text('Список всех запросов:'))
        # Анализируем статус запроса
        for request in telbot[message.from_user.id]:
            if request[3] == 0:
                status = 'Инициализирован'
            elif request[3] == 1:
                status = "В обработке"
            elif request[3] == 2:
                status = "Завершен"
            else:
                status = "Неопределен"

            # Выводим краткую информацию о запросе
            await bot.send_message(message.chat.id,
                  md.text(
                      md.text('Номер: ', md.bold(request_number)),
                      md.text('Регион: ', md.bold(request[0])),
                      md.text('Запрос: ', md.bold(request[1])),
                      md.text('Количество вакансий: ', md.bold(request[2])),
                      md.text('Статус: ', md.bold(status)),
                      md.text('Создан: ', md.bold(request[4])),
                  ),
                  reply_markup=markup,
                  parse_mode=ParseMode.MARKDOWN,
                  )
            request_number += 1
    else:
        await bot.send_message(message.chat.id, md.text('Запросов не найдено'))

@dp.message_handler(commands=['display'])
async def display_result(message: types.message):
    '''
        Функция обработки команды /display {param}
    :param message: сообщение от пользоваетля
    '''
    arg: str = message.get_args()
    markup=types.ReplyKeyboardRemove()
    # Если параметр быд задан, и он является числом
    if arg:
        if arg.isnumeric():
            if telbot.get(message.from_user.id):
                if len(telbot.get(message.from_user.id)) >= int(arg) > 0:
                    row = telbot[message.from_user.id][int(arg)-1]
                    if row:
                        # Были ли найдены вакансии по этому запросу
                        if row[2]:
                            # Если запрос найден, то открываем файл с результатами
                            with open(file_folder + "/" + row[5], 'r') as f:
                                result: json = json.load(f)
                            # Формируем строки вывода
                            description_skills: dict = result['description']
                            key_skills: dict = result['keyskills']
                            salary_average: dict = result['salary']
                            # Для навыков из описания
                            sum_description: str = ""
                            for key, value in list(description_skills.items())[:10]:
                                sum_description += key + " - " + str(value) + "%\n"
                            # Для навыков из ключевых навыков
                            sum_keyskills: str = ""
                            for key, value in list(key_skills.items())[:10]:
                                sum_keyskills += key + " - " + str(value) + "%\n"
                            sum_salaries: str = ""
                            # Для зарплат
                            for key, value in salary_average.items():
                                sum_salaries += key + "   от: " + '{:6.0f}'.format(value[0]) + "₽.  до: " + '{:6.0f}'.format(value[1]) + "₽.\n"

                            # Выводим полученные результаты
                            sum_description = "10 навыков взятых из описания вакансии:\n\n" + sum_description
                            sum_keyskills = "10 знаний взятых из ключевых навыков:\n\n" + sum_keyskills
                            sum_salaries = "Усредненная зарплата для данной выборки:\n\n" + sum_salaries
                            await bot.send_message(message.chat.id, sum_description)
                            await bot.send_message(message.chat.id, sum_keyskills)
                            await bot.send_message(message.chat.id, sum_salaries)
                        else:
                            await bot.send_message(message.chat.id,
                                                   md.text("По этому запросу не найдено ни одной вакансии."))
                else:
                    # Если номер запроса указан неверно
                    await message.reply(f"Неверный параметр: {arg}")
            else:
                # Возможны случаи ( telegram bot ) был перезапущен, и запросы из
                # кэша пропали. Тогда нужно запустить команду /list all и кэш будет восстановлен
                await bot.send_message(message.chat.id,
                                       md.text("Необходимо обновить данные с помощью команды", md.bold("/list all")),
                                       reply_markup=markup,
                                       parse_mode=ParseMode.MARKDOWN,
                                       )
        else:
            # Если параметр не является числом, то выводим сообщение об ошибке
            await message.reply("Неправильный формат команды.")
    else:
        # Если у команды не было задано параметров, то выводим текущий запрос
        if current_telbot.get(message.from_user.id):
            region = str(current_telbot[message.from_user.id][0]).replace("None", "Не задан")
            request = str(current_telbot[message.from_user.id][1]).replace("None","Не задан")
            await bot.send_message(message.chat.id,
                                   md.text(
                                        md.text("Текущий запрос:\nрегион: ", md.bold(region)),
                                        md.text("\nзапрос: ", md.bold(request))
                                   ),
                                   reply_markup=markup,
                                   parse_mode=ParseMode.MARKDOWN,
                                   )
        else:
            await message.reply("Текущий запрос не сформирован.")

@dp.message_handler()
async def wrong_command(message: types.Message):
    '''
       Функция обработки ситуации, когда ни одна из команд не распознана
    :param message: Сообщение от пользователя
    '''
    await bot.send_message(message.from_user.id, "Команда не распознана!")


def add_request(telbot: dict, message: types.message):
    '''
        Функция добавляет запись запроса в БД
    :param telbot: словарь с текущими запросами
    :param message: сообщение от пользователя
    '''
    try:
        # Устанавливаем связь с БД
        db_connection = sql.connect(sqlite_db)
        cursor = db_connection.cursor()
    except Exception as ex:
        print(f"Error during establishing connection to DB\n{ex}")
        return

    # Проверяем есть ли такой пользователь в БД, если нет добавляем его
    sql_statement = '''SELECT * from users WHERE id=?'''
    cursor.execute(sql_statement, (message.from_user.id,))
    row = cursor.fetchone()
    if not row:
        sql_statement = '''INSERT INTO users(id,full_name,created) VALUES (?,?,datetime('now','localtime')) '''
        cursor.execute(sql_statement,(message.from_user.id,message.from_user.full_name))
        db_connection.commit()
    else:
        # Если пользователь существует, то заносим запрос на его имя и устанавливаем статус в Инициализирован
        sql_statement = '''INSERT INTO requests(user_id,region,text_request,status,created) VALUES (?,?,?,?,datetime('now','localtime'))'''
        cursor.execute(sql_statement, (message.from_user.id,
                                       current_telbot[message.from_user.id][0],
                                       current_telbot[message.from_user.id][1],
                                       0))
        db_connection.commit()
    # Закрываем соединение с БД
    cursor.close()
    db_connection.close()


def get_all_requests(message: types.message):
    '''
        Функция чтения всез запросов из БД для конкретного пользователя
    :param message: сообщение от пользователя
    '''
    try:
        # Устанавливаем связь с БД
        db_connection = sql.connect(sqlite_db, detect_types=sql.PARSE_DECLTYPES | sql.PARSE_COLNAMES)
        cursor = db_connection.cursor()
    except Exception as ex:
        print(f"Error during establishing connection to DB\n{ex}")
        return

    # Формируем и отправляем запрос к БД
    sql_statement = '''SELECT region, text_request, vacancy_number, status, created, file_name FROM requests WHERE user_id = ? ORDER BY created asc '''
    cursor.execute(sql_statement, (message.from_user.id,))
    rows = cursor.fetchall()
    # Заносим результаты запроса в кэш
    telbot[message.from_user.id] = rows
    # Закрываем связь с БД
    cursor.close()
    db_connection.close()


if __name__ == '__main__':

    # Читаем информацию из конфигурационного файла
    config = cfg.ConfigParser()
    config.read("hh_config.ini")
    sqlite_db = config["SQLite"]["path"]
    file_folder = config["Json"]["path"]
    # Запускаем telegram bot
    executor.start_polling(dp)
