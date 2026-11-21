import sqlite3

import pytest

from src.checks import run_all_checks
from src.config import STATUS_IN_PROGRESS, STATUS_RESOLVED, STATUS_TODO
from src.tracking import init_log, sync_log, update_status
from tests.conftest import make_df


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    init_log(connection)
    return connection


def rows(conn):
    return conn.execute(
        "SELECT rule, status, owner_team, detected_date, resolved_date FROM exception_log"
    ).fetchall()


def test_new_anomalies_are_logged_as_todo_with_owner(conn, as_of):
    anomalies = run_all_checks(make_df({"amount": None}, {"currency": "XXX"}), as_of)
    assert sync_log(conn, anomalies, as_of)["new"] == 2
    assert set(rows(conn)) == {
        ("MISSING_AMOUNT", STATUS_TODO, "Middle Office", "2026-11-20", None),
        ("INVALID_CURRENCY", STATUS_TODO, "Reference Data", "2026-11-20", None),
    }


def test_rerun_does_not_duplicate_entries(conn, as_of):
    anomalies = run_all_checks(make_df({"amount": None}), as_of)
    sync_log(conn, anomalies, as_of)
    assert sync_log(conn, anomalies, as_of) == {"new": 0, "reopened": 0, "auto_resolved": 0}
    assert len(rows(conn)) == 1


def test_fixed_anomaly_is_auto_resolved(conn, as_of):
    sync_log(conn, run_all_checks(make_df({"amount": None}), as_of), as_of)
    fixed = run_all_checks(make_df({"amount": 150000.0}), as_of)
    assert sync_log(conn, fixed, as_of)["auto_resolved"] == 1
    assert rows(conn)[0][1:] == (STATUS_RESOLVED, "Middle Office", "2026-11-20", "2026-11-20")


def test_resolved_anomaly_that_comes_back_is_reopened(conn, as_of):
    broken = run_all_checks(make_df({"amount": None}), as_of)
    sync_log(conn, broken, as_of)
    sync_log(conn, run_all_checks(make_df({"amount": 1.0}), as_of), as_of)
    assert sync_log(conn, broken, as_of)["reopened"] == 1
    assert rows(conn)[0][1] == STATUS_TODO


def test_manual_status_update(conn, as_of):
    sync_log(conn, run_all_checks(make_df({"amount": None}), as_of), as_of)
    update_status(conn, 1, STATUS_IN_PROGRESS, as_of, "Pris en charge")
    assert rows(conn)[0][1] == STATUS_IN_PROGRESS
    update_status(conn, 1, STATUS_RESOLVED, as_of)
    assert rows(conn)[0][4] == "2026-11-20"


def test_update_status_rejects_bad_input(conn, as_of):
    with pytest.raises(ValueError):
        update_status(conn, 1, "Inconnu", as_of)
    with pytest.raises(ValueError):
        update_status(conn, 999, STATUS_RESOLVED, as_of)
