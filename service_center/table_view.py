from __future__ import annotations

from typing import Iterable


def print_rows(headers: list[str], rows: Iterable[tuple]) -> None:
    materialized = list(rows)
    if not materialized:
        print("Дані відсутні.")
        return

    widths = [len(header) for header in headers]
    for row in materialized:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(str(cell)))

    separator = " | "
    header_line = separator.join(header.ljust(widths[index]) for index, header in enumerate(headers))
    divider = "-+-".join("-" * width for width in widths)
    print(header_line)
    print(divider)
    for row in materialized:
        print(separator.join(str(cell).ljust(widths[index]) for index, cell in enumerate(row)))
