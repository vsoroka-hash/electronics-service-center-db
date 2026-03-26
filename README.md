# Electronics Service Center DB

Курсовий проєкт з дисципліни «Бази даних» на тему розробки бази даних сервісного центру ремонту електроніки. Репозиторій містить SQL-схему, прикладний Python-застосунок, діаграми та автотести.

## Що реалізовано

- облік клієнтів, пристроїв і ремонтних замовлень;
- збереження діагностики, послуг, деталей і платежів;
- контроль цілісності даних через `PK`, `FK`, `CHECK`, `VIEW`, процедури й тригери;
- GUI на `Tkinter` і резервний CLI-режим;
- аналітичні графіки для звітності;
- ER-діаграма та логічна схема БД.

## Структура репозиторію

- `schema.sql` — повна структура MySQL-бази, ролі, представлення, процедури, тригери та демонстраційні дані.
- `queries.sql` — приклади SQL-запитів для вибірок, агрегацій, підзапитів і звітів.
- `app.py` — точка входу в застосунок.
- `reporting.py` — запуск генерації графіків і діаграм.
- `service_center/` — прикладний код.
- `tests/` — автотести сервісного шару та модуля візуалізації.
- `diagrams/` — вихідні `PlantUML`-файли.
- `docs/` — технічна документація.
- `tools/plantuml.jar` — локальний `PlantUML`, якщо на машині є Java.

## Технології

- Python 3.9+
- MySQL 8.x
- Tkinter
- `mysql-connector-python`
- `matplotlib`
- `pytest`
- `PlantUML`

## Швидкий старт

1. Встановити залежності:

```bash
pip install -r requirements.txt
```

2. Імпортувати схему:

```bash
mysql --default-character-set=utf8mb4 -u root -p < schema.sql
```

3. За потреби виконати демонстраційні SQL-запити:

```bash
mysql --default-character-set=utf8mb4 -u course_user -p service_center_db < queries.sql
```

4. Запустити застосунок:

```bash
python app.py
```

5. Або запустити CLI:

```bash
python app.py --cli
```

## Параметри підключення

За замовчуванням застосунок читає такі змінні середовища:

- `DB_HOST=127.0.0.1`
- `DB_PORT=3306`
- `DB_USER=course_user`
- `DB_PASSWORD=1910`
- `DB_NAME=service_center_db`

Їх можна перевизначити через змінні середовища без зміни коду.

## Генерація звітів і діаграм

```bash
python reporting.py
```

Після запуску створюється папка `artifacts/` з файлами:

- `revenue_chart.png`
- `status_chart.png`
- `technician_chart.png`
- `er_diagram.png`
- `schema_diagram.png`

Якщо Java або `PlantUML` недоступні, модуль усе одно сформує аналітичні графіки й не зупинить виконання з помилкою.

## Тестування

Автотести:

```bash
python -m pytest -q
```

Додатково можна перевірити CLI без підключення до БД:

```bash
python app.py --cli
```

## Документація

- `docs/ARCHITECTURE.md`
- `docs/SETUP_WINDOWS.md`

## Чистота репозиторію

У `.gitignore` винесено службові та згенеровані файли:

- `artifacts/`
- `.pytest_cache/`
- `__pycache__/`
- `.DS_Store`
- `*.bak`
- фінальний `.docx` курсової роботи
