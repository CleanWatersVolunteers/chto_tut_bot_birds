import json
import nextgis_connector as nextgis
from datetime import datetime, timedelta
import project_config as conf

class nextgis_manager:
    send_to_gis_queue = dict()
    send_to_gis_queue_awaiting_for_coordinates = set()

    @classmethod
    def append(cls, query, coordinates):
        print("[..] Appending")
        userid = query["message"]["reply_to_message"]["from"]["id"]
        cls.send_to_gis_queue[userid] = {
            "query":query.to_dict(), 
            "coordinates":coordinates, 
            "ts":datetime.now()
        }
        if coordinates is None: 
            print(f"[..] No coordinates for {userid}")
            cls.send_to_gis_queue_awaiting_for_coordinates.add(userid)
            print(f"[..] SET {cls.send_to_gis_queue_awaiting_for_coordinates}")
    
    @classmethod
    def append_and_check_awaiting(cls, userid, coordinates):
        print(f"[..] Some coordinates: {userid} Waiting set: {cls.send_to_gis_queue_awaiting_for_coordinates}")
        if userid in cls.send_to_gis_queue_awaiting_for_coordinates and userid in cls.send_to_gis_queue:
            print("[..] Coordinates received. Discarding from list")
            cls.send_to_gis_queue[userid]["coordinates"] = coordinates
            cls.send_to_gis_queue_awaiting_for_coordinates.discard(userid)
            return True
        return False
    
    @classmethod
    def send_what_is_possible(cls):
        new_send_to_gis_queue = dict()
        cnt = 0
        for k, v in cls.send_to_gis_queue.items():
            if v["ts"] + timedelta(minutes=conf.LOCATION_WAIT_TIME) < datetime.now():
                cls.send_to_gis_queue_awaiting_for_coordinates.discard(k)
                continue
            if v["coordinates"] is None:
                new_send_to_gis_queue[k] = v
                continue
            send_to_gis(v["query"], 'bird', v["coordinates"], v["ts"])
            cnt +=1
        cls.send_to_gis_queue = new_send_to_gis_queue
        if cnt > 0:
            print(f"[..] Sent to gis {cnt}. DL {len(cls.send_to_gis_queue)} QL {len(cls.send_to_gis_queue_awaiting_for_coordinates)}")

def get_region(lat, lon):
    def get_r(A, B):
        r = ((A[0] - B[0])**2 + (A[1] - B[1])**2)**0.5
        return r
    anapa = [[44.982265, 37.247752],[45.098649, 36.924302]]
    NR = [[44.7, 37.7],[44.73, 37.42]]
    sochi = [[43.6, 39.71],[44.08, 39.03]]
    anapa.append(get_r(anapa[0], anapa[1]))
    NR.append(get_r(NR[0], NR[1]))
    sochi.append(get_r(sochi[0], sochi[1]))

    if get_r([float(lat), float(lon)], anapa[0]) < anapa[2]:
        return "Анапа"
    if get_r([float(lat), float(lon)], NR[0]) < NR[2]:
        return "Новороссийск"
    if get_r([float(lat), float(lon)], sochi[0]) < sochi[2]:
        return "Сочи"
    return "Иное"

def get_count(system_message_part):
    if "Одна птица" in system_message_part:
        return "Одна птица"
    elif "Две птицы" in system_message_part:
        return "Две птицы"
    elif "от 3 до 5" in system_message_part:
        return "от 3 до 5"
    elif "Больше 5" in system_message_part:
        "Больше 5"
    elif "Больше 10" in system_message_part:
        return "Больше 10"
    return None

def get_position(system_message_part):
    position = None
    if "Около/на берегу" in system_message_part:
        return "Около/на берегу"
    elif "В море" in system_message_part:
        return "В море"
    return None

def get_catch_status(system_message_part):
    if "Нужен отлов птицы" in system_message_part:
        return "не поймана"
    if "Птица поймана" in system_message_part:
        return "поймана"
    return None

def need_boxes(system_message_part):
    if "Нужны коробки" in system_message_part:
        return "Нужны коробки.\n"
    return ""

def send_to_gis(query, layer, coordinates, dtime):
    #Check if this comment come from prser user-bot.
    #print(json.dumps(query, indent = 4))
    user_message_part = ""
    if "text" in query["message"]["reply_to_message"]:
        user_message_part = query["message"]["reply_to_message"]["text"]

    system_message_part = query["message"]["text"].split("-"*25)[1]
    message = query["message"]

    print("[..] User message")
    tg_link = f'https://t.me/c/{str(message["chat"]["id"])[4:]}/{message["reply_to_message"]["message_id"]}'

    comment = need_boxes(system_message_part) + user_message_part
    lat_list, lon_list = coordinates
    print(f"[..] Sending to gis: {coordinates}, {type(coordinates)}, {type(coordinates[0])}")
    nextgis.add_point(
            lat = float(lat_list), 
            lon = float(lon_list), 
            comment = comment, #query["message"]["text"].split("-"*25)[0], 
            dtime = dtime,
            tg_link = tg_link, 
            layer_name = layer, 
            count = get_count(system_message_part),
            position = get_position(system_message_part),
            status_us = get_catch_status(system_message_part), 
            region = get_region(float(lat_list), float(lon_list))
    )