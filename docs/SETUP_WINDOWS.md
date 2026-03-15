# Windows Setup

## Передумови

- Windows 10 або новіше
- Python 3.13+
- MySQL Server 8.x

## Встановлення залежностей Python

```powershell
pip install -r requirements.txt
```

## Підготовка бази даних

Імпорт схеми:

```powershell
mysql --default-character-set=utf8mb4 -u root -p < schema.sql
```

Запуск перевірочних SQL-запитів:

```powershell
mysql --default-character-set=utf8mb4 -u course_user -p service_center_db < queries.sql
```

## Запуск застосунку

GUI:

```powershell
python app.py
```

CLI:

```powershell
python app.py --cli
```

## Генерація артефактів

```powershell
python reporting.py
```

Після цього буде створено папку `artifacts/`.
