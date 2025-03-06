from aiogram import Router, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config_data.config import Config, load_config
from database import requests as rq
from database.models import User
from utils.error_handling import error_handler
from keyboards.start_keyboard import keyboard_start
from filter.admin_filter import check_super_admin

import logging

router = Router()
config: Config = load_config()


@router.message(CommandStart())
@error_handler
async def process_start_command_user(message: Message, state: FSMContext, command: CommandObject, bot: Bot) -> None:
    """
    Обработки запуска бота или ввода команды /start
    :param message:
    :param state:
    :param command:
    :param bot:
    :return:
    """
    logging.info(f'process_start_command_user: {message.chat.id}')
    await state.set_state(state=None)
    token = command.args
    # добавление пользователя в БД если еще его там нет
    user: User = await rq.get_user_by_id(tg_id=message.from_user.id)
    if not user:
        if message.from_user.username:
            username = message.from_user.username
        else:
            username = "user_name"
        data_user = {"tg_id": message.from_user.id,
                     "name": username}
        if await check_super_admin(telegram_id=message.from_user.id):
            data_user = {"tg_id": message.from_user.id,
                         "name": username,
                         "role": rq.UserRole.admin}
        await rq.add_user(data=data_user)
    if token:
        role = await rq.get_token(token=token, tg_id=message.from_user.id)
        if role:
            await rq.set_user_role(tg_id=message.from_user.id,
                                   role=role)
        else:
            await message.answer(text='Пригласительная ссылка не валидна')
    # вывод клавиатуры в зависимости от роли пользователя
    user: User = await rq.get_user_by_id(tg_id=message.from_user.id)
    # пользователь
    if user.role == rq.UserRole.user:
        await message.answer(text='Бот доступен только авторизованным пользователям')

    # администратор
    elif await check_super_admin(telegram_id=message.from_user.id):
        await message.answer(text=f'Добро пожаловать! Вы являетесь АДМИНИСТРАТОРОМ проекта',
                             reply_markup=keyboard_start(role=rq.UserRole.admin))

    # партнер
    elif user.role == rq.UserRole.admin:
        await message.answer(text=f'Добро пожаловать! Вы являетесь ПАРТНЕРОМ проекта',
                             reply_markup=keyboard_start(role=rq.UserRole.partner))
