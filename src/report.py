"""Rapport d'anomalies : indicateurs (SQL) + scores de qualité (Pandas)."""
import pandas as pd

from src.config import CHECK_TYPES, REPORTS_DIR, SQL_DIR


def load_queries():
    """Lit sql/kpis.sql et renvoie {nom: requête}."""
    queries, name, lines = {}, None, []
    for line in (SQL_DIR / "kpis.sql").read_text().splitlines():
        if line.startswith("-- name:"):
            if name:
                queries[name] = "\n".join(lines).strip().rstrip(";")
            name, lines = line.split(":", 1)[1].strip(), []
        elif name:
            lines.append(line)
    if name:
        queries[name] = "\n".join(lines).strip().rstrip(";")
    return queries


def quality_scores(transactions, anomalies):
    """Pour chaque dimension : % de transactions sans aucune anomalie de ce type."""
    total = len(transactions)
    rows = []
    for check_type in CHECK_TYPES:
        flagged = anomalies.loc[anomalies["check_type"] == check_type, "row_id"].nunique()
        rows.append({"Dimension": check_type, "Lignes en anomalie": flagged,
                     "Score de qualité (%)": round(100 * (1 - flagged / total), 1)})
    flagged_any = anomalies["row_id"].nunique()
    rows.append({"Dimension": "Global (au moins une anomalie)", "Lignes en anomalie": flagged_any,
                 "Score de qualité (%)": round(100 * (1 - flagged_any / total), 1)})
    return pd.DataFrame(rows)


def _md_table(df):
    """DataFrame -> tableau Markdown (sans dépendance supplémentaire)."""
    header = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([header, sep, *body])


def build_report(conn, transactions, anomalies, as_of):
    """Assemble le rapport Markdown."""
    queries = load_queries()
    kpi = lambda name: pd.read_sql(queries[name], conn, params={"as_of": as_of.isoformat()})
    total_log = conn.execute("SELECT COUNT(*) FROM exception_log").fetchone()[0]
    open_count = conn.execute("SELECT COUNT(*) FROM exception_log WHERE status <> 'Résolu'").fetchone()[0]

    sections = [
        f"# Rapport Data Quality — Market Operations\n\nDate de référence : **{as_of.isoformat()}**",
        "## Vue d'ensemble\n\n"
        f"- Transactions analysées : **{len(transactions)}**\n"
        f"- Anomalies détectées à cette date : **{len(anomalies)}** "
        f"(sur **{anomalies['row_id'].nunique()}** transactions)\n"
        f"- Anomalies suivies dans le journal : **{total_log}** dont **{open_count}** encore ouvertes",
        "## Score de qualité par dimension\n\n" + _md_table(quality_scores(transactions, anomalies)),
        "## Anomalies par règle\n\n" + _md_table(kpi("by_rule")),
        "## Suivi des corrections\n\n### Par statut\n\n" + _md_table(kpi("by_status")),
        "### Par type de contrôle\n\n" + _md_table(kpi("by_check")),
        "### Anomalies ouvertes par équipe\n\n" + _md_table(kpi("open_by_team")),
    ]
    return "\n\n".join(sections) + "\n"


def write_reports(conn, transactions, anomalies, as_of):
    """Écrit reports/summary.md et reports/exception_log.csv."""
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "summary.md").write_text(build_report(conn, transactions, anomalies, as_of))
    pd.read_sql("SELECT * FROM exception_log ORDER BY exception_id", conn).to_csv(
        REPORTS_DIR / "exception_log.csv", index=False)
