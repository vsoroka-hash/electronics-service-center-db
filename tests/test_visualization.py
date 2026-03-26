from pathlib import Path
from unittest.mock import Mock

import mysql.connector

from service_center.visualization import ArtifactGenerator


def test_revenue_data_uses_database_rows_when_available(tmp_path: Path) -> None:
    database = Mock()
    database.fetch_all.return_value = [("2026-03", 10650.0)]
    generator = ArtifactGenerator(database=database, artifacts_dir=tmp_path)

    assert generator.revenue_data() == [("2026-03", 10650.0)]


def test_status_data_falls_back_when_database_fails(tmp_path: Path) -> None:
    database = Mock()
    database.fetch_all.side_effect = mysql.connector.Error(msg="db unavailable")
    generator = ArtifactGenerator(database=database, artifacts_dir=tmp_path)

    assert generator.status_data() == generator.fallback_statuses()


def test_generate_revenue_chart_creates_png(tmp_path: Path) -> None:
    database = Mock()
    database.fetch_all.return_value = [("2026-03", 10650.0)]
    generator = ArtifactGenerator(database=database, artifacts_dir=tmp_path)

    output = Path(generator.generate_revenue_chart())

    assert output.exists()
    assert output.suffix == ".png"


def test_generate_all_skips_unavailable_diagrams(tmp_path: Path) -> None:
    database = Mock()
    database.fetch_all.side_effect = [
        [("2026-03", 10650.0)],
        [("У ремонті", 2)],
        [("Петренко Андрій", 3)],
    ]
    generator = ArtifactGenerator(database=database, artifacts_dir=tmp_path)
    generator.generate_er_diagram = Mock(side_effect=RuntimeError("no java"))
    generator.generate_schema_diagram = Mock(side_effect=RuntimeError("no java"))

    outputs = generator.generate_all()

    assert len(outputs) == 3
    assert all(Path(output).exists() for output in outputs)
