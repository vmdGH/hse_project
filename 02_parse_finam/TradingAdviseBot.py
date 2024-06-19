from aiogram import Bot, Dispatcher
from aiogram.types import Message
import asyncio
import pickle

with open('adaboost_random.pkl', 'rb') as model_file:
    adaboost_model = pickle.load(model_file)



token = 



async def get_start(message: Message, bot: Bot):
    await bot.send_message(message.from_user.id, f'hello, {message.from_user.first_name}')
    await message.answer(f'hello, {message.from_user.first_name}')
    await message.reply(f'hello, {message.from_user.first_name}')



async def start():

    bot = Bot(token=token)

    dp = Dispatcher()
    dp.message.register(get_start)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()



if __name__ == "__main__":
    asyncio.run(start())