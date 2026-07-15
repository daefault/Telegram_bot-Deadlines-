import csv
import os
from datetime import datetime
from config import EXPORT_PATH


def export_links_to_csv(user_id: int, links, category: str):

    date_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"links_{category}_{date_str}.csv"
    filepath = os.path.join(EXPORT_PATH, filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writerow(['№', 'Название', 'Ссылка'])
        for idx, link in enumerate(links, 1):
            writer.writerow([idx, link[1], link[2]])
    
    return filepath

def format_deadline(deadlines):
    rows = []
    for d in deadlines:
        id, title, date, done = d
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        date_str = date_obj.strftime('%d.%m.%Y')
        status = 'Выполнен✅' if done else 'В процессе⏳'
        rows.append({
            'id': f'#{id}',
            'title': title,
            'date': date_str,
            'status': status
        })
        max_id = max(len(row['id']) for row in rows)
        max_title = max(len(row['title']) for row in rows)
        max_date = max(len(row['date']) for row in rows)
        max_status = max(len(row['status']) for row in rows)
        
        max_id = max(max_id, 4) 
        max_title = max(max_title, 8)  
        max_date = max(max_date, 6)  
        max_status = max(max_status, 8) 
        header = (
        f"{'ID'.ljust(max_id)} "
        f"{'Название'.ljust(max_title)} "
        f"{'Дата'.ljust(max_date)} "
        f"{'Статус'.ljust(max_status)}"
    )
        separator = '-' * (max_id + max_title + max_date + max_status + 5)

        lines = [header, separator]
        for row in rows:
            lines.append(
                f"{row['id'].ljust(max_id)} "
                f"{row['title'].ljust(max_title)} "
                f"{row['date'].ljust(max_date)} "
                f"{row['status'].ljust(max_status)}"
            )
    return '\n'.join(lines)

