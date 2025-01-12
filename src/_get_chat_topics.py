import asyncio
import pandas as pd
from pyrogram import Client
from pyrogram.raw.functions.channels import GetForumTopics

# Ваши данные API
api_id = 1
api_hash = "..."

# Список ID чатов
chat_ids = [-1002425874693]  # Замените на ваши chat_id

async def get_forum_topics_from_chats(chat_ids):
    async with Client("me", api_id, api_hash) as app:
        results = []
        for chat_id in chat_ids:
            print(chat_id)
            try:
                # Получение информации о чате
                chat = await app.get_chat(chat_id)

                # Получение топиков форума
                input_peer = await app.resolve_peer(chat_id)
                response = await app.invoke(GetForumTopics(
                    channel=input_peer,
                    offset_date=0,      # Используйте 0 для начала
                    offset_id=0,        # Используйте 0 для начала
                    offset_topic=0,     # Используйте 0 для начала
                    limit=100           # Максимальное количество возвращаемых тем
                ))

                # Обработка топиков
                for topic in response.topics:
                        
                    results.append({
                        "chat_id": chat.id,
                        "chat_name": chat.title,
                        "topic_id": topic.id,
                        "topic_name": topic.title
                    })
            except Exception as e:
                print(f"Ошибка при обработке чата {chat_id}: {e}")

        return results

# Основная функция для получения данных и создания таблицы
async def main():
    topics_data = await get_forum_topics_from_chats(chat_ids)
    df = pd.DataFrame(topics_data)
    # Сохранение в Excel
    output_file = "-1002425874693.csv"
    df.to_csv(output_file, index=False)
    print(f"Данные сохранены в {output_file}")

# Запуск
asyncio.run(main())
