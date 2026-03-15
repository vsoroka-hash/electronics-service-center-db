# Electronics Service Center DB

Система для курсового проєкту з баз даних: облік клієнтів, пристроїв, ремонтних замовлень, діагностики, послуг, запчастин, платежів і звітів сервісного центру ремонту електроніки.

## Структура проєкту

- `schema.sql` — повна схема MySQL: таблиці, ключі, тестові дані, `VIEW`, процедури, тригери.
- `queries.sql` — приклади SQL-запитів і перевірочних викликів.
- `app.py` — точка входу в застосунок.
- `reporting.py` — генерація діаграм і артефактів.
- `service_center/` — Python-код застосунку.
- `diagrams/` — джерела структурних діаграм у `PlantUML`.
- `tools/plantuml.jar` — локальний `PlantUML` для генерації PNG без окремої інсталяції.

## Функціональність

- ведення довідників клієнтів, пристроїв, послуг і запчастин;
- створення та супровід ремонтних замовлень;
- додавання діагностики, послуг, запчастин і платежів;
- контроль суми замовлення та складських залишків на рівні БД;
- звіти по доходу, статусах замовлень і навантаженню майстрів;
- генерація ER-діаграми та логічної схеми через `PlantUML`.

## Вимоги

- Python 3.13+
- MySQL 8.x
- доступ до локальної БД `service_center_db`

Python-залежності:

```bash
pip install -r requirements.txt
```

## Налаштування БД

За замовчуванням застосунок читає такі параметри:

- `DB_HOST=127.0.0.1`
- `DB_PORT=3306`
- `DB_USER=course_user`
- `DB_PASSWORD=1910`
- `DB_NAME=service_center_db`

За потреби їх можна перевизначити через змінні середовища.

## Ініціалізація схеми

Створення або перевідновлення БД:

```bash
mysql --default-character-set=utf8mb4 -u root -p < schema.sql
```

Запуск прикладів запитів:

```bash
mysql --default-character-set=utf8mb4 -u course_user -p service_center_db < queries.sql
```

## Запуск застосунку

GUI:

```bash
python app.py
```

CLI:

```bash
python app.py --cli
```

## Генерація діаграм

```bash
python reporting.py
```

Після запуску створюється папка `artifacts/` з файлами:

- `er_diagram.png`
- `schema_diagram.png`
- `revenue_chart.png`
- `status_chart.png`
- `technician_chart.png`

## Архітектура

- `service_center/config.py` — конфігурація підключення;
- `service_center/database.py` — доступ до MySQL і пул з’єднань;
- `service_center/services.py` — бізнес-операції;
- `service_center/gui.py` — графічний інтерфейс;
- `service_center/cli.py` — консольний інтерфейс;
- `service_center/visualization.py` — візуалізація і рендер діаграм;
- `service_center/table_view.py` — форматування таблиць для CLI.

## Примітка

`artifacts/` і `__pycache__/` не зберігаються в репозиторії, бо це згенеровані файли.
