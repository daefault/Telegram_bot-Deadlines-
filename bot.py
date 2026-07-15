import asyncio
from telethon import TelegramClient
from telethon.network.connection.tcpmtproxy import ConnectionTcpMTProxyAbridged
import config 
import database as db
from handlers import registed_handlers
from datetime import datetime, timedelta


print('Создаю клиент')

if config.PROXY_HOST:
    print('используется прокси')
    client = TelegramClient('bot_session', 
                        config.API_ID,
                        config.API_HASH,
                          connection=ConnectionTcpMTProxyAbridged,
                            proxy=(config.PROXY_HOST, config.PROXY_PORT, config.PROXY_SECRET))
else:
    print('без прокси')
    client = TelegramClient(
        'bot_session',
        config.API_ID,
        config.API_HASH
    )


async def reminder_job():
    print('Задача напоминаний запущена')

    while True:
        now = datetime.now()
        target = now.replace(hour = 18, minute = 0, second = 0, microsecond=0)
        if now >=target:
            target+=timedelta(days = 1)
        wait_seconds = (target-now).total_seconds()
        await asyncio.sleep(wait_seconds)

        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        all_deadlines = db.get_all_active_deadlines()

        if not all_deadlines:
            print('Дедлайнов нет')
            return
        reminders = {}
        for deadline in all_deadlines:
            deadline_id, user_id, title, date_str = deadline
            deadline_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if deadline_date == today:
                key = 'today'
            elif deadline_date == tomorrow:
                key = 'tomorrow'
            else:
                continue

            if user_id not in reminders:
                reminders[user_id] = {'today': [], 'tomorrow': []}
            reminders[user_id][key].append(deadline)

        for user_id, deadlines_by_day in reminders.items():
            try: 
                if deadlines_by_day['today']:
                    message = 'Сегодня истекают дедлайны:\n\n'
                    for d in deadlines_by_day['today']:
                        deadline_id, _, title, _ = d
                        message +=f'#{deadline_id}: {title}'
                    await client.send_message(user_id, message)
                if deadlines_by_day['tomorrow']:
                    message = 'Завтра истекают дедлайны:\n\n'
                    for d in deadlines_by_day['tomorrow']:
                        deadline_id, _, title, _ =d
                        message += f'#{deadline_id}: {title}'
                    await client.send_message(user_id, message)
            except Exception as e:
                print(f'Ошибка при отправке напоминания пользователю {user_id}: {e}')


async def main():

    db.init_db()

    registed_handlers(client)

    await client.start(bot_token = config.BOT_TOKEN)
    print('запущен')
    asyncio.create_task(reminder_job())
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот остановлен')