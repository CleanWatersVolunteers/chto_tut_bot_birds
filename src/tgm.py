from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update


def get_username_in_text(): 
    pass
def get_username_in_query(query):
    pass

def make_inline_keyboard(text_list):
    line_text_len = 0
    keyboard = []
    kb_line = []
    sorted_keys = text_list.keys()#sorted(text_list.keys())
    for item in sorted_keys:
        if line_text_len + len(text_list[item]) > 25:
            keyboard.append(kb_line)
            kb_line = []
            line_text_len = 0
        kb_line.append(
            InlineKeyboardButton(text_list[item], callback_data=item)
        )
        line_text_len += len(text_list[item])
    keyboard.append(kb_line)
    return keyboard