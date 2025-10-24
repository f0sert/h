from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject

from config import ADMIN_IDS
from database import Database
from keyboards import get_admin_keyboard, get_confirmation_keyboard, get_moderation_keyboard

router = Router()
db = Database()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(F.text == '⚙️ Админ-панель')
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав доступа к админ-панели")
        return
    
    await message.answer(
        "⚙️ Админ-панель:",
        reply_markup=get_admin_keyboard()
    )

@router.message(F.text == '👥 Управление дефферами')
async def manage_deffers(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "👥 Управление дефферами:\n\n"
        "Для добавления деффера используйте:\n"
        "<code>/add_deffer тг_айди</code>\n\n"
        "Для удаления деффера используйте:\n"
        "<code>/remove_deffer тг_айди</code>",
        parse_mode='HTML'
    )

@router.message(F.text == '🔄 Очистить статистику')
async def clear_stats_confirm(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "⚠️ Вы уверены что хотите очистить статистику?(Не касается статистики за всё время)\n"
        "Это действие нельзя отменить!",
        reply_markup=get_confirmation_keyboard('clear_week')
    )

@router.message(F.text == '🏆 Подсчитать победителя')
async def calculate_winner(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    deffers_stats = db.get_all_deffers_stats()
    if not deffers_stats:
        await message.answer("❌ Нет дефферов для подсчета")
        return
    
    winner = deffers_stats[0]
    winner_id, winner_username, week_count, total_count = winner
    
    await message.answer(
        f"🏆 Победитель недели:\n"
        f"Деффер: {winner_username or f'ID: {winner_id}'}\n"
        f"Количество отзывов: {week_count}\n"
        "Уведомить победителя и очистить недельную статистику?",
        reply_markup=get_confirmation_keyboard('notify_winner')
    )

@router.message(F.text == '📈 Топ недели')
async def top_deffers(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    deffers_stats = db.get_all_deffers_stats()
    if not deffers_stats:
        await message.answer("❌ Нет дефферов")
        return
    
    top_text = "📈 Топ дефферов за неделю:\n\n"
    for i, (user_id, username, week_count, total_count) in enumerate(deffers_stats, 1):
        display_name = username if username else f"deffer_{user_id}"
        top_text += f"{i}. @{display_name} (ID: {user_id})\n"
        top_text += f"Неделя: {week_count} | Всего: {total_count}\n\n"
    
    await message.answer(top_text)

@router.message(F.text == '📋 Список дефферов')
async def list_deffers(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    deffers_stats = db.get_all_deffers_stats()
    if not deffers_stats:
        await message.answer("❌ Нет зарегистрированных дефферов")
        return
    
    deffers_text = "📋 Список дефферов:\n\n"
    for i, (user_id, username, week_count, total_count) in enumerate(deffers_stats, 1):
        username_display = username if username else "нет юзернейма"
        deffers_text += f"{i}. @{username_display} (ID: {user_id})\n"
        deffers_text += f"Неделя: {week_count} | Всего: {total_count}\n\n"
    
    await message.answer(deffers_text)

@router.message(F.text == '✏️ Изменить статистику')
async def manual_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "✏️ Ручное изменение статистики:\n\n"
        "Для изменения статистики отправьте:\n"
        "<code>/set_week_stats тг_айди +/- количество</code> - для недельной статистики\n"
        "<code>/set_total_stats тг_айди +/- количество</code> - для общей статистики\n\n"
        "Примеры:\n"
        "<code>/set_week_stats 189365026 +5</code> (Добавит 5 отзывов за неделю)\n"
        "<code>/set_total_stats 758465696 -2</code> (Отберёт 2 отзыва за всё время)",
        parse_mode='HTML'
    )

async def send_review_to_admins(bot, deffer_id, review_id, review_data):
    try:
        chat = await bot.get_chat(deffer_id)
        deffer_username = f"@{chat.username}" if chat.username else f"ID: {deffer_id}"
    except:
        deffer_username = f"ID: {deffer_id}"
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.forward_message(
                chat_id=admin_id,
                from_chat_id=review_data['chat_id'],
                message_id=review_data['message_id']
            )
            
            await bot.send_message(
                chat_id=admin_id,
                text=f"Новый отзыв, просыпаемся!\n\nДеффер: {deffer_username}",
                reply_markup=get_moderation_keyboard(review_id, deffer_id)
            )
        except Exception as e:
            print(f"Ошибка отправки админу {admin_id}: {e}")

@router.callback_query(F.data.startswith("accept_") | F.data.startswith("reject_"))
async def handle_moderation(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return

    data = callback.data.split('_')
    action = data[0]
    review_id = int(data[1])
    deffer_id = int(data[2])
    
    if action == 'accept':
        db.update_review_status(review_id, 'accepted', callback.from_user.id)
        await callback.message.edit_text("✅ Отзыв принят и зачислен на баланс деффера")

        try:
            await callback.bot.send_message(
                deffer_id,
                "✅ Ваш отзыв был принят администратором\n\nВаша статистика была обновлена"
            )
        except:
            pass
            
    elif action == 'reject':
        db.update_review_status(review_id, 'rejected', callback.from_user.id)
        await callback.message.edit_text("❌ Отзыв отклонен\n\nСтатистика деффера не изменился")

        try:
            await callback.bot.send_message(
                deffer_id,
                "❌ Ваш отзыв был отклонен администратором.\n\nВаша статистика не изменилась"
            )
        except:
            pass

@router.callback_query(F.data.in_(["clear_week_confirm", "notify_winner_confirm", "cancel_action"]))
async def handle_admin_callbacks(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return

    if callback.data == 'clear_week_confirm':
        db.clear_week_stats()
        await callback.message.edit_text("✅ Недельная статистика очищена")
    
    elif callback.data == 'notify_winner_confirm':
        deffers_stats = db.get_all_deffers_stats()
        if not deffers_stats:
            await callback.message.edit_text("❌ Нет дефферов для уведомления")
            return
        
        winner = deffers_stats[0]
        winner_id, winner_username, week_count, total_count = winner

        try:
            await callback.bot.send_message(
                winner_id,
                "🎉 Ай красава, Марат!\n\nЖди свои 20$ и продолжай работать в том же духе!"
            )
        except Exception as e:
            print(f"Ошибка уведомления победителя: {e}")
            await callback.message.edit_text(
                f"✅ Победитель определен: {winner_username or f'ID: {winner_id}'}\n"
                f"❌ Но не удалось уведомить победителя."
            )
            return

        db.clear_week_stats()
        
        await callback.message.edit_text(
            f"✅ Победитель определен и уведомлен: {winner_username or f'ID: {winner_id}'}\n"
            "Недельная статистика так же была очищена."
        )
    
    elif callback.data == 'cancel_action':
        await callback.message.edit_text("❌ Действие отменено")

@router.message(Command("add_deffer"))
async def add_deffer(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    
    args = command.args
    if not args:
        await message.answer("❌ Неверный формат команды. Используйте: /add_deffer тг_айди")
        return
    
    try:
        deffer_id = int(args)
        db.set_user_role(deffer_id, 'deffer')
        await message.answer(f"✅ Пользователь {deffer_id} добавлен как деффер")
    except ValueError:
        await message.answer("❌ Неверный ID пользователя")

@router.message(Command("remove_deffer"))
async def remove_deffer(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    
    args = command.args
    if not args:
        await message.answer("❌ Неверный формат команды. Используйте: /remove_deffer тг_айди")
        return
    
    try:
        deffer_id = int(args)
        db.set_user_role(deffer_id, 'user')
        await message.answer(f"✅ Пользователь {deffer_id} удален из дефферов")
    except ValueError:
        await message.answer("❌ Неверный ID пользователя")

@router.message(Command("set_week_stats"))
async def set_week_stats(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    
    args = command.args
    if not args:
        await message.answer("❌ Неверный синтаксис команды. Используйте: /set_week_stats тг_айди +/- количество")
        return
    
    parts = args.split()
    if len(parts) != 2:
        await message.answer("❌ Неверное количество аргументов. Нужно: тг_айди +/- количество")
        return
    
    try:
        target_id = int(parts[0])
        operation = parts[1]
        
        if not (operation.startswith('+') or operation.startswith('-')):
            await message.answer("❌ Неверный формат операции. Используйте + или - перед числом для добавления/отбирания отзывов у деффера")
            return
        
        amount = int(operation[1:])
        if operation.startswith('-'):
            amount = -amount

        current_week, current_total = db.get_stats(target_id)
        new_week = current_week + amount
        if new_week < 0:
            new_week = 0
        
        db.manual_update_stats(target_id, new_week, current_total)
        await message.answer(f"✅ Недельная статистика деффера {target_id} изменена: {current_week} → {new_week}")
        
    except ValueError:
        await message.answer("❌ Неверные аргументы")

@router.message(Command("set_total_stats"))
async def set_total_stats(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    
    args = command.args
    if not args:
        await message.answer("❌ Неверный синтаксис команды. Используйте: /set_total_stats тг_айди +/- количество")
        return
    
    parts = args.split()
    if len(parts) != 2:
        await message.answer("❌ Неверное количество аргументов. Нужно: тг_айди +/- количество")
        return
    
    try:
        target_id = int(parts[0])
        operation = parts[1]
        
        if not (operation.startswith('+') or operation.startswith('-')):
            await message.answer("❌ Неверный формат операции. Используйте + или - перед числом для добавления/отбирания отзывов у деффера")
            return
        
        amount = int(operation[1:])
        if operation.startswith('-'):
            amount = -amount

        current_week, current_total = db.get_stats(target_id)
        new_total = current_total + amount
        if new_total < 0:
            new_total = 0
        
        db.manual_update_stats(target_id, current_week, new_total)
        await message.answer(f"✅ Общая статистика деффера {target_id} изменена: {current_total} → {new_total}")
        
    except ValueError:
        await message.answer("❌ Неверные аргументы")