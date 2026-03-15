from __future__ import annotations

from decimal import Decimal

from .database import Database


class ServiceCenterService:
    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    def list_orders(self) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT order_id, client_name, device_name, status_name, technician_name, total_amount
            FROM vw_order_summary
            ORDER BY accepted_at DESC
            """
        )

    def search_orders(self, phone: str, status: str) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT ro.order_id, CONCAT(c.last_name, ' ', c.first_name), CONCAT(d.brand, ' ', d.model),
                   os.status_name, ro.planned_finish_date, ro.total_amount
            FROM repair_order ro
            JOIN device d ON d.device_id = ro.device_id
            JOIN client c ON c.client_id = d.client_id
            JOIN order_status os ON os.status_id = ro.status_id
            WHERE (%s = '' OR c.phone = %s)
              AND (%s = '' OR os.status_name = %s)
            ORDER BY ro.accepted_at DESC
            """,
            (phone, phone, status, status),
        )

    def list_clients(self) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT client_id, last_name, first_name, phone, COALESCE(email, '')
            FROM client
            ORDER BY last_name, first_name
            """
        )

    def list_devices(self) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT d.device_id, CONCAT(c.last_name, ' ', c.first_name), dt.type_name,
                   d.brand, d.model, d.serial_number
            FROM device d
            JOIN client c ON c.client_id = d.client_id
            JOIN device_type dt ON dt.device_type_id = d.device_type_id
            ORDER BY d.device_id
            """
        )

    def list_device_types(self) -> list[tuple]:
        return self.database.fetch_all(
            "SELECT device_type_id, type_name FROM device_type ORDER BY device_type_id"
        )

    def list_technicians(self) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT technician_id, CONCAT(last_name, ' ', first_name), specialization
            FROM technician
            ORDER BY technician_id
            """
        )

    def list_services(self) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT service_id, service_name, base_price, estimated_hours, is_active
            FROM service_catalog
            ORDER BY service_id
            """
        )

    def list_parts(self) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT part_id, part_name, manufacturer, unit_price, quantity_in_stock
            FROM part
            ORDER BY part_id
            """
        )

    def add_client(self, last_name: str, first_name: str, phone: str, email: str | None) -> None:
        self.database.execute(
            """
            INSERT INTO client (last_name, first_name, phone, email)
            VALUES (%s, %s, %s, %s)
            """,
            (last_name, first_name, phone, email),
        )

    def add_device(
        self,
        client_id: int,
        device_type_id: int,
        brand: str,
        model: str,
        serial_number: str,
        purchase_year: int | None,
    ) -> None:
        self.database.execute(
            """
            INSERT INTO device (client_id, device_type_id, brand, model, serial_number, purchase_year)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (client_id, device_type_id, brand, model, serial_number, purchase_year),
        )

    def create_order(
        self, device_id: int, technician_id: int, issue_description: str, planned_finish: str
    ) -> None:
        self.database.call_procedure(
            "create_repair_order",
            [device_id, technician_id, issue_description, planned_finish],
        )

    def add_diagnostic(
        self, order_id: int, diagnostic_result: str, estimated_cost: Decimal, urgent_flag: bool
    ) -> None:
        self.database.call_procedure(
            "add_diagnostic_entry",
            [order_id, diagnostic_result, estimated_cost, urgent_flag],
        )

    def add_service_to_order(
        self, order_id: int, service_id: int, quantity: int, agreed_price: Decimal
    ) -> None:
        self.database.call_procedure(
            "add_service_to_order",
            [order_id, service_id, quantity, agreed_price],
        )

    def add_part_to_order(
        self, order_id: int, part_id: int, quantity: int, unit_price: Decimal
    ) -> None:
        self.database.call_procedure(
            "add_part_to_order",
            [order_id, part_id, quantity, unit_price],
        )

    def register_payment(self, order_id: int, amount: Decimal, method: str) -> None:
        self.database.call_procedure("register_payment", [order_id, amount, method])

    def order_summary(self, order_id: int) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT order_id, client_name, device_name, status_name, technician_name, total_amount
            FROM vw_order_summary
            WHERE order_id = %s
            """,
            (order_id,),
        )

    def order_services(self, order_id: int) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT sc.service_name, os.quantity, os.agreed_price
            FROM order_service os
            JOIN service_catalog sc ON sc.service_id = os.service_id
            WHERE os.order_id = %s
            """,
            (order_id,),
        )

    def order_parts(self, order_id: int) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT p.part_name, op.quantity, op.unit_price
            FROM order_part op
            JOIN part p ON p.part_id = op.part_id
            WHERE op.order_id = %s
            """,
            (order_id,),
        )

    def list_reorder_parts(self) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT part_id, part_name, manufacturer, quantity_in_stock, reorder_level
            FROM vw_parts_to_reorder
            ORDER BY part_name
            """
        )

    def revenue_report(self) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT payment_month, revenue, payments_count
            FROM vw_revenue_by_month
            ORDER BY payment_month
            """
        )

    def technician_report(self) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT technician_id, technician_name, orders_count, orders_total
            FROM vw_technician_workload
            ORDER BY orders_count DESC, technician_name
            """
        )

    def status_report(self) -> list[tuple]:
        return self.database.fetch_all(
            """
            SELECT os.status_name, COUNT(*) AS orders_count
            FROM repair_order ro
            JOIN order_status os ON os.status_id = ro.status_id
            GROUP BY os.status_name
            ORDER BY orders_count DESC, os.status_name
            """
        )

    def dashboard_metrics(self) -> dict[str, int | float]:
        counts = self.database.fetch_all(
            """
            SELECT
              (SELECT COUNT(*) FROM client) AS clients_count,
              (SELECT COUNT(*) FROM device) AS devices_count,
              (SELECT COUNT(*) FROM repair_order) AS orders_count,
              (SELECT COUNT(*) FROM payment) AS payments_count,
              (SELECT COALESCE(SUM(amount), 0) FROM payment) AS revenue_total
            """
        )[0]
        return {
            "clients_count": counts[0],
            "devices_count": counts[1],
            "orders_count": counts[2],
            "payments_count": counts[3],
            "revenue_total": float(counts[4]),
        }

    def close_order(self, order_id: int) -> None:
        self.database.call_procedure("close_repair_order", [order_id])
