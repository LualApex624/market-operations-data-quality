# Market Operations Data Quality

Système simple de **contrôle automatique de la qualité de données de transactions financières**, avec **journal des anomalies et suivi de leur correction**.

**Stack : Python · Pandas · SQL (SQLite)**

> Projet de portfolio. Les données sont **entièrement fictives** (générées par le script `src/generate_data.py`) ; elles imitent le flux de transactions qu'une équipe Market Operations / Middle Office reçoit chaque jour.

---

## 1. L'idée en 30 secondes

Une banque traite chaque jour des milliers de transactions (identifiant, produit, dates, montant, devise, contrepartie, statut). Ces données arrivent de plusieurs systèmes et **peuvent contenir des erreurs** : montant vide, devise `XXX`, transaction saisie deux fois, règlement avant la transaction…

Ces erreurs faussent les rapports financiers et les positions. Ce projet :

1. **récupère** les transactions (SQL),
2. **vérifie** automatiquement leur qualité avec 4 familles de contrôles (Python / Pandas),
3. **enregistre** chaque anomalie et **suit sa résolution** (qui doit agir, depuis quand, est-ce résolu ?),
4. **produit un rapport** avec des indicateurs.

```
 Base SQL ──► Extraction ──► 4 contrôles ──► Journal des exceptions ──► Rapport
(transactions)   (SQL)       (Pandas)      (suivi des corrections)    (KPI + CSV)
```

---

## 2. Les étapes expliquées (et à quoi elles servent)

### Étape 1 — Récupération des données (SQL)
- `sql/schema.sql` définit la table `transactions` **sans contraintes** (pas de clé unique, colonnes vides autorisées) : c'est le cas d'un flux externe, et c'est précisément ce qu'on veut contrôler.
- `sql/extract_transactions.sql` extrait les transactions ; `src/run_pipeline.py` les charge dans un DataFrame Pandas.
- **Utilité :** montrer qu'on sait interroger une base de données et alimenter une analyse.

### Étape 2 — Contrôles qualité (Python / Pandas) — `src/checks.py`

| Dimension | Question posée | Règles implémentées |
|---|---|---|
| **Completeness** (complétude) | Les infos obligatoires sont-elles là ? | Identifiant, produit, date, montant, devise, contrepartie, statut non vides |
| **Validity** (validité) | Les valeurs respectent-elles les règles ? | Devise dans la liste autorisée (EUR, USD, GBP, CHF, JPY) · montant strictement positif · statut dans la liste (PENDING, CONFIRMED, SETTLED, CANCELLED) · dates au format `YYYY-MM-DD` et existantes · date de transaction pas dans le futur |
| **Uniqueness** (unicité) | Une transaction est-elle enregistrée plusieurs fois ? | Identifiant en doublon · *doublon potentiel* (mêmes produit, date, montant, devise, contrepartie sous un autre identifiant) |
| **Consistency** (cohérence) | Les infos se contredisent-elles ? | `SETTLED` sans date de règlement · encore `PENDING` alors que la date de règlement est passée · règlement antérieur à la transaction |

Deux choix de conception importants :
- Une valeur **absente** est signalée une seule fois (Completeness) et **pas** une seconde fois comme invalide : on évite de compter deux fois la même erreur.
- Chaque contrôle est une fonction courte qui renvoie un tableau d'anomalies au même format → facile à lire, à tester et à compléter avec de nouvelles règles.

**Utilité :** c'est le cœur métier : traduire des règles de gestion en code, de façon automatique et répétable.

