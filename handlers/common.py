from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from config import ADMIN_IDS
from database import Database
from keyboards import get_main_keyboard

router = Router()
db = Database()

@router.message(CommandStart())
async def start(message: Message):
    user = message.from_user
    user_id = user.id
    username = user.username or f"user_{user_id}"

    display_name = user.first_name or ""
    if user.last_name:
        display_name += f" {user.last_name}"

    if not display_name.strip():
        display_name = username

    if user_id in ADMIN_IDS:
        db.add_user(user_id, username, 'admin')
        role = 'admin'
    else:
        role = db.get_user_role(user_id)
        db.add_user(user_id, username, role)
    
    if role == 'user':
        await message.answer(
            "Для подачи заявки на помощь используйте @freedefer_bot"
        )
    else:
        keyboard = get_main_keyboard(role)
        await message.answer(
            f"Привет, {display_name}\n\n"
            "Используйте кнопки ниже для навигации по боту",
            reply_markup=keyboard
        )

@router.message(F.text == '📊 Общая статистика')
async def show_stats(message: Message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer("У вас нет прав для просмотра общей статистики")
        return

    deffers_stats = db.get_all_deffers_stats()

    total_week = 0
    total_all = 0
    for deffer in deffers_stats:
        total_week += deffer[2]
        total_all += deffer[3]
    
    stats_text = (
        f"📊 Общая статистика:\n"
        f"За текущую неделю: {total_week} отзывов\n"
        f"Всего: {total_all} отзывов\n\n"
    )

    for deffer in deffers_stats:
        user_id, username, week_count, total_count = deffer
        display_name = username if username else f"deffer_{user_id}"
        stats_text += (
            f"📊 Статистика @{display_name}:\n"
            f"За текущую неделю: {week_count} отзывов\n"
            f"Всего: {total_count} отзывов\n\n"
        )
    
    await message.answer(stats_text)

@router.message(F.text == '👤 Мой профиль')
async def show_my_profile(message: Message):
    user_id = message.from_user.id
    role = db.get_user_role(user_id)
    
    if role != 'deffer':
        await message.answer("У вас нет прав для просмотра профиля")
        return
    
    week_count, total_count = db.get_stats(user_id)
    
    stats_text = (
        f"👤 Ваш профиль:\n"
        f"За текущую неделю: {week_count} отзывов\n"
        f"Всего: {total_count} отзывов"
    )
    
    await message.answer(stats_text)

@router.message(F.text == '⬅️ Главное меню')
async def back_to_main_menu(message: Message):
    user_id = message.from_user.id
    role = db.get_user_role(user_id)
    
    if role in ['admin', 'deffer']:
        keyboard = get_main_keyboard(role)
        await message.answer(
            "Главное меню:",
            reply_markup=keyboard
        )