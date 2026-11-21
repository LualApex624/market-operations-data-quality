"""Met à jour le statut d'une anomalie du journal.

Exemples :
    python -m src.update_status 12 "En cours" --comment "Pris en charge par Reference Data"
    python -m src.update_status 12 "Résolu"
"""
import argparse
import sqlite3
from datetime import date

from src.config import AS_OF_DATE, DB_PATH, TRACKING_STATUSES
from src.tracking import update_status


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("exception_id", type=int, help="identifiant de l'anomalie (colonne exception_id)")
    parser.add_argument("status", choices=TRACKING_STATUSES)
    parser.add_argument("--comment", help="commentaire libre")
    parser.add_argument("--as-of", type=date.fromisoformat, default=AS_OF_DATE,
                        help="date de la mise à jour (YYYY-MM-DD)")
    args = parser.parse_args()

    with sqlite3.connect(DB_PATH) as conn:
        update_status(conn, args.exception_id, args.status, args.as_of, args.comment)
    print(f"Anomalie {args.exception_id} -> {args.status}")


if __name__ == "__main__":
    main()
