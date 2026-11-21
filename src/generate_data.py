"""Génère une base SQLite de transactions fictives contenant des anomalies injectées.

Les données sont 100 % synthétiques. Le générateur crée d'abord des transactions
propres, puis y injecte volontairement des erreurs de chaque famille (complétude,
validité, unicité, cohérence) pour que les contrôles aient quelque chose à détecter.
La graine aléatoire est fixe : on obtient toujours les mêmes données.

Usage : python -m src.generate_data
"""
import random
import sqlite3
from datetime import timedelta

from src.config import (
    ALLOWED_CURRENCIES, AS_OF_DATE, COUNTERPARTIES, DB_PATH, PRODUCTS, SQL_DIR,
)

N_CLEAN = 200
SEED = 42


def build_clean_rows(rng):
    """Transactions valides : règlement à J+2, statut cohérent avec les dates."""
    rows = []
    for i in range(1, N_CLEAN + 1):
        trade = AS_OF_DATE - timedelta(days=rng.randint(0, 40))
        settle = trade + timedelta(days=2)
        if settle <= AS_OF_DATE:
            status = rng.choices(["SETTLED", "CANCELLED"], weights=[92, 8])[0]
        else:
            status = rng.choice(["PENDING", "CONFIRMED"])
        rows.append({
            "transaction_id": f"TR{i:04d}",
            "product": rng.choice(PRODUCTS),
            "trade_date": trade.isoformat(),
            "settlement_date": None if status == "CANCELLED" else settle.isoformat(),
            "amount": round(rng.uniform(10_000, 2_000_000), 2),
            "currency": rng.choice(sorted(ALLOWED_CURRENCIES)),
            "counterparty": rng.choice(COUNTERPARTIES),
            "status": status,
        })
    return rows


def inject_anomalies(rows, rng):
    """Corrompt des lignes distinctes (une anomalie par ligne) et ajoute des doublons."""
    free = list(range(len(rows)))
    rng.shuffle(free)

    def take(k):
        return [rows[free.pop()] for _ in range(k)]

    # --- Completeness : champs obligatoires absents ---
    for r in take(5):
        r["amount"] = None
    for r in take(3):
        r["currency"] = None
    for r in take(2):
        r["counterparty"] = None
    for r in take(2):
        r["transaction_id"] = None

    # --- Validity : valeurs hors règles ---
    for r in take(4):
        r["currency"] = "XXX"                        # devise hors liste autorisée
    for r in take(4):
        r["amount"] = -r["amount"]                   # montant négatif
    for r in take(2):
        r["status"] = "UNKNOWN"                      # statut hors liste
    for r, bad in zip(take(3), ["2026-13-45", "2026-02-30", "20/11/2026"]):
        r["trade_date"] = bad                        # dates impossibles ou mauvais format
    for r in take(2):                                # date de transaction dans le futur
        r["trade_date"] = (AS_OF_DATE + timedelta(days=5)).isoformat()
        r["settlement_date"] = (AS_OF_DATE + timedelta(days=7)).isoformat()
        r["status"] = "PENDING"

    # --- Consistency : informations qui se contredisent ---
    for r in take(3):                                # réglée mais sans date de règlement
        r["status"] = "SETTLED"
        r["settlement_date"] = None
    for r in take(4):                                # règlement avant la transaction
        r["status"] = "SETTLED"
        r["settlement_date"] = (
            AS_OF_DATE - timedelta(days=rng.randint(45, 50))
        ).isoformat()
    for r in take(3):                                # en attente alors que le règlement est passé
        settle = AS_OF_DATE - timedelta(days=rng.randint(3, 10))
        r["status"] = "PENDING"
        r["trade_date"] = (settle - timedelta(days=2)).isoformat()
        r["settlement_date"] = settle.isoformat()

    # --- Uniqueness : doublons ---
    extra = []
    for r in take(4):                                # même identifiant enregistré deux fois
        extra.append(dict(r))
    for n, r in enumerate(take(3), start=1):         # mêmes données, identifiant différent
        copy = dict(r)
        copy["transaction_id"] = f"TR{N_CLEAN + n:04d}"
        extra.append(copy)

    rows.extend(extra)
    rng.shuffle(rows)
    return rows


def main():
    rng = random.Random(SEED)
    rows = inject_anomalies(build_clean_rows(rng), rng)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.unlink(missing_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript((SQL_DIR / "schema.sql").read_text())
        conn.executemany(
            "INSERT INTO transactions (transaction_id, product, trade_date, settlement_date,"
            " amount, currency, counterparty, status)"
            " VALUES (:transaction_id, :product, :trade_date, :settlement_date,"
            " :amount, :currency, :counterparty, :status)",
            rows,
        )
    print(f"{len(rows)} transactions générées dans {DB_PATH}")


if __name__ == "__main__":
    main()
