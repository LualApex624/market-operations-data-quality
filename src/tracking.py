"""Journal des exceptions et suivi de leur résolution (Exception Logging & Remediation Tracking).

Détecter une anomalie ne suffit pas : il faut savoir qui doit la corriger, depuis
quand elle existe et si elle est résolue. Ces informations sont stockées dans la
table `exception_log`.

Cycle de vie d'une anomalie :
    À corriger  ->  En cours  ->  Résolu
- Une anomalie détectée pour la première fois est créée avec le statut "À corriger".
- Si elle n'est plus détectée lors d'un contrôle ultérieur (donnée corrigée à la
  source), elle passe automatiquement à "Résolu".
- Si une anomalie "Résolue" réapparaît, elle est rouverte.
"""
import pandas as pd

from src.config import (
    OWNER_TEAMS, SQL_DIR, STATUS_RESOLVED, STATUS_TODO, TRACKING_STATUSES,
)


def init_log(conn):
    """Crée les tables si elles n'existent pas encore."""
    conn.executescript((SQL_DIR / "schema.sql").read_text())


def sync_log(conn, anomalies, as_of):
    """Aligne le journal sur les anomalies détectées aujourd'hui.

    Renvoie un dict de compteurs : new, reopened, auto_resolved.
    """
    today = as_of.isoformat()
    existing = pd.read_sql("SELECT exception_id, row_id, rule, status FROM exception_log", conn)
    known = {(int(r.row_id), r.rule): (int(r.exception_id), r.status) for r in existing.itertuples()}
    detected = {(int(r.row_id), r.rule) for r in anomalies.itertuples()}
    stats = {"new": 0, "reopened": 0, "auto_resolved": 0}

    for a in anomalies.itertuples(index=False):
        key = (int(a.row_id), a.rule)
        if key not in known:
            conn.execute(
                "INSERT INTO exception_log (row_id, transaction_id, check_type, rule, description,"
                " owner_team, status, detected_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (key[0], None if pd.isna(a.transaction_id) else a.transaction_id, a.check_type,
                 a.rule, a.description, OWNER_TEAMS[a.check_type], STATUS_TODO, today),
            )
            stats["new"] += 1
        elif known[key][1] == STATUS_RESOLVED:
            conn.execute(
                "UPDATE exception_log SET status = ?, resolved_date = NULL, comment = ?"
                " WHERE exception_id = ?",
                (STATUS_TODO, "Anomalie réapparue après résolution", known[key][0]),
            )
            stats["reopened"] += 1

    for key, (exception_id, status) in known.items():
        if key not in detected and status != STATUS_RESOLVED:
            conn.execute(
                "UPDATE exception_log SET status = ?, resolved_date = ?, comment = ?"
                " WHERE exception_id = ?",
                (STATUS_RESOLVED, today, "Résolue automatiquement : plus détectée", exception_id),
            )
            stats["auto_resolved"] += 1

    conn.commit()
    return stats


def update_status(conn, exception_id, new_status, as_of, comment=None):
    """Change manuellement le statut d'une anomalie (ex. une équipe prend le sujet en charge)."""
    if new_status not in TRACKING_STATUSES:
        raise ValueError(f"Statut inconnu : {new_status!r}. Valeurs possibles : {TRACKING_STATUSES}")
    resolved_date = as_of.isoformat() if new_status == STATUS_RESOLVED else None
    cursor = conn.execute(
        "UPDATE exception_log SET status = ?, resolved_date = ?, comment = COALESCE(?, comment)"
        " WHERE exception_id = ?",
        (new_status, resolved_date, comment, exception_id),
    )
    if cursor.rowcount == 0:
        raise ValueError(f"Aucune anomalie avec l'identifiant {exception_id}")
    conn.commit()
