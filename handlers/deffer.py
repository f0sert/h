from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards import get_review_submission_keyboard, get_main_keyboard

router = Router()
db = Database()

class ReviewStates(StatesGroup):
    waiting_for_submission = State()

@router.message(F.text == '📨 Отправить отзыв')
async def send_review_instruction(message: Message):
    await message.answer(
        "Чтобы отправить отзыв, просто перешли отзыв от человека, которому помог(с именем отправителя)\n"
        "Бот автоматически предложит отправить его на модерацию."
    )

@router.message(F.forward_date)
async def handle_forwarded_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if db.get_user_role(user_id) != 'deffer':
        return
    
    if not message.forward_from_chat and not message.forward_from:
        await message.answer("❌ Это сообщение не является пересланным")
        return

    await state.update_data(
        pending_review_message_id=message.message_id,
        pending_review_chat_id=message.chat.id,
        victim_info=f"Chat: {message.forward_from_chat.title if message.forward_from_chat else 'Private'}"
    )
    
    await message.answer(
        "Отправить отзыв на модерацию?",
        reply_markup=get_review_submission_keyboard()
    )
    await state.set_state(ReviewStates.waiting_for_submission)

@router.callback_query(F.data.in_(["submit_review", "cancel_review"]))
async def handle_review_submission(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'cancel_review':
        await callback.message.edit_text("❌ Отправка отзыва отменена")
        await state.clear()
        return
    
    user_id = callback.from_user.id
    data = await state.get_data()
    pending_review = {
        'message_id': data.get('pending_review_message_id'),
        'chat_id': data.get('pending_review_chat_id'),
        'victim_info': data.get('victim_info')
    }
    
    if not pending_review['message_id']:
        await callback.message.edit_text("❌ Ошибка: данные отзыва не найдены")
        await state.clear()
        return

    review_id = db.add_review(user_id, pending_review['victim_info'])

    from handlers.admin import send_review_to_admins
    await send_review_to_admins(callback.bot, user_id, review_id, pending_review)
    
    await callback.message.edit_text("✅ Отзыв отправлен на модерацию")
    await state.clear()