from telethon import events
from telethon.tl.types import DocumentAttributeFilename
from telethon import Button
import database as db 
import utils
from config import EXPORT_PATH
from datetime import datetime 


DELETE_STATES = {
    'WAITING_CATEGORY': 1,
    'WAITING_ACTION': 2,
    'CANCELLED':0
}
delete_sessions = {}



def registed_handlers(client):
    @client.on(events.NewMessage(pattern = '/start'))
    async def start_handler(event):
        user = await event.get_sender()
        db.add_user(
            user_id = event.sender_id,
            first_name = user.first_name or '',
            username = user.username or ''
        )
        await event.respond(
            'Привет! Я бот-помощник для учёбы и работы\n\n'
            'Я могу '
            'Список команд:\n'
            '/add_deadline YYYY-MM-DD Название - добавить дедлайн\n'
            '/deadlines - показать дедлайны\n'
            '/done_deadline N - отметить выполнение дедлайна\n'
            '/delete_deadline N - удалить дедлайн\n'
            '/clear_deadlines - удалить все дедлайны, либо только выполненные\n'
            'Функции для хранения полезных ссылок:\n\n'
            '/add_link категория название ссылка - добавить ссылку\n'
            '/get_links категория - показать ссылки\n'
            '/export_links категория - выгрузить ссылки в csv\n'
            '/categories - показать все категории\n'
            '/delete_link - удаление ссылок\n\n'
            '/stats - статистика\n\n'
            '/ping - проверить, работает бот или нет'
        )

    @client.on(events.NewMessage(pattern='/add_deadline (\\d{4}-\\d{2}-\\d{2}) (.+)'))
    async def add_deadline_handler(event):
        date = event.pattern_match.group(1)
        title = event.pattern_match.group(2).strip()

        try: 
            deadline_date = datetime.strptime(date, '%Y-%m-%d').date()
            today = datetime.now().date()
            if deadline_date < today:
                await event.respond(
                    f'Нельзя добавить дедлайн на прошедшую дату ({date})\n'
                    f'Сегодня {today.strftime("%Y-%m-%d")}\n'
                    f'Выберите другую дату'
                )
                return
        except ValueError:
                await event.respond(f'Неверный формат даты: {date}\nИспользуйте YYYY-MM-DD')
                return
        if db.deadline_exists_for_user(event.sender_id, title, date):
            await event.respond('Такой дедлайн уже существует')
            return
        db.add_deadline(event.sender_id, title, date)
        await event.respond(f'Дедлайн добавлен:\n{date}\n{title}')

    @client.on(events.NewMessage(pattern='/deadlines'))
    async def deadlines_handler(event):
        deadlines = db.get_deadlines(event.sender_id)
        
        if not deadlines:
            await event.respond('У тебя нет дедлайнов')
            return
        
        message = 'Твои дедлайны: \n\n'
        table = utils.format_deadline(deadlines)


        await event.respond(f'{message} `{table}` ')


    @client.on(events.NewMessage(pattern= '/done_deadline (\\d+)'))
    async def done_deadline_handler(event):
        deadline_id = int(event.pattern_match.group(1))
        deadline = db.get_one_deadline(deadline_id, event.sender_id)
        if not deadline:
            await event.respond(f'Дедлайн #{deadline_id} не найден')
            return
        if deadline and deadline[3] == 1:
            await event.respond(f'Дедлайн #{deadline_id} уже выполнен')
            return


        db.complete_deadline(deadline_id)
        await event.respond(f'Дедлайн #{deadline_id} выполнен')

    @client.on(events.NewMessage(pattern='/delete_deadline (\\d+)'))
    async def delete_deadline_handler(event):
        deadline_id = int(event.pattern_match.group(1))
        deadline = db.get_one_deadline(deadline_id, event.sender_id)
        if not deadline:
            await event.respond(f'Дедлайн #{deadline_id} не найден')
            return
        db.delete_deadline(deadline_id)
        await event.respond(f'Дедлайн #{deadline_id} удалён')


    @client.on(events.NewMessage(pattern = '/add_link (.+)'))
    async def add_link_handler(event):
        text = event.pattern_match.group(1).strip()
        parts = text.split(' ', 2)
        if len(parts) < 3:
            await client.send_message(
                event.chat_id,
                'Неправильный формат!\n'
                'Используйте: `/add_link категория название ссылка`\n'
                'Пример: `/add_link python Документация Python https://docs.python.org`'
            )
            return
        
        category = parts[0].strip()
        title = parts[1].strip()
        url = parts[2].strip()

        if not url.startswith(('http://', 'https://')):
            await client.send_message(
                event.chat_id,
                f'Ссылка должна начинаться с http:// или https://\n'
            )
            return
        
        if db.link_exists_for_user(event.sender_id, category, title):
            await event.respond('Уже существует ссылка с таким названием в этой категории')
            return

        db.add_link(event.sender_id, category, title, url)
        await event.respond(f'Ссылка добавлена')




    @client.on(events.NewMessage(pattern='/get_links(?: (.+))?'))
    async def get_links_handler(event):
        category = event.pattern_match.group(1)
        if not category:
            await event.respond('Категория не указана')
            return
        category = category.strip()
        links = db.get_links(event.sender_id, category)
        if not links:
            await event.respond(f'В категории {category} нет ссылок')
            return 
        
        message = f'Ссылки в категории {category}:\n\n'
        for link in links:
            link_id, title, url = link
            message += f"{title}\n{url}\n\n"
        await client.send_message(
        event.chat_id,
        message,
        link_preview=False
    )
        
    @client.on(events.NewMessage(pattern = '/categories'))
    async def categories_handler(event):
        categories = db.get_categories(event.sender_id)
        
        if not categories:
            await event.respond('У тебя пока нет категорий. Добавь ссылку через /add_link')
            return
        
        message = 'Твои категории\n\n'
        for cat in categories:
            links = db.get_links(event.sender_id, cat)
            count = len(links)
            message +=f'{cat} ({count} ссылок)\n'
        await event.respond(message)

    @client.on(events.NewMessage(pattern ='/export_links (\\w+)'))
    async def export_links_handler(event):
        category = event.pattern_match.group(1)
        links = db.get_links(event.sender_id, category)

        if not links:
            await event.respond(f'В категории {category} нет ссылок для экспорта')
            return
        
        filepath = utils.export_links_to_csv(event.sender_id, links, category)
        
        await client.send_file(
            event.chat_id,
            filepath,
            caption = f'Экспорт ссылок из категории {category}',
            attributes = [DocumentAttributeFilename(file_name = 'links.csv')]
        )

        await event.respond('Файл отправлен')

    @client.on(events.NewMessage(pattern = '/stats'))
    async def stats_handler(event):
        stats = db.get_stats(event.sender_id)
        message = f'Твоя статистика:\n\n'
        message += f'Активных дедлайнов: {len(stats["active_deadlines"])}\n'
        message += f'Всего дедлайнов: {stats["total_deadlines"]}\n'
        message += f'Всего ссылок: {stats["total_links"]}\n'
        message += f'Категорий: {stats["total_categories"]}\n'

        await event.respond(message)

    @client.on(events.NewMessage(pattern='/ping'))
    async def ping_handler(event):
        await event.respond('Бот работает')

    @client.on(events.NewMessage(pattern='/info'))
    async def info_handler(event):
        me = await client.get_me()
        user_count = db.get_user_count()
        await event.respond(
            f'Бот @{me.username}\n'
            f'ID: {me.id}\n'
            f'Пользователей в БД: {user_count}'
        )

    @client.on(events.NewMessage(pattern = '/clear_deadlines'))
    async def clear_deadlines_handler(event):
        deadlines = db.get_deadlines(event.sender_id, only_active=False)
        if not deadlines:
            await event.respond('У тебя нет дедлайнов для очистки!')
            return
        buttons = [
            [
                Button.inline('Удалить ВСЕ дедлайны', b'clear_all'),
                Button.inline('Удалить только выполненные дедлайны', b'clear_active')
            ],
            [Button.inline('Отмена', b'clear_cancel')]
        ]


        await event.respond(
            'Очистка дедлайнов\n\n'
            'Выберите действие',
            buttons = buttons
        )

    @client.on(events.NewMessage)
    async def unknown_command_handler(event):
        text = event.raw_text
        if not text:
            return
        known_commands = [
            # Основные
            '/start', '/help', '/ping', '/info', '/stats',
            
            # Дедлайны
            '/add_deadline', '/deadlines', '/done_deadline', '/delete_deadline',
            '/clear_deadlines',
            
            # Ссылки - добавление и просмотр
            '/add_link', '/get_links', '/categories',
            
            # Ссылки - удаление
            '/delete_link', '/delete_all', '/delete', '/cancel',
            
            # Ссылки - экспорт
            '/export_links'
        ]
        is_known = False
        for cmd in known_commands:
            if text.startswith(cmd):
                is_known = True
                break
        if is_known:
            return
        if text.startswith('/'):
            await event.respond(
                'Неизвестная команда\n'
                f'Доступные команды:\n\n'
                f'Дедлайны:\n'
                f'/add_deadline YYYY-MM-DD Название - добавить дедлайн\n'
                f'/deadlines - показать все дедлайны\n'
                f'/done_deadline N - отметить дедлайн выполненным\n'
                f'/delete_deadline N - удалить дедлайн\n\n'
                f'Ссылки:\n'
                f'/add_link категория название ссылка - добавить ссылку\n'
                f'/get_links категория - показать ссылки по категории\n'
                f'/categories - показать все категории\n'
                f'/export_links категория - выгрузить ссылки в CSV\n'
                f'/delete_link - удаление ссылок\n\n'
                f'Другое:\n'
                f'/stats - статистика\n'
                f'/info - информация о боте\n'
                f'/ping - проверить, жив ли бот\n'
                f'/start - показать это меню'
            )
            return 


    @client.on(events.NewMessage(pattern = '/help'))
    async def help_handler(event):
        await event.respond(f'Доступные команды:\n\n'
                f'Дедлайны:\n'
                f'/add_deadline YYYY-MM-DD Название - добавить дедлайн\n'
                f'/deadlines - показать все дедлайны\n'
                f'/done_deadline N - отметить дедлайн выполненным\n'
                f'/delete_deadline N - удалить дедлайн\n'
                f'/clear_deadlines - удалить все дедлайны, либо только выполненные\n\n'
                f'Ссылки:\n'
                f'/add_link категория название ссылка - добавить ссылку\n'
                f'/get_links категория - показать ссылки по категории\n'
                f'/categories - показать все категории\n'
                f'/export_links категория - выгрузить ссылки в CSV\n'
                f'/delete_link - удаление ссылок\n\n'
                f'Другое:\n'
                f'/stats - статистика\n'
                f'/info - информация о боте\n'
                f'/ping - проверить, жив ли бот\n'
                f'/start - показать это меню'
            )
    @client.on(events.CallbackQuery)
    async def clear_callback_handler(event):
        data = event.data.decode()
        if data == 'clear_all':
            deleted  = db.clear_deadlines(event.sender_id)
            await event.edit(f'🗑️ Удалено {deleted} дедлайнов (все)')
            await event.answer('✅ Все дедлайны удалены!')
        elif data == 'clear_active':
            deleted = db.clear_active_deadlines(event.sender_id)
            await event.edit(f'🗑️ Удалено {deleted} выполненных дедлайнов')
            await event.answer('✅ Активные дедлайны удалены!')
        elif data == 'clear_cancel':
            await event.edit('❌ Очистка отменена')
            await event.answer('Очистка отменена')

    @client.on(events.NewMessage(pattern = '/delete_link'))
    async def delete_link_start_handler(event):
        categories = db.get_categories(event.sender_id)
        
        if not categories:
            await client.send_message(
                event.chat_id, 
                'У тебя нет категорий.\n'
            )
            return
        delete_sessions[event.sender_id]={
            'state':DELETE_STATES['WAITING_CATEGORY'],
            'category': None,
            'links': None,
            'categories': categories
        }

        message = 'Выбери категорию для удаления ссылок:\n\n'
        for i, cat in enumerate(categories, 1):
            count = len(db.get_links(event.sender_id, cat))
            message +=f'{i}. {cat} ({count} ссылок)\n'

        message +='\nНапиши номер категории\n'
        message +='Или /cancel для отмены'
        await client.send_message(event.chat_id, message)

    @client.on(events.NewMessage)
    async def delete_link_category_handler(event):

        user_id = event.sender_id
        text = event.raw_text
        if text.startswith('/'):
             return
        if user_id not in delete_sessions:
            return 

        session = delete_sessions[user_id]
        if session['state'] == DELETE_STATES['CANCELLED']:
            del delete_sessions[user_id]
            return
        if session['state'] != DELETE_STATES['WAITING_CATEGORY']:
            return
        if text == '/cancel':
            del delete_sessions[user_id]
            await client.send_message(event.chat_id, 'Удаление отменено')
            return
        
        if not text.isdigit():
            await client.send_message(
                event.chat_id,
                'Введён не номер категории'
            )
            return 
        category_index = int(text)
        categories = db.get_categories(user_id)
        if category_index < 1 or category_index > len(categories):
            await client.send_message(
                event.chat_id,
                f'Неправильно введён номер категории'
            )
            return 
        category = categories[category_index - 1]
        links = db.get_links(user_id, category)
        if not links:
            await client.send_message(
                event.chat_id,
                f'В категории "{category}" нет ссылок для удаления'
            )
            del delete_sessions[user_id]
            return
        session['state'] = DELETE_STATES['WAITING_ACTION']
        session['category'] = category
        session['links'] = links

        message = f'Категория: {text}\n'
        message +='Список ссылок:\n'
        for link in links:
            link_id, title, url = link
            display_url = url if len(url) < 40 else url[:37] + '...'
            message += f'  #{link_id}: {title} ({display_url})\n'
        message +='\nЧто выполнить?\n'
        message +='/delete_all - удалить все ссылки в категории\n'
        message += '/delete <ID> - удалить конкретную ссылку (например /delete 5)\n'
        message += '/cancel - отменить удаление'
        await client.send_message(event.chat_id, message, link_preview = False)


    @client.on(events.NewMessage(pattern = '/delete_all'))
    async def delete_all_links_handler(event):
        user_id = event.sender_id

        if user_id not in delete_sessions:
            await client.send_message(
                event.chat_id,
                'Сначала выбери категорию: /delete_link'
            )
            return 
        session = delete_sessions[user_id]

        if session['state'] !=DELETE_STATES['WAITING_ACTION']:
            await client.send_message(
                event.chat_id, 
                'Сначала выбери категорию: /delete_link'
            )

        category = session['category']
        links = session['links']
        buttons = [
            [
                Button.inline(f'Да, удалить все', f'confirm_delete_all_{category}'),
                Button.inline('Отмена', f'cancel_delete_all_{category}')
            ]
        ]

        await client.send_message(
            event.chat_id,
            f'Вы уверены что хотите удалить ВСЕ ссылки в категории "{category}"?\n',
            buttons = buttons
        )
    @client.on(events.NewMessage(pattern = '/delete (\\d+)'))
    async def delete_specific_link_handler(event):
        try:
            link_id = int(event.pattern_match.group(1))
        except ValueError:
            await client.send_message(
                event.chat_id,
                'Id должен быть числом!, например, /delete 5'
            )
            return
        user_id = event.sender_id 

        if user_id not in delete_sessions:
            await client.send_message(
                event.chat_id,
                'Сначала выбери категорию: /delete_link'
            )
            return
        session = delete_sessions[user_id]

        if session['state'] != DELETE_STATES['WAITING_ACTION']:
            await client.send_message(
                event.chat_id,
                'Сначала выбери категорию: /delete_link'
            )
            return

        links = session['links']
        link_to_delete = None
        for link in links:
            if link[0] == link_id:
                link_to_delete = link
                break
        if not link_to_delete:
            await client.send_message(
                event.chat_id,
                f'Ссылка #{link_id} не найдена в категории "{session["category"]}"\n'
            )
            return
        
        _, title, url= link_to_delete

        buttons = [
            [
                Button.inline(f'Да, удалить #{link_id}', f'confirm_delete_specific_{link_id}'),
                Button.inline('Отмена', f'cancel_delete_specific_{link_id}')
            ]
        ]

        await client.send_message(
            event.chat_id,
            'Вы уверены что хотите удалить ссылку?\n\n'
            f'Категория: {session["category"]}\n'
            f'Название: {title}\n'
            f'Ссылка: {url}\n\n',
            buttons = buttons,
            link_preview = False
        )


    @client.on(events.CallbackQuery)
    async def delete_link_callback_handler(event):
        try:
            if not hasattr(event, 'data'):
                return
            data = event.data.decode()
            user_id = event.sender_id

            if data.startswith('confirm_delete_all_'):
                category = data.split('_', 3)[3]

                deleted = db.delete_category(user_id, category)

                if user_id in delete_sessions:
                    del delete_sessions[user_id]

                await event.edit(f'Категория "{category}" удалена')
                
            elif data.startswith('cancel_delete_all_'):
                category = data.split('_', 3)[3]

                if user_id in delete_sessions:
                    session = delete_sessions[user_id]
                    session['state'] = DELETE_STATES['WAITING_ACTION']
                await event.edit(f'Удаление категории "{category}" отменено')
            elif data.startswith('confirm_delete_specific_'):
                link_id = int(data.split('_')[3])

                success = db.delete_link(link_id, user_id)
                if success:
                    if user_id in delete_sessions:
                        session = delete_sessions[user_id]
                        session['links'] = [l for l in session['links'] if l[0] != link_id]

                        if not session['links']:
                            await event.edit(f'Ссылка #{link_id} удалена, в категории не осталось ссылок')
                            del delete_sessions[user_id]
                            return
                        
                    await event.edit(f'Ссылка #{link_id} удалена')
                else:
                    await event.edit(f'Ссылка #{link_id} не найдена')

            elif data.startswith('cancel_delete_specific_'):
                link_id = data.split('_')[3]

                if user_id in delete_sessions:
                    session = delete_sessions[user_id]
                    session['state'] = DELETE_STATES['WAITING_ACTION']

                await event.edit(f'Удаление ссылки #{link_id} отменено')
        except Exception as e:
            print(f'Ошибка {e}')
            await event.answer('Произошла ошибка', alert = True)


    @client.on(events.NewMessage(pattern = '/cancel'))
    async def cancel_handler(event):
        user_id = event.sender_id

        if user_id in delete_sessions:
            del delete_sessions[user_id]
            await client.send_message(event.chat_id, 'Операция отменена')
        else:
            await client.send_message(event.chat_id, 'Нет активной операции для отмены')