from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_markup(buttons, columns=1):
    inline_keyboard = []
    for i in range(0, len(buttons), columns):
        row = []
        for text, callback_data in buttons[i : i + columns]:
            button = InlineKeyboardButton(text=text, callback_data=callback_data)
            row.append(button)
        inline_keyboard.append(row)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def create_markup_with_url(buttons):
    markup = types.InlineKeyboardMarkup()
    for text, url, callback_data in buttons:
        button = types.InlineKeyboardButton(text=text, url=url, callback_data=callback_data)
        markup.add(button)
    # for text, url in buttons:
    #     markup.add(types.InlineKeyboardButton(text=text, url=url))
    return markup
