from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from typing import Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
import mysql.connector

from .database import Database


plt.rcParams["font.family"] = "DejaVu Sans"


class ArtifactGenerator:
    def __init__(self, database: Optional[Database] = None, artifacts_dir: Optional[Path] = None) -> None:
        self.database = database
        self.artifacts_dir = artifacts_dir or Path("artifacts")
        self.diagrams_dir = Path("diagrams")
        self.tools_dir = Path("tools")
        self.palette = {
            "ink": "#14324A",
            "blue": "#2E648E",
            "blue_soft": "#D9E7F1",
            "green": "#3F7E4C",
            "gold": "#C78A2C",
            "rose": "#B55D4C",
            "sand": "#F4E9D8",
            "mint": "#DDEBDB",
            "paper": "#FFFDF8",
            "line": "#B8C7D3",
            "grid": "#D6E0E8",
        }

    def ensure_dir(self) -> None:
        self.artifacts_dir.mkdir(exist_ok=True)

    def fetch_rows(self, query: str) -> list[tuple]:
        if self.database is None:
            self.database = Database()
        return self.database.fetch_all(query)

    @staticmethod
    def fallback_revenue() -> list[tuple]:
        return [("2026-03", 10650.00)]

    @staticmethod
    def fallback_statuses() -> list[tuple]:
        return [
            ("У ремонті", 2),
            ("На діагностиці", 1),
            ("Очікує запчастини", 1),
            ("Готове до видачі", 1),
        ]

    @staticmethod
    def fallback_technicians() -> list[tuple]:
        return [
            ("Петренко Андрій", 3),
            ("Лисенко Наталія", 1),
            ("Савчук Роман", 1),
        ]

    def revenue_data(self) -> list[tuple]:
        try:
            rows = self.fetch_rows(
                """
                SELECT payment_month, revenue
                FROM vw_revenue_by_month
                ORDER BY payment_month
                """
            )
            return rows or self.fallback_revenue()
        except mysql.connector.Error:
            return self.fallback_revenue()

    def status_data(self) -> list[tuple]:
        try:
            rows = self.fetch_rows(
                """
                SELECT os.status_name, COUNT(*)
                FROM repair_order ro
                JOIN order_status os ON os.status_id = ro.status_id
                GROUP BY os.status_name
                ORDER BY COUNT(*) DESC, os.status_name
                """
            )
            return rows or self.fallback_statuses()
        except mysql.connector.Error:
            return self.fallback_statuses()

    def technician_data(self) -> list[tuple]:
        try:
            rows = self.fetch_rows(
                """
                SELECT technician_name, orders_count
                FROM vw_technician_workload
                ORDER BY orders_count DESC, technician_name
                """
            )
            return rows or self.fallback_technicians()
        except mysql.connector.Error:
            return self.fallback_technicians()

    def _base_figure(self, width: float, height: float):
        fig, axis = plt.subplots(figsize=(width, height), facecolor=self.palette["paper"])
        axis.set_facecolor(self.palette["paper"])
        return fig, axis

    def _save_figure(self, fig, filename: str) -> str:
        self.ensure_dir()
        out = self.artifacts_dir / filename
        fig.tight_layout(pad=1.1)
        fig.savefig(out, dpi=240, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        return str(out)

    def _resolve_java(self) -> str:
        java_path = shutil.which("java")
        if java_path:
            return java_path

        search_roots = [
            Path(r"C:\Program Files\Microsoft"),
            Path(r"C:\Program Files\Java"),
            Path(r"C:\Program Files\JetBrains"),
        ]
        for root in search_roots:
            if not root.exists():
                continue
            matches = sorted(root.glob("**/java.exe"))
            if matches:
                return str(matches[0])
        raise RuntimeError("Java runtime not found. Install OpenJDK 17 or add java.exe to PATH.")

    def _render_plantuml(self, source_name: str, output_name: str) -> str:
        source = self.diagrams_dir / source_name
        if not source.exists():
            raise FileNotFoundError(f"PlantUML source not found: {source}")
        self.ensure_dir()
        target = self.artifacts_dir / output_name

        try:
            plantuml_path = shutil.which("plantuml")
            if plantuml_path:
                command = [plantuml_path, "-tpng", "-o", str(self.artifacts_dir.resolve()), str(source.resolve())]
            else:
                jar_path = self.tools_dir / "plantuml.jar"
                if not jar_path.exists():
                    raise RuntimeError("PlantUML not found. Install plantuml or place plantuml.jar in tools/plantuml.jar.")
                command = [self._resolve_java(), "-jar", str(jar_path.resolve()), "-tpng", "-o", str(self.artifacts_dir.resolve()), str(source.resolve())]

            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError):
            if target.exists():
                return str(target)
            raise

        generated = self.artifacts_dir / source.with_suffix(".png").name
        if generated.exists() and generated != target:
            generated.replace(target)
        output = target if target.exists() else generated
        if not output.exists():
            raise RuntimeError(f"PlantUML did not generate expected output for {source_name}.")
        return str(output)

    @staticmethod
    def _money_formatter(value: float, _position: int) -> str:
        return f"{value:,.0f} грн".replace(",", " ")

    def _style_axis(self, axis) -> None:
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_color(self.palette["ink"])
        axis.spines["bottom"].set_color(self.palette["ink"])
        axis.tick_params(colors=self.palette["ink"], labelsize=11)
        axis.grid(color=self.palette["grid"], linewidth=0.8, alpha=0.7)
        axis.set_axisbelow(True)

    def generate_revenue_chart(self) -> str:
        rows = self.revenue_data()
        months = [str(row[0]) for row in rows]
        values = [float(row[1]) for row in rows]

        fig, axis = self._base_figure(10.2, 5.8)
        x = list(range(len(months)))
        axis.fill_between(x, values, color=self.palette["blue_soft"], alpha=0.95)
        axis.plot(x, values, color=self.palette["blue"], linewidth=2.8, marker="o", markersize=8)
        axis.set_xticks(x, months)
        axis.set_title("Динаміка доходу сервісного центру", fontsize=18, fontweight="bold", color=self.palette["ink"], pad=16)
        axis.set_xlabel("Місяць", fontsize=12, color=self.palette["ink"])
        axis.set_ylabel("Сума оплат", fontsize=12, color=self.palette["ink"])
        axis.yaxis.set_major_formatter(FuncFormatter(self._money_formatter))
        self._style_axis(axis)

        top = max(values) if values else 1
        axis.set_ylim(0, top * 1.25)
        for x_value, value in zip(x, values):
            axis.text(
                x_value,
                value + top * 0.05,
                f"{value:,.0f}".replace(",", " ") + " грн",
                ha="center",
                va="bottom",
                fontsize=10.5,
                fontweight="bold",
                color=self.palette["ink"],
            )

        return self._save_figure(fig, "revenue_chart.png")

    def generate_status_chart(self) -> str:
        rows = self.status_data()
        labels = [str(row[0]) for row in rows]
        values = [int(row[1]) for row in rows]
        total = sum(values) or 1

        fig, axis = self._base_figure(10.4, 5.8)
        colors = [self.palette["blue"], self.palette["gold"], self.palette["green"], self.palette["rose"]]
        bars = axis.barh(labels, values, color=colors[: len(values)], edgecolor=self.palette["ink"], linewidth=0.9, height=0.58)
        axis.invert_yaxis()
        axis.set_title("Структура замовлень за статусами", fontsize=18, fontweight="bold", color=self.palette["ink"], pad=16)
        axis.set_xlabel("Кількість замовлень", fontsize=12, color=self.palette["ink"])
        axis.xaxis.set_major_locator(MaxNLocator(integer=True))
        self._style_axis(axis)

        for bar, value in zip(bars, values):
            percent = value / total * 100
            axis.text(
                value + 0.08,
                bar.get_y() + bar.get_height() / 2,
                f"{value} ({percent:.0f}%)",
                va="center",
                ha="left",
                fontsize=10.5,
                fontweight="bold",
                color=self.palette["ink"],
            )

        axis.set_xlim(0, max(values) + 1.8 if values else 1)
        return self._save_figure(fig, "status_chart.png")

    def generate_technician_chart(self) -> str:
        rows = self.technician_data()
        names = [str(row[0]) for row in rows]
        values = [int(row[1]) for row in rows]

        fig, axis = self._base_figure(10.2, 5.8)
        bars = axis.barh(names, values, color=self.palette["green"], edgecolor=self.palette["ink"], linewidth=0.9, height=0.55)
        axis.invert_yaxis()
        axis.set_title("Навантаження майстрів", fontsize=18, fontweight="bold", color=self.palette["ink"], pad=16)
        axis.set_xlabel("Кількість активних замовлень", fontsize=12, color=self.palette["ink"])
        axis.xaxis.set_major_locator(MaxNLocator(integer=True))
        self._style_axis(axis)

        for bar, value in zip(bars, values):
            axis.text(
                value + 0.08,
                bar.get_y() + bar.get_height() / 2,
                str(value),
                va="center",
                ha="left",
                fontsize=10.5,
                fontweight="bold",
                color=self.palette["ink"],
            )

        axis.set_xlim(0, max(values) + 1.5 if values else 1)
        return self._save_figure(fig, "technician_chart.png")

    def generate_er_diagram(self) -> str:
        return self._render_plantuml("er_diagram.puml", "er_diagram.png")

    def generate_schema_diagram(self) -> str:
        return self._render_plantuml("logical_schema.puml", "schema_diagram.png")

    def generate_all(self) -> list[str]:
        generators = [
            self.generate_er_diagram,
            self.generate_schema_diagram,
            self.generate_revenue_chart,
            self.generate_status_chart,
            self.generate_technician_chart,
        ]
        generated: list[str] = []
        for generate in generators:
            try:
                generated.append(generate())
            except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError):
                continue
        return generated


def generate_all_artifacts() -> list[str]:
    return ArtifactGenerator().generate_all()
