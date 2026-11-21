"""Paramètres et référentiels communs au projet."""
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "market_ops.db"
SQL_DIR = ROOT / "sql"
REPORTS_DIR = ROOT / "reports"

# Date de référence des contrôles ("as of"). Fixée pour que la démo soit
# reproductible ; en production ce serait la date du jour (voir --as-of).
AS_OF_DATE = date(2026, 11, 20)

# --- Référentiels utilisés par les contrôles de validité ---
ALLOWED_CURRENCIES = {"EUR", "USD", "GBP", "CHF", "JPY"}
ALLOWED_STATUSES = {"PENDING", "CONFIRMED", "SETTLED", "CANCELLED"}

# Champs obligatoires -> message affiché quand ils sont absents (contrôle Completeness)
MANDATORY_FIELDS = {
    "transaction_id": "Identifiant manquant",
    "product": "Produit manquant",
    "trade_date": "Date de transaction manquante",
    "amount": "Montant manquant",
    "currency": "Devise manquante",
    "counterparty": "Contrepartie manquante",
    "status": "Statut manquant",
}

# Les quatre dimensions de qualité
COMPLETENESS = "Completeness"
VALIDITY = "Validity"
UNIQUENESS = "Uniqueness"
CONSISTENCY = "Consistency"
CHECK_TYPES = [COMPLETENESS, VALIDITY, UNIQUENESS, CONSISTENCY]

# Équipe responsable de la correction selon le type d'anomalie
OWNER_TEAMS = {
    COMPLETENESS: "Middle Office",
    VALIDITY: "Reference Data",
    UNIQUENESS: "Trade Capture",
    CONSISTENCY: "Settlement",
}

# Statuts de suivi d'une anomalie
STATUS_TODO = "À corriger"
STATUS_IN_PROGRESS = "En cours"
STATUS_RESOLVED = "Résolu"
TRACKING_STATUSES = [STATUS_TODO, STATUS_IN_PROGRESS, STATUS_RESOLVED]

# Données de démonstration
PRODUCTS = ["Equity", "Bond", "FX", "Derivative"]
COUNTERPARTIES = ["BNP Paribas", "Societe Generale", "JP Morgan", "Goldman Sachs", "Deutsche Bank", "Barclays"]
