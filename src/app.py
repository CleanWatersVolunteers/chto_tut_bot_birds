import logging
import asyncio
import json
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, constants, ReactionTypeEmoji
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, ContextTypes, filters

from telegram import Update
import re
import tgm
import nextgis_connector as nextgis
from datetime import datetime, timedelta

import project_config as conf

from stop_reply_manager import stop_reply_manager as srm
from stop_reply_manager import stop_reply_by_clicks

from nextgis_manager import nextgis_manager

pass_mode_enabled = True

with open("__allowed_groups_test.json", "r") as f:
    target_group_id = json.load(f)

with open("../__token_sosbird_chto_tut_bot.txt", "r") as f:
    TELEGRAM_BOT_TOKEN = f.read()


def get_coord_from_text(text):
    latitude_pattern = r"4[2-7]\.\d{5,7}"
    longitude_pattern = r"3[5-9]\.\d{5,7}"
    all_lat = re.findall(latitude_pattern, text.replace(",", "."))
    all_lon = re.findall(longitude_pattern, text.replace(",", "."))
    return all_lat, all_lon


# Нужен отлов птицы -> Если стриггерились на геопозицию, то спрашиваем фото и количество
#                                         Если стриггерились на фото, спрашиваем геопозицию и количество
#
# Птица поймана -> 1. Нужно забрать -> Сколько птиц? 
# -> Нужны ли коробки? (нужна / коробка есть) 
# -> ваш номер телефона, (Обязательна геолокация, если мы стриггерились не на геолокацию) 
# (Тут обязательна отбивка "Ждите когда приедет машина.") 
# 2. Отвезём сами -> пишем адреса (Витязево, Жемчужная, 9, Витязево, Черноморская, 2) 
# (Нужно будет поменять после переезда моек)

keyboard_text_node_start = {
        "edge1_bird":"Нужен отлов птицы",
        "edge2_bird_catched":"Птица поймана",
        "edge3_cancel":"Закрыть"
}
keyboard_text_node1X = {
        "edge11_bird_on_beach":"Около/на берегу", 
        "edge12_bird_far_in_sea":"В море", 
        "edge_to_start":"Назад"
}
keyboard_text_node1XX = {
        "edge1X1_bird_1":"Одна птица",
        "edge1X1_bird_2":"Две птицы",
        "edge1X2_bird_5":"от 3 до 5",
        "edge1X3_bird_10":"Больше 5",
        "edge1X4_bird_more":"Больше 10",
        "edge_to_start":"Назад"
}
keyboard_text_node2X = {
        "edge21_pick_bird":"Нужно забрать", 
        "edge22_we_bring_bird":"Отвезём сами", 
        "edge_to_start":"Назад"
}
keyboard_text_node21X = {
        "edge211_bird_1":"Одна птица",
        "edge211_bird_2":"Две",
        "edge212_bird_5":"от 3 до 5",
        "edge213_bird_10":"Больше 5",
        "edge214_bird_more":"Больше 10",
        "edge_to_start":"Назад"
}
keyboard_text_node21XX = {
        "edge21X1_we_need_boxes":"Нужны коробки", 
        "edge21X2_we_have_boxes":"Коробки есть", 
        "edge_to_start":"Назад"
}

keyboard_text_node_done = {
        "edge_done":"Всё верно", 
        "edge_to_start":"Назад"
}

def keyboard_text_node_start_handler(query):
    text = f'{query["message"]["text"]}\n{"-"*25}\n{keyboard_text_node_start[query.data]}'
    keyboard = None
    if query.data == "edge1_bird":
        keyboard = tgm.make_inline_keyboard(keyboard_text_node1X)
    if query.data == "edge2_bird_catched":
        keyboard = tgm.make_inline_keyboard(keyboard_text_node2X)
    if query.data == "edge3_cancel":
        text = None #"Действие отменено."
        keyboard = None
    return text, keyboard

def go_to_start(query):
    text = query["message"]["text"]
    text = text.split("-"*25)[0]
    keyboard = tgm.make_inline_keyboard(keyboard_text_node_start)
    return text, keyboard

def keyboard_text_node1X_handler(query):
    text = f'{query["message"]["text"]}\n{keyboard_text_node1X[query.data]}'
    if query.data == "edge12_bird_far_in_sea":
        keyboard = tgm.make_inline_keyboard(keyboard_text_node_done)    
    else:
        keyboard = tgm.make_inline_keyboard(keyboard_text_node1XX)
    return text, keyboard    

def keyboard_text_node1XX_handler(query):
    text = f'{query["message"]["text"]}\n{keyboard_text_node1XX[query.data]}'
    keyboard = tgm.make_inline_keyboard(keyboard_text_node_done)
    return text, keyboard 

def keyboard_text_node2X_handler(query):
    text = f'{query["message"]["text"]}\n{keyboard_text_node2X[query.data]}'
    keyboard = None
    if query.data == "edge21_pick_bird":
        keyboard = tgm.make_inline_keyboard(keyboard_text_node21X)
    if query.data == "edge22_we_bring_bird":
        keyboard = tgm.make_inline_keyboard(keyboard_text_node_done)
    return text, keyboard 

