"""Outils de test partagés."""
import pandas as pd
import pytest

from src.config import AS_OF_DATE


@pytest.fixture
def as_of():
    return AS_OF_DATE


def make_df(*overrides):
    """Construit un DataFrame de transactions valides ; chaque dict modifie une ligne."""
    base = {
        "transaction_id": "TR1", "product": "Equity", "trade_date": "2026-11-10",
        "settlement_date": "2026-11-12", "amount": 150000.0, "currency": "EUR",
        "counterparty": "BNP Paribas", "status": "SETTLED",
    }
    rows = [{**base, "transaction_id": f"TR{i + 1}", **o} for i, o in enumerate(overrides)]
    df = pd.DataFrame(rows)
    df.insert(0, "row_id", range(1, len(df) + 1))
    return df


def rules_found(anomalies):
    """Ensemble des (row_id, règle) détectés, pratique pour les assertions."""
    return set(zip(anomalies["row_id"], anomalies["rule"]))
