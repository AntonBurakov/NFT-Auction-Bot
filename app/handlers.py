from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.database.requests as rq

router = Router()


class Register(StatesGroup):
    number = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id)
    await message.answer('Привет!')
    await message.reply('Как дела?')


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Вы нажали на кнопку помощи')


@router.message(F.text == 'Каталог')
async def catalog(message: Message):
    await message.answer('Выберите категорию товара')


@router.callback_query(F.data == 't-shirt')
async def t_shirt(callback: CallbackQuery):
    await callback.answer('Вы выбрали категорию', show_alert=True)
    await callback.message.answer('Вы выбрали категорию футболок.')


"""
@router.message(Command('register'))
async def register(message: Message, state: FSMContext):
    await state.set_state(Register.name)
    await message.answer('Введите ваше имя')


@router.message(Register.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Register.age)
    await message.answer('Введите ваш возраст')


@router.message(Register.age)
async def register_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    data = await state.get_data()
    await message.answer(f'Ваше имя: {data["name"]}\nВаш возраст: {data["age"]}')
    await state.clear() 
"""

@router.message(Command('random_image'))
async def send_random_image(message: Message):
    image_url = 'https://placebear.com/400/300'  
    await message.answer_photo(photo=image_url, caption="Вот случайная картинка!")


@router.message(Command('select_image'))
async def register(message: Message, state: FSMContext):
    await state.set_state(Register.number)
    await message.answer('Введите номер картинки')

@router.message(Register.number)
async def register_name(message: Message, state: FSMContext):
    # Получаем введённое число (номер) от пользователя
    number = message.text
    # Формируем ссылку с номером
    href = f'https://placebear.com/400/{number}'
    # Получаем ID пользователя Telegram
    tg_id = message.from_user.id
    # Создаем NFT, используя заранее определённую функцию set_nft
    await rq.set_nft(href=href, tg_id=tg_id)
    # Завершаем FSM (очищаем состояние)
    await state.clear()

@router.message(Command('get_nfts'))
async def get_nfts(message: Message, state: FSMContext):
    tg_id = message.from_user.id  # Получаем tg_id из сообщения

    # Получаем список NFT для пользователя
    nfts = await rq.get_user_nfts(tg_id)

    # Проверяем, есть ли NFT
    if not nfts:
        await message.answer("У вас нет NFT.")
        return

    # Отправляем изображение для каждого href
    for href in nfts:
        await message.answer_photo(href)  # Отправляем фото по URL