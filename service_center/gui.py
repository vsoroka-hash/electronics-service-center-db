from __future__ import annotations

import os
import tkinter as tk
from concurrent.futures import Future, ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional, Union

import mysql.connector

from .services import ServiceCenterService
from .visualization import ArtifactGenerator


class ServiceCenterApp:
    def __init__(
        self,
        service: Optional[ServiceCenterService] = None,
        artifact_generator: Optional[ArtifactGenerator] = None,
    ) -> None:
        self.service = service or ServiceCenterService()
        self.artifact_generator = artifact_generator or ArtifactGenerator()
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="service-center")
        self.root = tk.Tk()
        self.root.title("Service Center DB")
        self.root.geometry("1320x860")
        self.root.minsize(1180, 760)
        self.root.configure(bg="#f4efe7")
        self.root.protocol("WM_DELETE_WINDOW", self._shutdown)

        self.colors = {
            "bg": "#f4efe7",
            "panel": "#fffaf2",
            "panel_alt": "#eef4f7",
            "text": "#16324f",
            "muted": "#5e6f82",
            "accent": "#2f6690",
            "accent_dark": "#1d4d72",
            "line": "#d2d9df",
        }

        self.status_var = tk.StringVar(value="Готово до роботи.")
        self.phone_var = tk.StringVar()
        self.order_status_var = tk.StringVar()
        self.charts_var = tk.StringVar(value="Діаграми ще не згенеровано в цій сесії.")
        self.metric_labels: dict[str, ttk.Label] = {}
        self.active_tasks = 0
        self.loaded_tabs: set[str] = set()

        self._configure_styles()
        self._build_layout()
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.root.after(50, lambda: self.refresh_dashboard(background=True))

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), foreground=self.colors["text"])
        style.configure("Main.TFrame", background=self.colors["bg"])
        style.configure("Panel.TFrame", background=self.colors["panel"], relief="flat")
        style.configure("AltPanel.TFrame", background=self.colors["panel_alt"], relief="flat")
        style.configure("Dashboard.TLabel", background=self.colors["panel"], foreground=self.colors["text"])
        style.configure("Muted.TLabel", background=self.colors["panel"], foreground=self.colors["muted"], font=("Segoe UI", 10))
        style.configure("Section.TLabel", background=self.colors["panel"], foreground=self.colors["text"], font=("Segoe UI Semibold", 12))
        style.configure("HeroTitle.TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Bahnschrift SemiBold", 30))
        style.configure("HeroSub.TLabel", background=self.colors["bg"], foreground=self.colors["muted"], font=("Segoe UI", 11))
        style.configure("CardTitle.TLabel", background=self.colors["panel_alt"], foreground=self.colors["muted"], font=("Segoe UI", 10))
        style.configure("CardValue.TLabel", background=self.colors["panel_alt"], foreground=self.colors["text"], font=("Bahnschrift SemiBold", 22))
        style.configure("Accent.TButton", background=self.colors["accent"], foreground="white", borderwidth=0, padding=(12, 8))
        style.map("Accent.TButton", background=[("active", self.colors["accent_dark"])])
        style.configure("Secondary.TButton", background="#dbe7ee", foreground=self.colors["text"], borderwidth=0, padding=(10, 7))
        style.map("Secondary.TButton", background=[("active", "#c8dae5")])
        style.configure("Treeview", background="white", fieldbackground="white", rowheight=30, bordercolor=self.colors["line"], borderwidth=0)
        style.configure("Treeview.Heading", background="#dbe7ee", foreground=self.colors["text"], font=("Segoe UI Semibold", 10), relief="flat")
        style.map("Treeview.Heading", background=[("active", "#cbdce8")])
        style.configure("TNotebook", background=self.colors["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 10), font=("Segoe UI Semibold", 10), background="#e2eaee", foreground=self.colors["text"])
        style.map("TNotebook.Tab", background=[("selected", self.colors["panel"])])
        style.configure("Status.TLabel", background=self.colors["bg"], foreground=self.colors["muted"], font=("Segoe UI", 10))

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, style="Main.TFrame", padding=18)
        container.pack(fill="both", expand=True)

        hero = ttk.Frame(container, style="Main.TFrame")
        hero.pack(fill="x", pady=(0, 14))
        ttk.Label(hero, text="Service Center Dashboard", style="HeroTitle.TLabel").pack(anchor="w")
        ttk.Label(hero, text="Керування ремонтами, платежами, складом і звітами в одному інтерфейсі.", style="HeroSub.TLabel").pack(anchor="w", pady=(4, 0))

        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill="both", expand=True)

        self.dashboard_tab = ttk.Frame(self.notebook, style="Main.TFrame", padding=6)
        self.orders_tab = ttk.Frame(self.notebook, style="Main.TFrame", padding=6)
        self.catalogs_tab = ttk.Frame(self.notebook, style="Main.TFrame", padding=6)
        self.reports_tab = ttk.Frame(self.notebook, style="Main.TFrame", padding=6)

        self.notebook.add(self.dashboard_tab, text="Огляд")
        self.notebook.add(self.orders_tab, text="Замовлення")
        self.notebook.add(self.catalogs_tab, text="Довідники")
        self.notebook.add(self.reports_tab, text="Звіти")

        self._build_dashboard_tab()
        self._build_orders_tab()
        self._build_catalogs_tab()
        self._build_reports_tab()

        footer = ttk.Frame(container, style="Main.TFrame")
        footer.pack(fill="x", pady=(10, 0))
        ttk.Label(footer, textvariable=self.status_var, style="Status.TLabel").pack(anchor="w")

    def _build_dashboard_tab(self) -> None:
        cards = ttk.Frame(self.dashboard_tab, style="Main.TFrame")
        cards.pack(fill="x", pady=(0, 14))
        for title, key in [
            ("Клієнти", "clients_count"),
            ("Пристрої", "devices_count"),
            ("Замовлення", "orders_count"),
            ("Платежі", "payments_count"),
            ("Загальний дохід", "revenue_total"),
        ]:
            self._card(cards, title, key)

        content = ttk.Frame(self.dashboard_tab, style="Main.TFrame")
        content.pack(fill="both", expand=True)

        left = ttk.Frame(content, style="Panel.TFrame", padding=16)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ttk.Label(left, text="Останні замовлення", style="Section.TLabel").pack(anchor="w", pady=(0, 10))
        self.dashboard_orders_tree = self._create_tree(
            left,
            ("id", "client", "device", "status", "tech", "sum"),
            ("ID", "Клієнт", "Пристрій", "Статус", "Майстер", "Сума"),
            (70, 180, 190, 150, 170, 100),
        )

        right = ttk.Frame(content, style="Panel.TFrame", padding=16)
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="Швидкі дії", style="Section.TLabel").pack(anchor="w", pady=(0, 10))
        for text, command, style in [
            ("Новий клієнт", self.open_add_client_dialog, "Accent.TButton"),
            ("Новий пристрій", self.open_add_device_dialog, "Secondary.TButton"),
            ("Нове замовлення", self.open_create_order_dialog, "Secondary.TButton"),
            ("Платіж", self.open_add_payment_dialog, "Secondary.TButton"),
            ("Перегенерувати діаграми", self.generate_visuals, "Secondary.TButton"),
            ("Відкрити artifacts", self.open_artifacts_folder, "Secondary.TButton"),
        ]:
            ttk.Button(right, text=text, style=style, command=command).pack(fill="x", pady=4)
        ttk.Label(right, textvariable=self.charts_var, style="Muted.TLabel", wraplength=320, justify="left").pack(anchor="w", pady=(16, 0))

    def _build_orders_tab(self) -> None:
        search_panel = ttk.Frame(self.orders_tab, style="Panel.TFrame", padding=14)
        search_panel.pack(fill="x", pady=(0, 12))
        ttk.Label(search_panel, text="Пошук замовлень", style="Section.TLabel").grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 10))
        ttk.Label(search_panel, text="Телефон клієнта", style="Dashboard.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Entry(search_panel, textvariable=self.phone_var, width=24).grid(row=1, column=1, padx=(8, 16), sticky="w")
        ttk.Label(search_panel, text="Статус", style="Dashboard.TLabel").grid(row=1, column=2, sticky="w")
        values = ["", "Нове", "На діагностиці", "Очікує запчастини", "У ремонті", "Готове до видачі", "Закрите"]
        ttk.Combobox(search_panel, textvariable=self.order_status_var, width=24, values=values).grid(row=1, column=3, padx=(8, 16), sticky="w")
        ttk.Button(search_panel, text="Знайти", style="Accent.TButton", command=self.refresh_orders).grid(row=1, column=4, padx=(0, 8))
        ttk.Button(search_panel, text="Скинути", style="Secondary.TButton", command=self.reset_order_filters).grid(row=1, column=5)

        body = ttk.Frame(self.orders_tab, style="Main.TFrame")
        body.pack(fill="both", expand=True)

        table_panel = ttk.Frame(body, style="Panel.TFrame", padding=14)
        table_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ttk.Label(table_panel, text="Список замовлень", style="Section.TLabel").pack(anchor="w", pady=(0, 10))
        self.orders_tree = self._create_tree(
            table_panel,
            ("id", "client", "device", "status", "term", "sum"),
            ("ID", "Клієнт", "Пристрій", "Статус", "Термін", "Сума"),
            (70, 180, 210, 150, 110, 100),
        )

        actions_panel = ttk.Frame(body, style="Panel.TFrame", padding=14)
        actions_panel.pack(side="left", fill="y")
        ttk.Label(actions_panel, text="Операції", style="Section.TLabel").pack(anchor="w", pady=(0, 10))
        for text, command, style in [
            ("Оновити", self.refresh_orders, "Accent.TButton"),
            ("Додати діагностику", self.open_add_diagnostic_dialog, "Secondary.TButton"),
            ("Додати послугу", self.open_add_service_dialog, "Secondary.TButton"),
            ("Додати запчастину", self.open_add_part_dialog, "Secondary.TButton"),
            ("Додати платіж", self.open_add_payment_dialog, "Secondary.TButton"),
            ("Закрити замовлення", self.open_close_order_dialog, "Secondary.TButton"),
        ]:
            ttk.Button(actions_panel, text=text, style=style, command=command).pack(fill="x", pady=4)

    def _build_catalogs_tab(self) -> None:
        notebook = ttk.Notebook(self.catalogs_tab)
        notebook.pack(fill="both", expand=True)

        clients_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=14)
        devices_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=14)
        services_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=14)
        parts_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=14)
        notebook.add(clients_tab, text="Клієнти")
        notebook.add(devices_tab, text="Пристрої")
        notebook.add(services_tab, text="Послуги")
        notebook.add(parts_tab, text="Запчастини")

        ttk.Button(clients_tab, text="Додати клієнта", style="Accent.TButton", command=self.open_add_client_dialog).pack(anchor="w", pady=(0, 10))
        self.clients_tree = self._create_tree(clients_tab, ("id", "last", "first", "phone", "email"), ("ID", "Прізвище", "Ім'я", "Телефон", "Email"), (70, 150, 150, 140, 220))
        ttk.Button(devices_tab, text="Додати пристрій", style="Accent.TButton", command=self.open_add_device_dialog).pack(anchor="w", pady=(0, 10))
        self.devices_tree = self._create_tree(devices_tab, ("id", "client", "type", "brand", "model", "serial"), ("ID", "Клієнт", "Тип", "Бренд", "Модель", "Серійний №"), (70, 180, 120, 120, 150, 170))
        self.services_tree = self._create_tree(services_tab, ("id", "name", "price", "hours", "active"), ("ID", "Послуга", "Базова ціна", "Години", "Активна"), (70, 260, 120, 90, 80))
        self.parts_tree = self._create_tree(parts_tab, ("id", "name", "manufacturer", "price", "stock"), ("ID", "Запчастина", "Виробник", "Ціна", "Залишок"), (70, 280, 180, 110, 90))

    def _build_reports_tab(self) -> None:
        top = ttk.Frame(self.reports_tab, style="Panel.TFrame", padding=14)
        top.pack(fill="x", pady=(0, 12))
        ttk.Label(top, text="Аналітичні таблиці та візуалізація", style="Section.TLabel").pack(anchor="w")
        ttk.Button(top, text="Перегенерувати artifacts", style="Accent.TButton", command=self.generate_visuals).pack(anchor="e", pady=(8, 0))

        body = ttk.Frame(self.reports_tab, style="Main.TFrame")
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body, style="Panel.TFrame", padding=14)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ttk.Label(left, text="Дохід за місяцями", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        self.revenue_tree = self._create_tree(left, ("month", "revenue", "count"), ("Місяць", "Дохід", "Платежі"), (130, 120, 90))
        ttk.Label(left, text="Завантаження майстрів", style="Section.TLabel").pack(anchor="w", pady=(16, 8))
        self.technician_tree = self._create_tree(left, ("id", "name", "orders", "total"), ("ID", "Майстер", "Замовлення", "Сума"), (60, 180, 100, 120))

        right = ttk.Frame(body, style="Panel.TFrame", padding=14)
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="Статуси замовлень", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        self.status_tree = self._create_tree(right, ("status", "count"), ("Статус", "Кількість"), (220, 90))
        ttk.Label(right, text="Стан артефактів", style="Section.TLabel").pack(anchor="w", pady=(18, 8))
        ttk.Label(right, textvariable=self.charts_var, style="Muted.TLabel", wraplength=360, justify="left").pack(anchor="w")

    def _card(self, parent, title: str, key: str) -> None:
        card = ttk.Frame(parent, style="AltPanel.TFrame", padding=18)
        card.pack(side="left", fill="both", expand=True, padx=(0, 12))
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
        label = ttk.Label(card, text="0", style="CardValue.TLabel")
        label.pack(anchor="w", pady=(10, 0))
        self.metric_labels[key] = label

    def _create_tree(self, parent, columns: tuple[str, ...], headings: tuple[str, ...], widths: tuple[int, ...]) -> ttk.Treeview:
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        for column, heading, width in zip(columns, headings, widths):
            tree.heading(column, text=heading)
            tree.column(column, width=width, anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        return tree

    def _set_tree_rows(self, tree: ttk.Treeview, rows: list[tuple]) -> None:
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", "end", values=row)

    def _set_busy(self, busy: bool, message: Optional[str] = None) -> None:
        if busy:
            self.active_tasks += 1
        else:
            self.active_tasks = max(0, self.active_tasks - 1)
        self.root.configure(cursor="watch" if self.active_tasks else "")
        if message:
            self.status_var.set(message)
        elif not self.active_tasks:
            self.status_var.set("Готово до роботи.")

    def _run_task(
        self,
        work,
        on_success,
        *,
        on_error=None,
        busy_message: str = "Виконується операція...",
        success_message: Optional[str] = None,
    ) -> None:
        self._set_busy(True, busy_message)
        future = self.executor.submit(work)
        self._poll_future(future, on_success, on_error=on_error, success_message=success_message)

    def _poll_future(self, future: Future, on_success, *, on_error=None, success_message: Optional[str] = None) -> None:
        if not future.done():
            self.root.after(30, lambda: self._poll_future(future, on_success, on_error=on_error, success_message=success_message))
            return
        self._set_busy(False)
        try:
            result = future.result()
        except Exception as exc:  # noqa: BLE001
            if on_error:
                on_error(exc)
            else:
                self._handle_exception(exc)
            return
        if success_message:
            self.status_var.set(success_message)
        on_success(result)

    def _handle_exception(self, exc: Exception) -> None:
        if isinstance(exc, mysql.connector.Error):
            messagebox.showerror("MySQL", str(exc), parent=self.root)
        else:
            messagebox.showerror("Помилка", str(exc), parent=self.root)

    def format_money(self, value: Union[int, float, str]) -> str:
        return f"{float(value):,.2f} грн".replace(",", " ")

    def _option_pairs(self, rows: list[tuple], label_builder) -> list[str]:
        return [f"{row[0]} | {label_builder(row)}" for row in rows]

    @staticmethod
    def _extract_id(value: str) -> int:
        return int(str(value).split("|", 1)[0].strip())

    def _on_tab_changed(self, _event) -> None:
        current_text = self.notebook.tab(self.notebook.select(), "text")
        if current_text == "Замовлення" and "orders" not in self.loaded_tabs:
            self.refresh_orders(background=True)
        elif current_text == "Довідники" and "catalogs" not in self.loaded_tabs:
            self.refresh_catalogs(background=True)
        elif current_text == "Звіти" and "reports" not in self.loaded_tabs:
            self.refresh_reports(background=True)

    def refresh_dashboard(self, *, background: bool = False) -> None:
        def work():
            return self.service.dashboard_metrics(), self.service.list_orders()[:8]

        def on_success(result) -> None:
            metrics, dashboard_rows = result
            for key, label in self.metric_labels.items():
                value = metrics[key]
                label.configure(text=self.format_money(value) if key == "revenue_total" else str(value))
            rows = [(row[0], row[1], row[2], row[3], row[4], self.format_money(row[5])) for row in dashboard_rows]
            self._set_tree_rows(self.dashboard_orders_tree, rows)
            self.loaded_tabs.add("dashboard")

        if background:
            self._run_task(work, on_success, busy_message="Оновлення огляду...")
        else:
            on_success(work())

    def refresh_orders(self, *, background: bool = True) -> None:
        phone = self.phone_var.get().strip()
        status = self.order_status_var.get().strip()

        def work():
            return self.service.search_orders(phone, status)

        def on_success(rows) -> None:
            formatted = [(row[0], row[1], row[2], row[3], row[4], self.format_money(row[5])) for row in rows]
            self._set_tree_rows(self.orders_tree, formatted)
            self.loaded_tabs.add("orders")

        if background:
            self._run_task(work, on_success, busy_message="Завантаження замовлень...")
        else:
            on_success(work())

    def refresh_catalogs(self, *, background: bool = True) -> None:
        def work():
            return {
                "clients": self.service.list_clients(),
                "devices": self.service.list_devices(),
                "services": self.service.list_services(),
                "parts": self.service.list_parts(),
            }

        def on_success(data) -> None:
            self._set_tree_rows(self.clients_tree, data["clients"])
            self._set_tree_rows(self.devices_tree, data["devices"])
            service_rows = [(row[0], row[1], self.format_money(row[2]), row[3], "Так" if row[4] else "Ні") for row in data["services"]]
            part_rows = [(row[0], row[1], row[2], self.format_money(row[3]), row[4]) for row in data["parts"]]
            self._set_tree_rows(self.services_tree, service_rows)
            self._set_tree_rows(self.parts_tree, part_rows)
            self.loaded_tabs.add("catalogs")

        if background:
            self._run_task(work, on_success, busy_message="Завантаження довідників...")
        else:
            on_success(work())

    def refresh_reports(self, *, background: bool = True) -> None:
        def work():
            return {
                "revenue": self.service.revenue_report(),
                "technicians": self.service.technician_report(),
                "statuses": self.service.status_report(),
            }

        def on_success(data) -> None:
            revenue_rows = [(row[0], self.format_money(row[1]), row[2]) for row in data["revenue"]]
            technician_rows = [(row[0], row[1], row[2], self.format_money(row[3])) for row in data["technicians"]]
            self._set_tree_rows(self.revenue_tree, revenue_rows)
            self._set_tree_rows(self.technician_tree, technician_rows)
            self._set_tree_rows(self.status_tree, data["statuses"])
            self.loaded_tabs.add("reports")

        if background:
            self._run_task(work, on_success, busy_message="Завантаження звітів...")
        else:
            on_success(work())

    def refresh_after_mutation(self) -> None:
        self.refresh_dashboard(background=True)
        current_text = self.notebook.tab(self.notebook.select(), "text")
        if current_text == "Замовлення":
            self.refresh_orders(background=True)
        elif current_text == "Довідники":
            self.refresh_catalogs(background=True)
        elif current_text == "Звіти":
            self.refresh_reports(background=True)

    def reset_order_filters(self) -> None:
        self.phone_var.set("")
        self.order_status_var.set("")
        self.refresh_orders(background=True)

    def _open_form(self, title: str, fields: list[dict], on_submit, *, success_message: str) -> None:
        window = tk.Toplevel(self.root)
        window.title(title)
        window.configure(bg=self.colors["panel"])
        window.transient(self.root)
        window.grab_set()
        window.resizable(False, False)

        container = ttk.Frame(window, style="Panel.TFrame", padding=18)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text=title, style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        variables: dict[str, tk.Variable] = {}
        for row_index, field in enumerate(fields, start=1):
            ttk.Label(container, text=field["label"], style="Dashboard.TLabel").grid(row=row_index, column=0, sticky="w", pady=6, padx=(0, 12))
            if field.get("kind") == "combobox":
                var = tk.StringVar(value=str(field.get("value", "")))
                control = ttk.Combobox(container, textvariable=var, values=field.get("values", []), width=30, state="readonly")
            elif field.get("kind") == "boolean":
                var = tk.BooleanVar(value=bool(field.get("value", False)))
                control = ttk.Checkbutton(container, variable=var)
            else:
                var = tk.StringVar(value=str(field.get("value", "")))
                control = ttk.Entry(container, textvariable=var, width=34)
            variables[field["name"]] = var
            control.grid(row=row_index, column=1, sticky="ew", pady=6)

        buttons = ttk.Frame(container, style="Panel.TFrame")
        buttons.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="e", pady=(14, 0))

        def submit() -> None:
            payload = {name: variable.get() for name, variable in variables.items()}

            def work():
                on_submit(payload)

            def done(_result) -> None:
                window.destroy()
                self.refresh_after_mutation()

            self._run_task(
                work,
                done,
                on_error=lambda exc: self._handle_exception(exc),
                busy_message=f"{title}...",
                success_message=success_message,
            )

        ttk.Button(buttons, text="Скасувати", style="Secondary.TButton", command=window.destroy).pack(side="right")
        ttk.Button(buttons, text="Зберегти", style="Accent.TButton", command=submit).pack(side="right", padx=(0, 8))
        container.columnconfigure(1, weight=1)

    def open_add_client_dialog(self) -> None:
        self._open_form(
            "Новий клієнт",
            [
                {"name": "last_name", "label": "Прізвище"},
                {"name": "first_name", "label": "Ім'я"},
                {"name": "phone", "label": "Телефон"},
                {"name": "email", "label": "Email"},
            ],
            lambda payload: self.service.add_client(
                payload["last_name"].strip(),
                payload["first_name"].strip(),
                payload["phone"].strip(),
                payload["email"].strip() or None,
            ),
            success_message="Клієнта збережено.",
        )

    def open_add_device_dialog(self) -> None:
        clients = self._option_pairs(self.service.list_clients(), lambda row: f"{row[1]} {row[2]} • {row[3]}")
        device_types = self._option_pairs(self.service.list_device_types(), lambda row: row[1])
        self._open_form(
            "Новий пристрій",
            [
                {"name": "client_id", "label": "Клієнт", "kind": "combobox", "values": clients},
                {"name": "device_type_id", "label": "Тип пристрою", "kind": "combobox", "values": device_types},
                {"name": "brand", "label": "Бренд"},
                {"name": "model", "label": "Модель"},
                {"name": "serial_number", "label": "Серійний номер"},
                {"name": "purchase_year", "label": "Рік придбання"},
            ],
            lambda payload: self.service.add_device(
                self._extract_id(payload["client_id"]),
                self._extract_id(payload["device_type_id"]),
                payload["brand"].strip(),
                payload["model"].strip(),
                payload["serial_number"].strip(),
                int(payload["purchase_year"]) if payload["purchase_year"].strip() else None,
            ),
            success_message="Пристрій збережено.",
        )

    def open_create_order_dialog(self) -> None:
        devices = self._option_pairs(self.service.list_devices(), lambda row: f"{row[3]} {row[4]} • {row[1]}")
        technicians = self._option_pairs(self.service.list_technicians(), lambda row: f"{row[1]} • {row[2]}")
        self._open_form(
            "Нове замовлення",
            [
                {"name": "device_id", "label": "Пристрій", "kind": "combobox", "values": devices},
                {"name": "technician_id", "label": "Майстер", "kind": "combobox", "values": technicians},
                {"name": "issue_description", "label": "Опис несправності"},
                {"name": "planned_finish", "label": "Планова дата (YYYY-MM-DD)"},
            ],
            lambda payload: self.service.create_order(
                self._extract_id(payload["device_id"]),
                self._extract_id(payload["technician_id"]),
                payload["issue_description"].strip(),
                payload["planned_finish"].strip(),
            ),
            success_message="Замовлення створено.",
        )

    def open_add_diagnostic_dialog(self) -> None:
        orders = self._option_pairs(self.service.list_orders(), lambda row: f"{row[1]} • {row[2]}")
        self._open_form(
            "Діагностика",
            [
                {"name": "order_id", "label": "Замовлення", "kind": "combobox", "values": orders},
                {"name": "diagnostic_result", "label": "Результат"},
                {"name": "estimated_cost", "label": "Орієнтовна вартість"},
                {"name": "urgent_flag", "label": "Термінове", "kind": "boolean"},
            ],
            lambda payload: self.service.add_diagnostic(
                self._extract_id(payload["order_id"]),
                payload["diagnostic_result"].strip(),
                Decimal(payload["estimated_cost"]),
                bool(payload["urgent_flag"]),
            ),
            success_message="Діагностику додано.",
        )

    def open_add_service_dialog(self) -> None:
        orders = self._option_pairs(self.service.list_orders(), lambda row: f"{row[1]} • {row[2]}")
        services = self._option_pairs(self.service.list_services(), lambda row: f"{row[1]} • {self.format_money(row[2])}")
        self._open_form(
            "Послуга до замовлення",
            [
                {"name": "order_id", "label": "Замовлення", "kind": "combobox", "values": orders},
                {"name": "service_id", "label": "Послуга", "kind": "combobox", "values": services},
                {"name": "quantity", "label": "Кількість", "value": "1"},
                {"name": "agreed_price", "label": "Узгоджена ціна"},
            ],
            lambda payload: self.service.add_service_to_order(
                self._extract_id(payload["order_id"]),
                self._extract_id(payload["service_id"]),
                int(payload["quantity"]),
                Decimal(payload["agreed_price"]),
            ),
            success_message="Послугу додано.",
        )

    def open_add_part_dialog(self) -> None:
        orders = self._option_pairs(self.service.list_orders(), lambda row: f"{row[1]} • {row[2]}")
        parts = self._option_pairs(self.service.list_parts(), lambda row: f"{row[1]} • залишок {row[4]}")
        self._open_form(
            "Запчастина до замовлення",
            [
                {"name": "order_id", "label": "Замовлення", "kind": "combobox", "values": orders},
                {"name": "part_id", "label": "Запчастина", "kind": "combobox", "values": parts},
                {"name": "quantity", "label": "Кількість", "value": "1"},
                {"name": "unit_price", "label": "Ціна одиниці"},
            ],
            lambda payload: self.service.add_part_to_order(
                self._extract_id(payload["order_id"]),
                self._extract_id(payload["part_id"]),
                int(payload["quantity"]),
                Decimal(payload["unit_price"]),
            ),
            success_message="Запчастину додано.",
        )

    def open_add_payment_dialog(self) -> None:
        orders = self._option_pairs(self.service.list_orders(), lambda row: f"{row[1]} • {row[2]}")
        self._open_form(
            "Реєстрація платежу",
            [
                {"name": "order_id", "label": "Замовлення", "kind": "combobox", "values": orders},
                {"name": "amount", "label": "Сума"},
                {"name": "method", "label": "Метод", "kind": "combobox", "values": ["cash", "card", "transfer"], "value": "card"},
            ],
            lambda payload: self.service.register_payment(
                self._extract_id(payload["order_id"]),
                Decimal(payload["amount"]),
                payload["method"],
            ),
            success_message="Платіж зареєстровано.",
        )

    def open_close_order_dialog(self) -> None:
        orders = self._option_pairs(self.service.list_orders(), lambda row: f"{row[1]} • {row[2]}")
        self._open_form(
            "Закриття замовлення",
            [{"name": "order_id", "label": "Замовлення", "kind": "combobox", "values": orders}],
            lambda payload: self.service.close_order(self._extract_id(payload["order_id"])),
            success_message="Замовлення закрито.",
        )

    def generate_visuals(self) -> None:
        def work():
            return self.artifact_generator.generate_all()

        def on_success(paths) -> None:
            names = ", ".join(Path(path).name for path in paths)
            self.charts_var.set(f"Оновлено: {names}")
            self.refresh_reports(background=True)

        self._run_task(work, on_success, busy_message="Генерація діаграм...", success_message="Артефакти оновлено.")

    def open_artifacts_folder(self) -> None:
        os.startfile(str(self.artifact_generator.artifacts_dir.resolve()))

    def _shutdown(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    ServiceCenterApp().run()
