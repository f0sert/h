from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard(role):
    if role == 'admin':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='📊 Общая статистика'), KeyboardButton(text='⚙️ Админ-панель')]
            ],
            resize_keyboard=True
        )
    elif role == 'deffer':
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='👤 Мой профиль'), KeyboardButton(text='📨 Отправить отзыв')]
            ],
            resize_keyboard=True
        )
    else:
        return None

def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='👥 Управление дефферами'), KeyboardButton(text='📋 Список дефферов')],
            [KeyboardButton(text='🔄 Очистить статистику'), KeyboardButton(text='🏆 Подсчитать победителя')],
            [KeyboardButton(text='📈 Топ недели'), KeyboardButton(text='✏️ Изменить статистику')],
            [KeyboardButton(text='⬅️ Главное меню')]
        ],
        resize_keyboard=True
    )

def get_confirmation_keyboard(action):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"{action}_confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")
            ]
        ]
    )

def get_review_submission_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="submit_review"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_review")
            ]
        ]
    )

def get_moderation_keyboard(review_id, deffer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{review_id}_{deffer_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{review_id}_{deffer_id}")
            ]
        ]
    )