def keyboard_text_node21X_handler(query):
    text = f'{query["message"]["text"]}\n{keyboard_text_node21X[query.data]}'
    keyboard = tgm.make_inline_keyboard(keyboard_text_node21XX)
    return text, keyboard 

def keyboard_text_node21XX_handler(query):
    text = f'{query["message"]["text"]}\n{keyboard_text_node21XX[query.data]}'
    keyboard = tgm.make_inline_keyboard(keyboard_text_node_done)
    return text, keyboard 


def keyboard_text_node_done_handler(query):
    keyboard = None
    if query.data == "edge_done":
        text = f'{query["message"]["text"]}'
        user_id = query["message"]["reply_to_message"]["from"]["id"]
        reasoning = query["message"]["text"].split("-"*25)[1]
        bot_reply = query["message"]["text"].split("-"*25)[0]
        request_for_additional_info = ""
        request_for_additional_info2 = ""
        coordinates = None
        if "координаты" in bot_reply:
            request_for_additional_info = "📷 Добавьте фотографии в чат, если есть."
            request_for_additional_info2 = ""
            request_for_additional_info3 = "Теперь у координатора есть вся необходимая информация 💚"
            all_lat, all_lon = get_coord_from_text(bot_reply)
            coordinates = [all_lat[0], all_lon[0]]
        else:
            request_for_additional_info = "<b>Обязательно пришлите координаты или геопозицию в чат!</b>"
            request_for_additional_info2 = "<b>координаты</b>,"
            request_for_additional_info3 = "Тогда у координатора @Mira113_shtab будет вся необходимая информация 💚"

        if keyboard_text_node2X["edge22_we_bring_bird"] in reasoning:
            text = text + "\nОтлично! Адреса приёма птиц смотрите в @sosbird_bot"

        elif keyboard_text_node1X["edge12_bird_far_in_sea"] in reasoning:
            text = text + f"\nОтлично! {request_for_additional_info} Фиксируем точку для информации @Mira113_shtab. В море птиц не ловим, это может травмировать птиц и людей."
            print("[OK] Approved. Sending to gis.....")
            srm.add_stop_reply(user_id, minutes=conf.LOCATION_WAIT_TIME)
            nextgis_manager.append(query, coordinates)

        elif keyboard_text_node1X["edge11_bird_on_beach"] in reasoning:
            text = text.split("!")[0] + ". Вы уточнили:" + text.split("-"*25)[1]
            text = text + f"\n{request_for_additional_info}\n{request_for_additional_info3}"
            srm.add_stop_reply(user_id, minutes=conf.LOCATION_WAIT_TIME)
            nextgis_manager.append(query, coordinates)

        elif keyboard_text_node2X["edge21_pick_bird"] in reasoning:
            text = text + f"\nОтлично!\nПришлите в чат {request_for_additional_info2} ваш <b>номер телефона</b> (или свяжитесь с координатором @Mira113_shtab) и <b>ждите машину</b>"
            srm.add_stop_reply(user_id, minutes=conf.LOCATION_WAIT_TIME)
            nextgis_manager.append(query, coordinates)

    else:
        text = f'{query["message"]["text"]}\n{keyboard_text_node_done[query.data]}'
    return text, keyboard 


edges = {
        "edge1_bird": keyboard_text_node_start_handler,
        "edge2_bird_catched": keyboard_text_node_start_handler,
        "edge3_cancel": keyboard_text_node_start_handler,

        "edge11_bird_on_beach": keyboard_text_node1X_handler, 
        "edge12_bird_far_in_sea": keyboard_text_node1X_handler,

        "edge1X1_bird_1": keyboard_text_node1XX_handler,
        "edge1X1_bird_2": keyboard_text_node1XX_handler,
        "edge1X2_bird_5": keyboard_text_node1XX_handler,
        "edge1X3_bird_10": keyboard_text_node1XX_handler,
        "edge1X4_bird_more": keyboard_text_node1XX_handler,

        "edge21_pick_bird": keyboard_text_node2X_handler, 
        "edge22_we_bring_bird": keyboard_text_node2X_handler, 

        "edge211_bird_1": keyboard_text_node21X_handler,
        "edge211_bird_2": keyboard_text_node21X_handler,
        "edge212_bird_5": keyboard_text_node21X_handler,
        "edge213_bird_10": keyboard_text_node21X_handler,
        "edge214_bird_more": keyboard_text_node21X_handler,

        "edge21X1_we_need_boxes": keyboard_text_node21XX_handler, 
        "edge21X2_we_have_boxes": keyboard_text_node21XX_handler, 

        "edge_done": keyboard_text_node_done_handler, 
        "edge_to_start": go_to_start
}

