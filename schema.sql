CREATE DATABASE IF NOT EXISTS service_center_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE service_center_db;

DROP VIEW IF EXISTS vw_revenue_by_month;
DROP VIEW IF EXISTS vw_technician_workload;
DROP VIEW IF EXISTS vw_order_summary;
DROP VIEW IF EXISTS vw_parts_to_reorder;

DROP PROCEDURE IF EXISTS register_payment;
DROP PROCEDURE IF EXISTS add_part_to_order;
DROP PROCEDURE IF EXISTS add_service_to_order;
DROP PROCEDURE IF EXISTS add_diagnostic_entry;
DROP PROCEDURE IF EXISTS close_repair_order;
DROP PROCEDURE IF EXISTS create_repair_order;
DROP PROCEDURE IF EXISTS recalculate_order_total;

DROP TABLE IF EXISTS payment;
DROP TABLE IF EXISTS order_service;
DROP TABLE IF EXISTS order_part;
DROP TABLE IF EXISTS diagnostic;
DROP TABLE IF EXISTS repair_order;
DROP TABLE IF EXISTS part;
DROP TABLE IF EXISTS service_catalog;
DROP TABLE IF EXISTS device;
DROP TABLE IF EXISTS technician;
DROP TABLE IF EXISTS client;
DROP TABLE IF EXISTS order_status;
DROP TABLE IF EXISTS device_type;