### Étape 3 — Journal des exceptions et suivi (Exception Logging & Remediation Tracking) — `src/tracking.py`
Détecter ne suffit pas : il faut suivre la résolution. Chaque anomalie est stockée **une seule fois** dans la table `exception_log` avec :
- la règle et la description (`Devise invalide`),
- l'**équipe responsable** (Completeness → Middle Office, Validity → Reference Data, Uniqueness → Trade Capture, Consistency → Settlement),
- la **date de détection** (pour mesurer l'ancienneté),
- un **statut** : `À corriger` → `En cours` → `Résolu`.

Règles du cycle de vie :
- première détection → créée en `À corriger` ;
- elle n'est plus détectée au contrôle suivant (donnée corrigée à la source) → passe **automatiquement** en `Résolu` ;
- une anomalie `Résolu` qui réapparaît → **rouverte** ;
- une équipe change le statut à la main avec `src/update_status.py`.

**Utilité :** répond aux questions du management : combien d'anomalies ? quelles équipes doivent intervenir ? depuis quand ? combien sont résolues ?

### Étape 4 — Rapport (`src/report.py`, `sql/kpis.sql`)
- **Score de qualité** par dimension = % de transactions sans anomalie de ce type (Pandas).
- **Indicateurs de suivi** (SQL) : anomalies par statut, par type de contrôle (avec taux de résolution), par équipe avec l'ancienneté de la plus vieille anomalie ouverte.
- Sorties : `reports/summary.md` (lisible) et `reports/exception_log.csv` (détail, exploitable dans Excel).

**Utilité :** transformer les contrôles en information de pilotage directement lisible.

---

## 3. Lancer le projet

Prérequis : Python 3.10+.

```bash
pip install -r requirements.txt

python -m src.generate_data     # crée la base de démonstration (207 transactions)
python -m src.run_pipeline      # extraction -> contrôles -> journal -> rapport
python -m pytest                # 24 tests unitaires
```

Résultat attendu au premier lancement : **44 anomalies détectées**, ce qui correspond exactement aux 44 erreurs injectées par le générateur (12 Completeness, 15 Validity, 7 Uniqueness, 10 Consistency).

### Simuler la remédiation
```bash
# Une équipe prend en charge deux montants manquants
python -m src.update_status 1 "En cours" --comment "Montant redemandé à la contrepartie"
python -m src.update_status 10 "En cours" --comment "Montant redemandé à la contrepartie"

# Reference Data corrige les devises "XXX" dans la base source
sqlite3 data/market_ops.db "UPDATE transactions SET currency = 'USD' WHERE currency = 'XXX';"

# Nouveau contrôle : les 4 anomalies corrigées passent automatiquement en "Résolu"
python -m src.run_pipeline
```
Le dossier `reports/` du dépôt contient le résultat de cette simulation (38 `À corriger`, 2 `En cours`, 4 `Résolu`).

---

## 4. Structure du dépôt

```
sql/
  schema.sql                 tables transactions et exception_log
  extract_transactions.sql   requête d'extraction
  kpis.sql                   indicateurs de suivi
src/
  config.py                  référentiels, équipes, statuts, date de référence
  generate_data.py           données fictives avec anomalies injectées
  checks.py                  les 4 familles de contrôles
  tracking.py                journal des exceptions et cycle de vie
  update_status.py           mise à jour manuelle d'un statut
  report.py                  scores qualité et rapport Markdown/CSV
  run_pipeline.py            enchaîne les 4 étapes
tests/                       tests unitaires (pytest)
reports/                     sorties : summary.md, exception_log.csv
```

---

## 5. Ce que ce projet démontre

- **Manipuler des données** : SQL pour extraire et agréger, Pandas pour transformer et analyser.
- **Définir des règles métier** : complétude, validité, unicité, cohérence appliquées à des transactions financières.
- **Automatiser des contrôles** : un seul lancement, résultat reproductible, règles testées.
- **Suivre la résolution des problèmes** : journal, responsables, ancienneté, taux de résolution.

## 6. Hypothèses et limites

- Données synthétiques, date de référence fixée au `2026-11-20` pour la reproductibilité (option `--as-of` pour la changer ; en production ce serait la date du jour).
- Hypothèse métier : un montant doit être **strictement positif**.
- Un doublon *potentiel* est à vérifier, pas forcément une erreur.
- Pistes d'évolution : contrôle de cohérence devise/contrepartie, alertes e-mail, tableau de bord, connexion à une vraie base.
