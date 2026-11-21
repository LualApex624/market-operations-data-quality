-- Indicateurs de suivi calculés en SQL sur le journal des exceptions.
-- Chaque requête est introduite par "-- name: <nom>" et lue par src/report.py.
-- :as_of est la date de référence du rapport.

-- name: by_status
SELECT status AS "Statut", COUNT(*) AS "Anomalies"
FROM exception_log
GROUP BY status
ORDER BY CASE status WHEN 'À corriger' THEN 1 WHEN 'En cours' THEN 2 ELSE 3 END;

-- name: by_check
SELECT
    check_type AS "Contrôle",
    COUNT(*) AS "Détectées",
    SUM(status = 'Résolu') AS "Résolues",
    ROUND(100.0 * SUM(status = 'Résolu') / COUNT(*), 1) AS "Taux de résolution (%)"
FROM exception_log
GROUP BY check_type
ORDER BY CASE check_type
    WHEN 'Completeness' THEN 1 WHEN 'Validity' THEN 2
    WHEN 'Uniqueness' THEN 3 ELSE 4 END;

-- name: open_by_team
SELECT
    owner_team AS "Équipe",
    COUNT(*) AS "Anomalies ouvertes",
    MAX(CAST(julianday(:as_of) - julianday(detected_date) AS INTEGER)) AS "Plus ancienne (jours)"
FROM exception_log
WHERE status <> 'Résolu'
GROUP BY owner_team
ORDER BY COUNT(*) DESC;

-- name: by_rule
SELECT check_type AS "Contrôle", rule AS "Règle", description AS "Description", COUNT(*) AS "Anomalies"
FROM exception_log
GROUP BY check_type, rule, description
ORDER BY COUNT(*) DESC, rule;
