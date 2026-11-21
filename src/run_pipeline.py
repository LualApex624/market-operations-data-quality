"""Pipeline complet : extraction SQL -> contrôles qualité -> journal -> rapport.

Usage :
    python -m src.generate_data     # (une fois) crée la base de démonstration
    python -m src.run_pipeline
"""
import argparse
import sqlite3
from datetime import date

import pandas as pd

from src.checks import run_all_checks
from src.config import AS_OF_DATE, DB_PATH, REPORTS_DIR, SQL_DIR
from src.report import write_reports
from src.tracking import init_log, sync_log


def extract_transactions(conn):
    """Étape 1 : récupération des données via SQL."""
    return pd.read_sql((SQL_DIR / "extract_transactions.sql").read_text(), conn)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--as-of", type=date.fromisoformat, default=AS_OF_DATE,
                        help="date de référence des contrôles (YYYY-MM-DD)")
    as_of = parser.parse_args().as_of

    if not DB_PATH.exists():
        raise SystemExit("Base introuvable. Lance d'abord : python -m src.generate_data")

    with sqlite3.connect(DB_PATH) as conn:
        init_log(conn)

        transactions = extract_transactions(conn)
        print(f"[1/4] Extraction SQL     : {len(transactions)} transactions")

        anomalies = run_all_checks(transactions, as_of)
        print(f"[2/4] Contrôles qualité  : {len(anomalies)} anomalies sur "
              f"{anomalies['row_id'].nunique()} transactions")
        for check_type, n in anomalies["check_type"].value_counts().items():
            print(f"        - {check_type:<13}: {n}")

        stats = sync_log(conn, anomalies, as_of)
        print(f"[3/4] Journal d'exceptions: {stats['new']} nouvelles, "
              f"{stats['auto_resolved']} résolues automatiquement, {stats['reopened']} rouvertes")

        write_reports(conn, transactions, anomalies, as_of)
        print(f"[4/4] Rapport            : {REPORTS_DIR.name}/summary.md et exception_log.csv")


if __name__ == "__main__":
    main()
