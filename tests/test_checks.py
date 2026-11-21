from src.checks import check_completeness, check_validity, run_all_checks
from tests.conftest import make_df, rules_found


def test_clean_data_has_no_anomaly(as_of):
    assert run_all_checks(make_df({}, {}), as_of).empty


# --- Completeness ---
def test_missing_amount_is_incomplete(as_of):
    df = make_df({"amount": None})
    assert rules_found(check_completeness(df)) == {(1, "MISSING_AMOUNT")}


def test_blank_and_null_fields_are_missing(as_of):
    df = make_df({"currency": "  "}, {"transaction_id": None})
    assert rules_found(check_completeness(df)) == {(1, "MISSING_CURRENCY"), (2, "MISSING_TRANSACTION_ID")}


# --- Validity ---
def test_invalid_currency(as_of):
    assert rules_found(check_validity(make_df({"currency": "XXX"}), as_of)) == {(1, "INVALID_CURRENCY")}


def test_negative_amount_is_invalid(as_of):
    assert rules_found(check_validity(make_df({"amount": -50000}), as_of)) == {(1, "INVALID_AMOUNT")}


def test_invalid_status(as_of):
    assert rules_found(check_validity(make_df({"status": "UNKNOWN"}), as_of)) == {(1, "INVALID_STATUS")}


def test_invalid_dates(as_of):
    df = make_df({"trade_date": "2026-13-45"}, {"trade_date": "20/11/2026"})
    assert rules_found(check_validity(df, as_of)) == {(1, "INVALID_TRADE_DATE"), (2, "INVALID_TRADE_DATE")}


def test_future_trade_date(as_of):
    df = make_df({"trade_date": "2026-12-25", "settlement_date": "2026-12-27", "status": "PENDING"})
    assert rules_found(check_validity(df, as_of)) == {(1, "FUTURE_TRADE_DATE")}


def test_missing_value_is_not_reported_as_invalid(as_of):
    """Un champ vide relève de Completeness, pas de Validity (évite le double comptage)."""
    df = make_df({"currency": None, "amount": None})
    assert check_validity(df, as_of).empty
