from src.checks import (
    check_completeness, check_consistency, check_uniqueness, check_validity, run_all_checks,
)
from tests.conftest import make_df, rules_found


def test_clean_data_has_no_anomaly(as_of):
    assert run_all_checks(make_df({}, {"amount": 99000.0}), as_of).empty


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


# --- Uniqueness ---
def test_duplicate_id_flags_the_extra_copy_only(as_of):
    df = make_df({}, {"transaction_id": "TR1", "amount": 80000.0})  # 2e ligne = même ID que la 1re
    assert rules_found(check_uniqueness(df)) == {(2, "DUPLICATE_ID")}


def test_same_business_data_with_other_id_is_potential_duplicate(as_of):
    df = make_df({}, {})  # TR1 et TR2 : mêmes produit, date, montant, devise, contrepartie
    assert rules_found(check_uniqueness(df)) == {(2, "POTENTIAL_DUPLICATE")}


def test_exact_copy_is_not_counted_twice(as_of):
    df = make_df({}, {"transaction_id": "TR1"})  # copie exacte : doublon d'ID uniquement
    assert rules_found(check_uniqueness(df)) == {(2, "DUPLICATE_ID")}


def test_missing_ids_are_not_duplicates_of_each_other(as_of):
    df = make_df({"transaction_id": None, "amount": 1.0}, {"transaction_id": None, "amount": 2.0})
    assert check_uniqueness(df).empty


# --- Consistency ---
def test_settled_without_settlement_date(as_of):
    df = make_df({"settlement_date": None})
    assert rules_found(check_consistency(df, as_of)) == {(1, "SETTLED_WITHOUT_SETTLEMENT_DATE")}


def test_pending_with_past_settlement_date(as_of):
    df = make_df({"status": "PENDING", "settlement_date": "2026-11-12"})
    assert rules_found(check_consistency(df, as_of)) == {(1, "PENDING_PAST_SETTLEMENT")}


def test_pending_with_future_settlement_date_is_fine(as_of):
    df = make_df({"status": "PENDING", "trade_date": "2026-11-19", "settlement_date": "2026-11-21"})
    assert check_consistency(df, as_of).empty


def test_settlement_before_trade(as_of):
    df = make_df({"trade_date": "2026-11-10", "settlement_date": "2026-11-05"})
    assert rules_found(check_consistency(df, as_of)) == {(1, "SETTLEMENT_BEFORE_TRADE")}


def test_cancelled_without_settlement_date_is_fine(as_of):
    assert check_consistency(make_df({"status": "CANCELLED", "settlement_date": None}), as_of).empty