async def cb_reaction_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    global pass_mode_enabled
    if pass_mode_enabled:
        print("^", end = "")
        sys.stdout.flush()
        return
    chat_id = str(query["message"]["chat"]["id"])
    if chat_id not in target_group_id:
        print("[!!] Button from wrong chat id, why so??")
        return

    if stop_reply_by_clicks.click_and_verify(query.message.message_id) == False:
        print(f'[..] Removing, reaction limit... Message: {query["message"]["text"]}')
        await query.delete_message()
        return
    #print(json.dumps(query.to_dict(), indent = 4))
    if query.message.reply_to_message is None:
        print("[..] Removing. Original message removed.")
        await query.delete_message()
        return

    coordinate_sender = query["message"]["reply_to_message"]["from"]["id"]
    replier = query["from"]["id"]
    print(f"[..] {datetime.now()} Sender {coordinate_sender}. Replier {replier}. {query.data}")
    if coordinate_sender != replier:
        return None
    if query.data in edges.keys():
        text, keyboard = edges[query.data](query)
        if keyboard is not None and text is not None:
            await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.HTML)
        elif keyboard is None and text is not None:
            await query.edit_message_text(text=text, parse_mode=constants.ParseMode.HTML)
        else:
            print(f'[..] Removing (canceled) {query["message"]["text"]}')
            await query.delete_message()
    else:
        print(f"[!!] Got unexpected argument: {query.data}")
    return

async def cb_message_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #print(json.dumps(update.to_dict(), indent = 4))
    global pass_mode_enabled
    if pass_mode_enabled:
        print("^", end = "")
        sys.stdout.flush()
        return   
    
    if update["message"] is None or update["message"]["is_topic_message"] != True:
        return None
    chat_id = str(update["message"]["chat"]["id"])
    group_id = update["message"]["message_thread_id"]
    if chat_id not in target_group_id or \
        group_id not in target_group_id[chat_id]["topic_list"]:
        return None
    if srm.check_active(update["message"]["from"]["id"]) == True:
        return None 

    keyboard = tgm.make_inline_keyboard(keyboard_text_node_start)
    username = update["message"]["from"]["username"]
    if username is not None:
        username = f"@{username}. "
    else:
        username = ""
    text = f"""\
{username}Спасибо за фотографию! 
Пожалуйста, уточните информацию о точке с помощью кнопок ниже ⬇️.
Это нужно, чтобы координаторы получили все необходимые данные для помощи.
⚠️ <b>Важно: бот не понимает текстовые сообщения. Нажимайте кнопки.</b>
"""
    srm.add_stop_reply(update["message"]["from"]["id"], minutes=conf.LOCATION_WAIT_TIME)
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.HTML)
    return None


async def cb_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global pass_mode_enabled
    if pass_mode_enabled:
        print("^", end = "")
        sys.stdout.flush()
        return None
    if update["message"] is None:
        return None
    if update["message"]["is_topic_message"] != True:
        return None
    chat_id = str(update["message"]["chat"]["id"])
    group_id = update["message"]["message_thread_id"]
    if chat_id not in target_group_id or \
        group_id not in target_group_id[chat_id]["topic_list"]:
        return None
    print(f'[..] message:... {update["message"]["from"]["id"]}')

    # Prepare to search the cordinates
    text = update.to_dict()
    if "reply_to_message" in text["message"]:
        text["message"]["reply_to_message"] = {}
    text = json.dumps(text)

    all_lat, all_lon = get_coord_from_text(text)
    message_text = update["message"]["text"]
    if message_text is None: 
        message_text = ""
    if len(all_lat) and len(all_lon) and len(message_text) < 500:# and "message" in update:
        coordinates = f"{all_lat[0]}, {all_lon[0]}"
        if nextgis_manager.append_and_check_awaiting(update.message["from"]["id"], [all_lat[0], all_lon[0]]):
            await update.message.set_reaction("👍")
            return None
        if srm.check_active(update["message"]["from"]["id"]) == True:
            return None
        username = update["message"]["from"]["username"]
        if username is not None:
            username = f"@{username}. "
        else:
            username = ""
        
        text = f"""\
{username} Спасибо за координаты ({coordinates})!
Пожалуйста, уточните информацию о точке с помощью кнопок ниже ⬇️
Это нужно, чтобы координаторы получили все необходимые данные для помощи.
⚠️ <b>Важно: бот не понимает текстовые сообщения. Нажимайте кнопки.</b>
"""
        keyboard = tgm.make_inline_keyboard(keyboard_text_node_start)
        await update.message.reply_text(f'{text}', reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=constants.ParseMode.HTML)
    return None

async def main() -> None:
    """Run the bot."""
    global application
    global pass_mode_enabled
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, cb_message_photo))
    application.add_handler(MessageHandler(filters.ALL, cb_message))
    application.add_handler(CallbackQueryHandler(cb_reaction_button))
    #application.add_handler(CallbackQueryHandler(button))
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    print("[OK] Bot enabled (pass mode)")
    await asyncio.sleep(15)
    pass_mode_enabled = False

    print("[OK] Bot enabled")
    while True:
        await asyncio.sleep(0.1)
        nextgis_manager.send_what_is_possible()

    await application.updater.stop()
    print("[OK] Bot disabled")

    await application.shutdown()

if __name__ == "__main__":
    asyncio.run(main())