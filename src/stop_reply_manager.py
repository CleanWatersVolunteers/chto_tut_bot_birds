
from datetime import datetime, timedelta

class stop_reply_manager:
    stop_reply_dict = {}

    @classmethod
    def add_stop_reply(cls, user_id, minutes = 0, seconds = 0):
        if user_id not in cls.stop_reply_dict:
            cls.stop_reply_dict[user_id] = datetime.now() + timedelta(minutes = minutes, seconds=seconds)
        k = [i for i in cls.stop_reply_dict.keys()] ###### Changes dufing runtime operatopn
        for uid in k:
            if uid in cls.stop_reply_dict and cls.stop_reply_dict[uid] < datetime.now():
                del cls.stop_reply_dict[uid]
        print(f"[..] Add stop reply: {user_id}. Dict: {cls.stop_reply_dict}")

    @classmethod
    def check_active(cls, user_id):
        print(f"Checking active: {user_id}. Dict: {cls.stop_reply_dict}")
        if user_id in cls.stop_reply_dict and cls.stop_reply_dict[user_id] > datetime.now():
            print(f"[..] Check active len = {len(cls.stop_reply_dict)}")
            return True
        return False

class stop_reply_by_clicks:
    stop_reply_dict = {}

    @classmethod
    def click_and_verify(cls, chat_instance):
        if chat_instance in cls.stop_reply_dict:
            cls.stop_reply_dict[chat_instance] += 1
        else:
            cls.stop_reply_dict[chat_instance] = 1

        if  cls.stop_reply_dict[chat_instance] > 15:
            return False
        return True