from decimal import Decimal
from unittest.mock import Mock

from service_center.services import ServiceCenterService


def test_search_orders_passes_filters_to_database() -> None:
    database = Mock()
    database.fetch_all.return_value = []

    service = ServiceCenterService(database=database)
    service.search_orders("+380671234501", "У ремонті")

    database.fetch_all.assert_called_once()
    _query, params = database.fetch_all.call_args.args
    assert params == ("+380671234501", "+380671234501", "У ремонті", "У ремонті")


def test_add_client_inserts_expected_values() -> None:
    database = Mock()
    service = ServiceCenterService(database=database)

    service.add_client("Сорока", "Володимир", "+380671112233", "volodymyr@example.com")

    database.execute.assert_called_once()
    _query, params = database.execute.call_args.args
    assert params == ("Сорока", "Володимир", "+380671112233", "volodymyr@example.com")


def test_register_payment_calls_procedure() -> None:
    database = Mock()
    service = ServiceCenterService(database=database)

    service.register_payment(4, Decimal("500.00"), "card")

    database.call_procedure.assert_called_once_with(
        "register_payment",
        [4, Decimal("500.00"), "card"],
    )


def test_dashboard_metrics_maps_database_row() -> None:
    database = Mock()
    database.fetch_all.return_value = [(5, 5, 5, 2, Decimal("10650.00"))]

    service = ServiceCenterService(database=database)
    metrics = service.dashboard_metrics()

    assert metrics == {
        "clients_count": 5,
        "devices_count": 5,
        "orders_count": 5,
        "payments_count": 2,
        "revenue_total": 10650.0,
    }
