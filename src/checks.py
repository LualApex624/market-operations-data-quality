"""Les quatre familles de contrôles qualité.

Chaque contrôle reçoit le DataFrame des transactions et renvoie un DataFrame
d'anomalies (une ligne = une anomalie détectée) avec les colonnes :
row_id, transaction_id, check_type, rule, description.
"""
import pandas as pd

from src.config import (
    ALLOWED_CURRENCIES, ALLOWED_STATUSES, COMPLETENESS, CONSISTENCY, MANDATORY_FIELDS,
    UNIQUENESS, VALIDITY,
)

COLUMNS = ["row_id", "transaction_id", "check_type", "rule", "description"]
DATE_FORMAT = "%Y-%m-%d"


# --- Outils communs ---------------------------------------------------------

def _flag(df, mask, check_type, rule, description):
    """Transforme un masque booléen en lignes d'anomalies."""
    out = df.loc[mask, ["row_id", "transaction_id"]].copy()
    out["check_type"] = check_type
    out["rule"] = rule
    out["description"] = description
    return out[COLUMNS]


def _is_missing(series):
    """Vrai si la valeur est NULL ou une chaîne vide."""
    return series.isna() | series.astype(str).str.strip().eq("")


def _parse_dates(series):
    """Convertit en dates ; les valeurs impossibles ou mal formatées deviennent NaT."""
    return pd.to_datetime(series, format=DATE_FORMAT, errors="coerce")


# --- 1. Completeness --------------------------------------------------------

def check_completeness(df, as_of=None):
    """Les champs obligatoires doivent être renseignés."""
    results = [
        _flag(df, _is_missing(df[field]), COMPLETENESS, f"MISSING_{field.upper()}", label)
        for field, label in MANDATORY_FIELDS.items()
    ]
    return pd.concat(results, ignore_index=True)


# --- 2. Validity ------------------------------------------------------------

def check_validity(df, as_of):
    """Les valeurs doivent respecter les règles métier (listes autorisées, bornes, dates)."""
    present = lambda col: ~_is_missing(df[col])  # un champ absent relève de Completeness
    amount = pd.to_numeric(df["amount"], errors="coerce")
    trade_dt = _parse_dates(df["trade_date"])
    results = [
        _flag(df, present("currency") & ~df["currency"].isin(ALLOWED_CURRENCIES),
              VALIDITY, "INVALID_CURRENCY", "Devise invalide (hors liste autorisée)"),
        _flag(df, amount.notna() & (amount <= 0),
              VALIDITY, "INVALID_AMOUNT", "Montant négatif ou nul"),
        _flag(df, present("status") & ~df["status"].isin(ALLOWED_STATUSES),
              VALIDITY, "INVALID_STATUS", "Statut invalide (hors liste autorisée)"),
        _flag(df, present("trade_date") & trade_dt.isna(),
              VALIDITY, "INVALID_TRADE_DATE", "Date de transaction invalide ou format non conforme"),
        _flag(df, present("settlement_date") & _parse_dates(df["settlement_date"]).isna(),
              VALIDITY, "INVALID_SETTLEMENT_DATE", "Date de règlement invalide ou format non conforme"),
        _flag(df, trade_dt > pd.Timestamp(as_of),
              VALIDITY, "FUTURE_TRADE_DATE", "Date de transaction dans le futur"),
    ]
    return pd.concat(results, ignore_index=True)


# --- 3. Uniqueness ----------------------------------------------------------

# Champs qui, ensemble, décrivent "la même opération" même si l'identifiant diffère
BUSINESS_KEY = ["product", "trade_date", "amount", "currency", "counterparty"]


def check_uniqueness(df, as_of=None):
    """Une transaction ne doit pas être enregistrée plusieurs fois."""
    # On garde la première occurrence et on signale les suivantes.
    duplicate_id = ~_is_missing(df["transaction_id"]) & df.duplicated("transaction_id", keep="first")

    # Même opération saisie sous un autre identifiant (doublon "potentiel" : à vérifier).
    complete_key = ~df[BUSINESS_KEY].isna().any(axis=1)
    potential = complete_key & df.duplicated(BUSINESS_KEY, keep="first") & ~duplicate_id

    return pd.concat([
        _flag(df, duplicate_id, UNIQUENESS, "DUPLICATE_ID", "Identifiant de transaction en doublon"),
        _flag(df, potential, UNIQUENESS, "POTENTIAL_DUPLICATE",
              "Doublon potentiel (mêmes caractéristiques, identifiant différent)"),
    ], ignore_index=True)


# --- 4. Consistency ---------------------------------------------------------

def check_consistency(df, as_of):
    """Les informations d'une même transaction ne doivent pas se contredire."""
    trade_dt = _parse_dates(df["trade_date"])
    settle_dt = _parse_dates(df["settlement_date"])
    return pd.concat([
        _flag(df, (df["status"] == "SETTLED") & _is_missing(df["settlement_date"]),
              CONSISTENCY, "SETTLED_WITHOUT_SETTLEMENT_DATE",
              "Statut SETTLED mais aucune date de règlement"),
        _flag(df, (df["status"] == "PENDING") & (settle_dt <= pd.Timestamp(as_of)),
              CONSISTENCY, "PENDING_PAST_SETTLEMENT",
              "Encore PENDING alors que la date de règlement est passée"),
        _flag(df, settle_dt < trade_dt,
              CONSISTENCY, "SETTLEMENT_BEFORE_TRADE",
              "Date de règlement antérieure à la date de transaction"),
    ], ignore_index=True)


# --- Orchestration ----------------------------------------------------------

CHECKS = [check_completeness, check_validity, check_uniqueness, check_consistency]


def run_all_checks(df, as_of):
    """Lance tous les contrôles et renvoie l'ensemble des anomalies."""
    anomalies = pd.concat([check(df, as_of) for check in CHECKS], ignore_index=True)
    return anomalies.sort_values(["row_id", "rule"]).reset_index(drop=True)