CREATE TABLE device_type (
  device_type_id INT AUTO_INCREMENT PRIMARY KEY,
  type_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE order_status (
  status_id INT AUTO_INCREMENT PRIMARY KEY,
  status_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE client (
  client_id INT AUTO_INCREMENT PRIMARY KEY,
  last_name VARCHAR(100) NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  phone VARCHAR(20) NOT NULL UNIQUE,
  email VARCHAR(120) NULL UNIQUE,
  registered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE technician (
  technician_id INT AUTO_INCREMENT PRIMARY KEY,
  last_name VARCHAR(100) NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  specialization VARCHAR(120) NOT NULL,
  hire_date DATE NOT NULL,
  phone VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE device (
  device_id INT AUTO_INCREMENT PRIMARY KEY,
  client_id INT NOT NULL,
  device_type_id INT NOT NULL,
  brand VARCHAR(80) NOT NULL,
  model VARCHAR(120) NOT NULL,
  serial_number VARCHAR(120) NOT NULL UNIQUE,
  purchase_year YEAR NULL,
  CONSTRAINT fk_device_client
    FOREIGN KEY (client_id) REFERENCES client (client_id),
  CONSTRAINT fk_device_type
    FOREIGN KEY (device_type_id) REFERENCES device_type (device_type_id)
);

CREATE TABLE service_catalog (
  service_id INT AUTO_INCREMENT PRIMARY KEY,
  service_name VARCHAR(150) NOT NULL UNIQUE,
  base_price DECIMAL(10, 2) NOT NULL,
  estimated_hours DECIMAL(5, 2) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE part (
  part_id INT AUTO_INCREMENT PRIMARY KEY,
  part_name VARCHAR(150) NOT NULL,
  manufacturer VARCHAR(100) NOT NULL,
  unit_price DECIMAL(10, 2) NOT NULL,
  quantity_in_stock INT NOT NULL DEFAULT 0,
  reorder_level INT NOT NULL DEFAULT 2,
  UNIQUE KEY uq_part_name_manufacturer (part_name, manufacturer)
);

CREATE TABLE repair_order (
  order_id INT AUTO_INCREMENT PRIMARY KEY,
  device_id INT NOT NULL,
  technician_id INT NULL,
  status_id INT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  accepted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  planned_finish_date DATE NULL,
  completed_at DATETIME NULL,
  issue_description TEXT NOT NULL,
  total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
  warranty_days INT NOT NULL DEFAULT 0,
  CONSTRAINT fk_order_device
    FOREIGN KEY (device_id) REFERENCES device (device_id),
  CONSTRAINT fk_order_technician
    FOREIGN KEY (technician_id) REFERENCES technician (technician_id),
  CONSTRAINT fk_order_status
    FOREIGN KEY (status_id) REFERENCES order_status (status_id),
  CONSTRAINT chk_total_amount CHECK (total_amount >= 0),
  CONSTRAINT chk_warranty_days CHECK (warranty_days >= 0)
);

CREATE TABLE diagnostic (
  diagnostic_id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  diagnostic_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  diagnostic_result TEXT NOT NULL,
  estimated_cost DECIMAL(10, 2) NOT NULL,
  urgent_flag BOOLEAN NOT NULL DEFAULT FALSE,
  CONSTRAINT fk_diagnostic_order
    FOREIGN KEY (order_id) REFERENCES repair_order (order_id),
  CONSTRAINT chk_estimated_cost CHECK (estimated_cost >= 0)
);

CREATE TABLE order_part (
  order_part_id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  part_id INT NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(10, 2) NOT NULL,
  CONSTRAINT fk_order_part_order
    FOREIGN KEY (order_id) REFERENCES repair_order (order_id),
  CONSTRAINT fk_order_part_part
    FOREIGN KEY (part_id) REFERENCES part (part_id),
  CONSTRAINT chk_order_part_qty CHECK (quantity > 0),
  CONSTRAINT chk_order_part_price CHECK (unit_price >= 0),
  UNIQUE KEY uq_order_part (order_id, part_id)
);

CREATE TABLE order_service (
  order_service_id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  service_id INT NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  agreed_price DECIMAL(10, 2) NOT NULL,
  CONSTRAINT fk_order_service_order
    FOREIGN KEY (order_id) REFERENCES repair_order (order_id),
  CONSTRAINT fk_order_service_service
    FOREIGN KEY (service_id) REFERENCES service_catalog (service_id),
  CONSTRAINT chk_order_service_qty CHECK (quantity > 0),
  CONSTRAINT chk_order_service_price CHECK (agreed_price >= 0),
  UNIQUE KEY uq_order_service (order_id, service_id)
);

CREATE TABLE payment (
  payment_id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  payment_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  amount DECIMAL(10, 2) NOT NULL,
  payment_method ENUM('cash', 'card', 'transfer') NOT NULL,
  CONSTRAINT fk_payment_order
    FOREIGN KEY (order_id) REFERENCES repair_order (order_id),
  CONSTRAINT chk_payment_amount CHECK (amount > 0)
);

INSERT INTO device_type (type_name) VALUES
('Смартфон'),
('Ноутбук'),
('Планшет'),
('Ігрова консоль'),
('Смарт-годинник');

INSERT INTO order_status (status_name) VALUES
('Нове'),
('На діагностиці'),
('Очікує запчастини'),
('У ремонті'),
('Готове до видачі'),
('Закрите');

INSERT INTO client (last_name, first_name, phone, email) VALUES
('Коваленко', 'Ірина', '+380671234501', 'i.kovalenko@example.com'),
('Мельник', 'Олег', '+380671234502', 'o.melnyk@example.com'),
('Ткачук', 'Софія', '+380671234503', 's.tkachuk@example.com'),
('Шевченко', 'Дмитро', '+380671234504', 'd.shevchenko@example.com'),
('Бондар', 'Марія', '+380671234505', 'm.bondar@example.com');

INSERT INTO technician (last_name, first_name, specialization, hire_date, phone) VALUES
('Петренко', 'Андрій', 'Смартфони та планшети', '2022-05-10', '+380501111111'),
('Савчук', 'Роман', 'Ноутбуки та материнські плати', '2021-03-15', '+380502222222'),
('Лисенко', 'Наталія', 'Пайка та мікросхеми', '2023-01-20', '+380503333333');

INSERT INTO device (client_id, device_type_id, brand, model, serial_number, purchase_year) VALUES
(1, 1, 'Apple', 'iPhone 13', 'SN-IP13-001', 2022),
(2, 2, 'Lenovo', 'ThinkPad E14', 'SN-LNV-002', 2021),
(3, 3, 'Samsung', 'Galaxy Tab S8', 'SN-SGT-003', 2023),
(4, 4, 'Sony', 'PlayStation 5', 'SN-PS5-004', 2022),
(5, 1, 'Xiaomi', 'Redmi Note 12', 'SN-XRM-005', 2023);

INSERT INTO service_catalog (service_name, base_price, estimated_hours, is_active) VALUES
('Діагностика пристрою', 300.00, 1.00, TRUE),
('Заміна дисплея', 2500.00, 2.50, TRUE),
('Заміна акумулятора', 1200.00, 1.50, TRUE),
('Чистка після залиття', 1800.00, 3.00, TRUE),
('Ремонт материнської плати', 3200.00, 4.50, TRUE),
('Профілактична чистка ноутбука', 900.00, 1.00, TRUE);

INSERT INTO part (part_name, manufacturer, unit_price, quantity_in_stock, reorder_level) VALUES
('OLED дисплей iPhone 13', 'Apple OEM', 5400.00, 3, 2),
('Акумулятор Redmi Note 12', 'Xiaomi OEM', 950.00, 6, 3),
('Кулер Lenovo ThinkPad E14', 'CoolerMaster', 700.00, 3, 2),
('HDMI порт PS5', 'Sony OEM', 480.00, 5, 2),
('Конектор живлення Samsung Tab', 'Samsung OEM', 260.00, 10, 4);

INSERT INTO repair_order (
  device_id, technician_id, status_id, accepted_at, planned_finish_date,
  issue_description, total_amount, warranty_days
) VALUES
(1, 1, 4, '2026-03-01 10:15:00', '2026-03-05', 'Розбитий дисплей після падіння', 0.00, 90),
(2, 2, 2, '2026-03-02 11:30:00', '2026-03-08', 'Ноутбук перегрівається та вимикається', 0.00, 60),
(3, 1, 3, '2026-03-03 09:45:00', '2026-03-10', 'Не заряджається планшет', 0.00, 30),
(4, 3, 4, '2026-03-04 14:20:00', '2026-03-09', 'Пошкоджено HDMI порт', 0.00, 120),
(5, 1, 5, '2026-03-05 16:00:00', '2026-03-06', 'Швидко розряджається акумулятор', 0.00, 90);

INSERT INTO diagnostic (order_id, diagnostic_date, diagnostic_result, estimated_cost, urgent_flag) VALUES
(1, '2026-03-01 12:00:00', 'Потрібна заміна дисплея', 7900.00, FALSE),
(2, '2026-03-02 15:10:00', 'Потрібна чистка системи охолодження', 1600.00, FALSE),
(3, '2026-03-03 13:25:00', 'Несправний конектор живлення', 850.00, TRUE),
(4, '2026-03-04 17:00:00', 'Пошкоджений HDMI порт, потрібна пайка', 2100.00, TRUE),
(5, '2026-03-05 17:10:00', 'Потрібна заміна акумулятора', 2150.00, FALSE);

INSERT INTO order_service (order_id, service_id, quantity, agreed_price) VALUES
(1, 1, 1, 300.00),
(1, 2, 1, 2500.00),
(2, 1, 1, 300.00),
(2, 6, 1, 900.00),
(3, 1, 1, 300.00),
(4, 1, 1, 300.00),
(4, 5, 1, 3200.00),
(5, 1, 1, 300.00),
(5, 3, 1, 1200.00);

INSERT INTO order_part (order_id, part_id, quantity, unit_price) VALUES
(1, 1, 1, 5400.00),
(3, 5, 1, 260.00),
(4, 4, 1, 480.00),
(5, 2, 1, 950.00);

INSERT INTO payment (order_id, payment_date, amount, payment_method) VALUES
(1, '2026-03-05 18:00:00', 8200.00, 'card'),
(5, '2026-03-06 12:10:00', 2450.00, 'cash');

DELIMITER //

CREATE PROCEDURE recalculate_order_total(IN p_order_id INT)
BEGIN
  DECLARE v_service_total DECIMAL(10, 2) DEFAULT 0.00;
  DECLARE v_part_total DECIMAL(10, 2) DEFAULT 0.00;

  SELECT COALESCE(SUM(quantity * agreed_price), 0.00)
    INTO v_service_total
  FROM order_service
  WHERE order_id = p_order_id;

  SELECT COALESCE(SUM(quantity * unit_price), 0.00)
    INTO v_part_total
  FROM order_part
  WHERE order_id = p_order_id;

  UPDATE repair_order
  SET total_amount = v_service_total + v_part_total
  WHERE order_id = p_order_id;
END//

CREATE TRIGGER trg_order_part_before_insert
BEFORE INSERT ON order_part
FOR EACH ROW
BEGIN
  DECLARE v_stock INT;

  SELECT quantity_in_stock INTO v_stock
  FROM part
  WHERE part_id = NEW.part_id;

  IF v_stock IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Запчастину не знайдено';
  END IF;

  IF v_stock < NEW.quantity THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Недостатньо запчастин на складі';
  END IF;
END//

CREATE TRIGGER trg_order_part_after_insert
AFTER INSERT ON order_part
FOR EACH ROW
BEGIN
  UPDATE part
  SET quantity_in_stock = quantity_in_stock - NEW.quantity
  WHERE part_id = NEW.part_id;

  CALL recalculate_order_total(NEW.order_id);
END//

CREATE TRIGGER trg_order_part_before_update
BEFORE UPDATE ON order_part
FOR EACH ROW
BEGIN
  DECLARE v_available INT;

  IF NEW.part_id = OLD.part_id THEN
    SELECT quantity_in_stock + OLD.quantity INTO v_available
    FROM part
    WHERE part_id = NEW.part_id;
  ELSE
    SELECT quantity_in_stock INTO v_available
    FROM part
    WHERE part_id = NEW.part_id;
  END IF;

  IF v_available IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Запчастину не знайдено для оновлення';
  END IF;

  IF v_available < NEW.quantity THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Недостатньо запчастин на складі для оновлення';
  END IF;
END//

CREATE TRIGGER trg_order_part_after_update
AFTER UPDATE ON order_part
FOR EACH ROW
BEGIN
  IF NEW.part_id = OLD.part_id THEN
    UPDATE part
    SET quantity_in_stock = quantity_in_stock + OLD.quantity - NEW.quantity
    WHERE part_id = NEW.part_id;
  ELSE
    UPDATE part
    SET quantity_in_stock = quantity_in_stock + OLD.quantity
    WHERE part_id = OLD.part_id;

    UPDATE part
    SET quantity_in_stock = quantity_in_stock - NEW.quantity
    WHERE part_id = NEW.part_id;
  END IF;

  CALL recalculate_order_total(NEW.order_id);
END//

CREATE TRIGGER trg_order_part_after_delete
AFTER DELETE ON order_part
FOR EACH ROW
BEGIN
  UPDATE part
  SET quantity_in_stock = quantity_in_stock + OLD.quantity
  WHERE part_id = OLD.part_id;

  CALL recalculate_order_total(OLD.order_id);
END//

CREATE TRIGGER trg_order_service_after_insert
AFTER INSERT ON order_service
FOR EACH ROW
BEGIN
  CALL recalculate_order_total(NEW.order_id);
END//

CREATE TRIGGER trg_order_service_after_update
AFTER UPDATE ON order_service
FOR EACH ROW
BEGIN
  CALL recalculate_order_total(NEW.order_id);
END//

CREATE TRIGGER trg_order_service_after_delete
AFTER DELETE ON order_service
FOR EACH ROW
BEGIN
  CALL recalculate_order_total(OLD.order_id);
END//

CREATE TRIGGER trg_payment_before_insert
BEFORE INSERT ON payment
FOR EACH ROW
BEGIN
  DECLARE v_total DECIMAL(10, 2);
  DECLARE v_paid DECIMAL(10, 2);

  SELECT total_amount INTO v_total
  FROM repair_order
  WHERE order_id = NEW.order_id;

  SELECT COALESCE(SUM(amount), 0.00) INTO v_paid
  FROM payment
  WHERE order_id = NEW.order_id;

  IF v_paid + NEW.amount > v_total THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Сума платежів перевищує суму замовлення';
  END IF;
END//

CREATE TRIGGER trg_payment_before_update
BEFORE UPDATE ON payment
FOR EACH ROW
BEGIN
  DECLARE v_total DECIMAL(10, 2);
  DECLARE v_paid DECIMAL(10, 2);

  SELECT total_amount INTO v_total
  FROM repair_order
  WHERE order_id = NEW.order_id;

  SELECT COALESCE(SUM(amount), 0.00) INTO v_paid
  FROM payment
  WHERE order_id = NEW.order_id
    AND payment_id <> OLD.payment_id;

  IF v_paid + NEW.amount > v_total THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Після оновлення сума платежів перевищує суму замовлення';
  END IF;
END//

CREATE PROCEDURE create_repair_order(
  IN p_device_id INT,
  IN p_technician_id INT,
  IN p_issue_description TEXT,
  IN p_planned_finish DATE
)
BEGIN
  INSERT INTO repair_order (
    device_id, technician_id, status_id, issue_description, planned_finish_date
  )
  VALUES (
    p_device_id, p_technician_id,
    (SELECT status_id FROM order_status WHERE status_name = 'Нове'),
    p_issue_description, p_planned_finish
  );
END//

CREATE PROCEDURE add_diagnostic_entry(
  IN p_order_id INT,
  IN p_result TEXT,
  IN p_estimated_cost DECIMAL(10, 2),
  IN p_urgent_flag BOOLEAN
)
BEGIN
  INSERT INTO diagnostic (order_id, diagnostic_result, estimated_cost, urgent_flag)
  VALUES (p_order_id, p_result, p_estimated_cost, p_urgent_flag);

  UPDATE repair_order
  SET status_id = (SELECT status_id FROM order_status WHERE status_name = 'На діагностиці')
  WHERE order_id = p_order_id
    AND status_id = (SELECT status_id FROM order_status WHERE status_name = 'Нове');
END//

CREATE PROCEDURE add_service_to_order(
  IN p_order_id INT,
  IN p_service_id INT,
  IN p_quantity INT,
  IN p_agreed_price DECIMAL(10, 2)
)
BEGIN
  INSERT INTO order_service (order_id, service_id, quantity, agreed_price)
  VALUES (p_order_id, p_service_id, p_quantity, p_agreed_price)
  ON DUPLICATE KEY UPDATE
    quantity = quantity + VALUES(quantity),
    agreed_price = VALUES(agreed_price);
END//

CREATE PROCEDURE add_part_to_order(
  IN p_order_id INT,
  IN p_part_id INT,
  IN p_quantity INT,
  IN p_unit_price DECIMAL(10, 2)
)
BEGIN
  INSERT INTO order_part (order_id, part_id, quantity, unit_price)
  VALUES (p_order_id, p_part_id, p_quantity, p_unit_price)
  ON DUPLICATE KEY UPDATE
    quantity = quantity + VALUES(quantity),
    unit_price = VALUES(unit_price);
END//

CREATE PROCEDURE register_payment(
  IN p_order_id INT,
  IN p_amount DECIMAL(10, 2),
  IN p_payment_method VARCHAR(20)
)
BEGIN
  IF p_payment_method NOT IN ('cash', 'card', 'transfer') THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Неприпустимий метод оплати';
  END IF;

  INSERT INTO payment (order_id, amount, payment_method)
  VALUES (p_order_id, p_amount, p_payment_method);
END//

CREATE PROCEDURE close_repair_order(IN p_order_id INT)
BEGIN
  UPDATE repair_order
  SET status_id = (SELECT status_id FROM order_status WHERE status_name = 'Закрите'),
      completed_at = NOW()
  WHERE order_id = p_order_id;
END//

DELIMITER ;

CREATE VIEW vw_order_summary AS
SELECT
  ro.order_id,
  CONCAT(c.last_name, ' ', c.first_name) AS client_name,
  CONCAT(d.brand, ' ', d.model) AS device_name,
  os.status_name,
  CONCAT(t.last_name, ' ', t.first_name) AS technician_name,
  ro.accepted_at,
  ro.planned_finish_date,
  ro.total_amount
FROM repair_order ro
JOIN device d ON d.device_id = ro.device_id
JOIN client c ON c.client_id = d.client_id
JOIN order_status os ON os.status_id = ro.status_id
LEFT JOIN technician t ON t.technician_id = ro.technician_id;

CREATE VIEW vw_parts_to_reorder AS
SELECT
  part_id,
  part_name,
  manufacturer,
  quantity_in_stock,
  reorder_level
FROM part
WHERE quantity_in_stock <= reorder_level;

CREATE VIEW vw_revenue_by_month AS
SELECT
  DATE_FORMAT(payment_date, '%Y-%m') AS payment_month,
  SUM(amount) AS revenue,
  COUNT(*) AS payments_count
FROM payment
GROUP BY DATE_FORMAT(payment_date, '%Y-%m');

CREATE VIEW vw_technician_workload AS
SELECT
  t.technician_id,
  CONCAT(t.last_name, ' ', t.first_name) AS technician_name,
  COUNT(ro.order_id) AS orders_count,
  COALESCE(SUM(ro.total_amount), 0) AS orders_total
FROM technician t
LEFT JOIN repair_order ro ON ro.technician_id = t.technician_id
GROUP BY t.technician_id, CONCAT(t.last_name, ' ', t.first_name);

CALL recalculate_order_total(1);
CALL recalculate_order_total(2);
CALL recalculate_order_total(3);
CALL recalculate_order_total(4);
CALL recalculate_order_total(5);

CREATE ROLE IF NOT EXISTS receptionist;
CREATE ROLE IF NOT EXISTS technician_role;
CREATE ROLE IF NOT EXISTS administrator_role;

GRANT SELECT, INSERT, UPDATE ON service_center_db.client TO receptionist;
GRANT SELECT, INSERT, UPDATE ON service_center_db.device TO receptionist;
GRANT SELECT, INSERT, UPDATE ON service_center_db.repair_order TO receptionist;
GRANT SELECT, INSERT ON service_center_db.payment TO receptionist;
GRANT SELECT ON service_center_db.vw_order_summary TO receptionist;

GRANT SELECT ON service_center_db.client TO technician_role;
GRANT SELECT ON service_center_db.device TO technician_role;
GRANT SELECT, UPDATE ON service_center_db.repair_order TO technician_role;
GRANT SELECT, INSERT, UPDATE ON service_center_db.diagnostic TO technician_role;
GRANT SELECT, INSERT, UPDATE ON service_center_db.order_service TO technician_role;
GRANT SELECT, INSERT, UPDATE ON service_center_db.order_part TO technician_role;
GRANT SELECT ON service_center_db.part TO technician_role;
GRANT SELECT ON service_center_db.vw_parts_to_reorder TO technician_role;

GRANT ALL PRIVILEGES ON service_center_db.* TO administrator_role;
