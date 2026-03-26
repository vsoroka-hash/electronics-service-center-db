from __future__ import annotations

import sys
from decimal import Decimal
from typing import Optional

import mysql.connector

from .services import ServiceCenterService
from .table_view import print_rows
from .visualization import ArtifactGenerator


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


class ServiceCenterCLI:
    def __init__(
        self,
        service: Optional[ServiceCenterService] = None,
        artifact_generator: Optional[ArtifactGenerator] = None,
    ) -> None:
        self.service = service or ServiceCenterService()
        self.artifact_generator = artifact_generator or ArtifactGenerator()

    def show_orders(self) -> None:
        print_rows(["ID", "Клієнт", "Пристрій", "Статус", "Майстер", "Сума"], self.service.list_orders())

    def search_orders(self) -> None:
        phone = input("Телефон клієнта або Enter для пропуску: ").strip()
        status = input("Статус замовлення або Enter для пропуску: ").strip()
        print_rows(
            ["ID", "Клієнт", "Пристрій", "Статус", "Термін", "Сума"],
            self.service.search_orders(phone, status),
        )

    def show_clients(self) -> None:
        print_rows(["ID", "Прізвище", "Ім'я", "Телефон", "Email"], self.service.list_clients())

    def show_devices(self) -> None:
        print_rows(["ID", "Клієнт", "Тип", "Бренд", "Модель", "Серійний №"], self.service.list_devices())

    def show_services(self) -> None:
        print_rows(["ID", "Послуга", "Базова ціна", "Години", "Активна"], self.service.list_services())

    def show_parts(self) -> None:
        print_rows(["ID", "Запчастина", "Виробник", "Ціна", "Залишок"], self.service.list_parts())

    def add_client(self) -> None:
        self.service.add_client(
            input("Прізвище: ").strip(),
            input("Ім'я: ").strip(),
            input("Телефон: ").strip(),
            input("Email або Enter: ").strip() or None,
        )
        print("Клієнта додано.")

    def add_device(self) -> None:
        self.show_clients()
        client_id = int(input("ID клієнта: ").strip())
        print_rows(["ID", "Тип пристрою"], self.service.list_device_types())
        device_type_id = int(input("ID типу пристрою: ").strip())
        brand = input("Бренд: ").strip()
        model = input("Модель: ").strip()
        serial_number = input("Серійний номер: ").strip()
        purchase_year_raw = input("Рік придбання або Enter: ").strip()
        purchase_year = int(purchase_year_raw) if purchase_year_raw else None
        self.service.add_device(client_id, device_type_id, brand, model, serial_number, purchase_year)
        print("Пристрій додано.")

    def create_order(self) -> None:
        self.show_devices()
        device_id = int(input("ID пристрою: ").strip())
        print_rows(["ID", "Майстер", "Спеціалізація"], self.service.list_technicians())
        technician_id = int(input("ID майстра: ").strip())
        issue_description = input("Опис несправності: ").strip()
        planned_finish = input("Планова дата завершення (YYYY-MM-DD): ").strip()
        self.service.create_order(device_id, technician_id, issue_description, planned_finish)
        print("Замовлення створено.")

    def add_diagnostic(self) -> None:
        self.service.add_diagnostic(
            int(input("ID замовлення: ").strip()),
            input("Результат діагностики: ").strip(),
            Decimal(input("Орієнтовна вартість: ").strip()),
            input("Термінове? (y/n): ").strip().lower() == "y",
        )
        print("Діагностику додано.")

    def add_service_to_order(self) -> None:
        order_id = int(input("ID замовлення: ").strip())
        self.show_services()
        service_id = int(input("ID послуги: ").strip())
        quantity = int(input("Кількість: ").strip())
        agreed_price = Decimal(input("Узгоджена ціна: ").strip())
        self.service.add_service_to_order(order_id, service_id, quantity, agreed_price)
        print("Послугу додано до замовлення.")

    def add_part_to_order(self) -> None:
        order_id = int(input("ID замовлення: ").strip())
        self.show_parts()
        part_id = int(input("ID запчастини: ").strip())
        quantity = int(input("Кількість: ").strip())
        unit_price = Decimal(input("Ціна одиниці: ").strip())
        self.service.add_part_to_order(order_id, part_id, quantity, unit_price)
        print("Запчастину додано до замовлення.")

    def add_payment(self) -> None:
        self.service.register_payment(
            int(input("ID замовлення: ").strip()),
            Decimal(input("Сума платежу: ").strip()),
            input("Метод оплати (cash/card/transfer): ").strip(),
        )
        print("Платіж зареєстровано.")

    def show_order_details(self) -> None:
        order_id = int(input("ID замовлення: ").strip())
        print_rows(["ID", "Клієнт", "Пристрій", "Статус", "Майстер", "Сума"], self.service.order_summary(order_id))
        print("\nПослуги:")
        print_rows(["Послуга", "Кількість", "Ціна"], self.service.order_services(order_id))
        print("\nЗапчастини:")
        print_rows(["Запчастина", "Кількість", "Ціна"], self.service.order_parts(order_id))

    def show_reorder_parts(self) -> None:
        print_rows(
            ["ID", "Запчастина", "Виробник", "Залишок", "Мін. залишок"],
            self.service.list_reorder_parts(),
        )

    def revenue_report(self) -> None:
        print_rows(["Місяць", "Дохід", "К-сть платежів"], self.service.revenue_report())

    def technician_report(self) -> None:
        print_rows(["ID", "Майстер", "К-сть замовлень", "Сума"], self.service.technician_report())

    def close_order(self) -> None:
        self.service.close_order(int(input("ID замовлення для закриття: ").strip()))
        print("Замовлення закрито.")

    def generate_visuals(self) -> None:
        for path in self.artifact_generator.generate_all():
            print(path)

    def run(self) -> None:
        menu = {
            "1": ("Переглянути замовлення", self.show_orders),
            "2": ("Пошук замовлень", self.search_orders),
            "3": ("Переглянути клієнтів", self.show_clients),
            "4": ("Додати клієнта", self.add_client),
            "5": ("Додати пристрій", self.add_device),
            "6": ("Створити замовлення", self.create_order),
            "7": ("Додати діагностику", self.add_diagnostic),
            "8": ("Додати послугу до замовлення", self.add_service_to_order),
            "9": ("Додати запчастину до замовлення", self.add_part_to_order),
            "10": ("Додати платіж", self.add_payment),
            "11": ("Деталі замовлення", self.show_order_details),
            "12": ("Запчастини для дозамовлення", self.show_reorder_parts),
            "13": ("Звіт по доходу", self.revenue_report),
            "14": ("Завантаженість майстрів", self.technician_report),
            "15": ("Закрити замовлення", self.close_order),
            "16": ("Згенерувати графіки й діаграми", self.generate_visuals),
        }

        while True:
            print("\nСистема сервісного центру")
            for key, (label, _) in menu.items():
                print(f"{key}. {label}")
            print("0. Вихід")
            choice = input("Оберіть дію: ").strip()
            if choice == "0":
                break
            action = menu.get(choice)
            if not action:
                print("Невірний пункт меню.")
                continue
            try:
                action[1]()
            except mysql.connector.Error as exc:
                print(f"Помилка MySQL: {exc}")
            except ValueError:
                print("Помилка введення даних.")


def main() -> None:
    ServiceCenterCLI().run()
