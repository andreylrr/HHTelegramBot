from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from config import TOKEN
import asyncio


bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    user_id = message.from_user.id
    await bot.send_chat_action(user_id, types.ChatActions.UPLOAD_VIDEO)
    await message.reply("Ваш запрос направлен на обработку.\rПо завершению обработки Вы получите сообщение.")


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Напиши мне что-нибудь, и я отправлю этот текст тебе в ответ!")


@dp.message_handler(commands=['region'])
async def process_start_command(message: types.Message):
    await message.reply("Команда region!")


@dp.message_handler(commands=['request'])
async def process_start_command(message: types.Message):
    await message.reply("Команда request!")


@dp.message_handler(commands=['list'])
async def process_start_command(message: types.Message):
    await message.reply("Команда list!")


@dp.message_handler()
async def echo_messaging(message: types.Message):
    await bot.send_message(message.from_user.id, "Команда не распознана!")


if __name__ == '__main__':

    executor.start_polling(dp)
