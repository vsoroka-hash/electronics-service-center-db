USE service_center_db;

-- 1. Список замовлень із клієнтом, пристроєм, статусом і сумою.
SELECT * FROM vw_order_summary ORDER BY accepted_at DESC;

-- 2. Замовлення конкретного майстра.
SELECT
  ro.order_id,
  CONCAT(d.brand, ' ', d.model) AS device_name,
  os.status_name,
  ro.planned_finish_date
FROM repair_order ro
JOIN device d ON d.device_id = ro.device_id
JOIN order_status os ON os.status_id = ro.status_id
WHERE ro.technician_id = 1
ORDER BY ro.planned_finish_date;

-- 3. Кількість ремонтів по типах пристроїв.
SELECT
  dt.type_name,
  COUNT(*) AS repairs_count
FROM repair_order ro
JOIN device d ON d.device_id = ro.device_id
JOIN device_type dt ON dt.device_type_id = d.device_type_id
GROUP BY dt.type_name
ORDER BY repairs_count DESC;

-- 4. Дохід сервісного центру за березень 2026.
SELECT
  DATE_FORMAT(payment_date, '%Y-%m') AS payment_month,
  SUM(amount) AS revenue
FROM payment
WHERE payment_date >= '2026-03-01' AND payment_date < '2026-04-01'
GROUP BY DATE_FORMAT(payment_date, '%Y-%m');

-- 5. Пристрої клієнта за номером телефону.
SELECT
  c.last_name,
  c.first_name,
  d.brand,
  d.model,
  d.serial_number
FROM client c
JOIN device d ON d.client_id = c.client_id
WHERE c.phone = '+380671234501';

-- 6. Запчастини, які треба дозамовити.
SELECT * FROM vw_parts_to_reorder;

-- 7. Середній чек по закритих або готових замовленнях.
SELECT
  ROUND(AVG(total_amount), 2) AS avg_order_total
FROM repair_order ro
JOIN order_status os ON os.status_id = ro.status_id
WHERE os.status_name IN ('Готове до видачі', 'Закрите');

-- 8. Незакриті термінові діагностики.
SELECT
  ro.order_id,
  diagnostic_result,
  estimated_cost,
  urgent_flag
FROM diagnostic d
JOIN repair_order ro ON ro.order_id = d.order_id
JOIN order_status os ON os.status_id = ro.status_id
WHERE d.urgent_flag = TRUE
  AND os.status_name <> 'Закрите';

-- 9. Вартість послуг і деталей у межах замовлення.
SELECT
  ro.order_id,
  COALESCE((
    SELECT SUM(osr.quantity * osr.agreed_price)
    FROM order_service osr
    WHERE osr.order_id = ro.order_id
  ), 0) AS services_total,
  COALESCE((
    SELECT SUM(op.quantity * op.unit_price)
    FROM order_part op
    WHERE op.order_id = ro.order_id
  ), 0) AS parts_total,
  ro.total_amount
FROM repair_order ro
ORDER BY ro.order_id;

-- 10. Виклик процедури створення замовлення.
CALL create_repair_order(2, 2, 'Заміна клавіатури та діагностика USB-портів', '2026-03-16');

-- 11. Додавання діагностики.
CALL add_diagnostic_entry(2, 'Пошкоджена клавіатурна матриця', 1400.00, FALSE);

-- 12. Додавання послуги до замовлення.
CALL add_service_to_order(2, 6, 1, 900.00);

-- 13. Додавання запчастини до замовлення.
CALL add_part_to_order(4, 4, 1, 480.00);

-- 14. Реєстрація платежу через процедуру.
CALL register_payment(4, 500.00, 'card');

-- 15. Перерахунок суми існуючого замовлення.
CALL recalculate_order_total(3);

-- 16. Закриття замовлення.
CALL close_repair_order(5);

-- 17. Дохід по місяцях.
SELECT * FROM vw_revenue_by_month ORDER BY payment_month;

-- 18. Завантаженість майстрів.
SELECT * FROM vw_technician_workload ORDER BY orders_count DESC, technician_name;
