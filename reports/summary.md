# Rapport Data Quality — Market Operations

Date de référence : **2026-11-20**

## Vue d'ensemble

- Transactions analysées : **207**
- Anomalies détectées à cette date : **44** (sur **44** transactions)
- Anomalies suivies dans le journal : **44** dont **44** encore ouvertes

## Score de qualité par dimension

| Dimension | Lignes en anomalie | Score de qualité (%) |
|---|---|---|
| Completeness | 12 | 94.2 |
| Validity | 15 | 92.8 |
| Uniqueness | 7 | 96.6 |
| Consistency | 10 | 95.2 |
| Global (au moins une anomalie) | 44 | 78.7 |

## Anomalies par règle

| Contrôle | Règle | Description | Anomalies |
|---|---|---|---|
| Completeness | MISSING_AMOUNT | Montant manquant | 5 |
| Uniqueness | DUPLICATE_ID | Identifiant de transaction en doublon | 4 |
| Validity | INVALID_AMOUNT | Montant négatif ou nul | 4 |
| Validity | INVALID_CURRENCY | Devise invalide (hors liste autorisée) | 4 |
| Consistency | SETTLEMENT_BEFORE_TRADE | Date de règlement antérieure à la date de transaction | 4 |
| Validity | INVALID_TRADE_DATE | Date de transaction invalide ou format non conforme | 3 |
| Completeness | MISSING_CURRENCY | Devise manquante | 3 |
| Consistency | PENDING_PAST_SETTLEMENT | Encore PENDING alors que la date de règlement est passée | 3 |
| Uniqueness | POTENTIAL_DUPLICATE | Doublon potentiel (mêmes caractéristiques, identifiant différent) | 3 |
| Consistency | SETTLED_WITHOUT_SETTLEMENT_DATE | Statut SETTLED mais aucune date de règlement | 3 |
| Validity | FUTURE_TRADE_DATE | Date de transaction dans le futur | 2 |
| Validity | INVALID_STATUS | Statut invalide (hors liste autorisée) | 2 |
| Completeness | MISSING_COUNTERPARTY | Contrepartie manquante | 2 |
| Completeness | MISSING_TRANSACTION_ID | Identifiant manquant | 2 |

## Suivi des corrections

### Par statut

| Statut | Anomalies |
|---|---|
| À corriger | 44 |

### Par type de contrôle

| Contrôle | Détectées | Résolues | Taux de résolution (%) |
|---|---|---|---|
| Completeness | 12 | 0 | 0.0 |
| Validity | 15 | 0 | 0.0 |
| Uniqueness | 7 | 0 | 0.0 |
| Consistency | 10 | 0 | 0.0 |

### Anomalies ouvertes par équipe

| Équipe | Anomalies ouvertes | Plus ancienne (jours) |
|---|---|---|
| Reference Data | 15 | 0 |
| Middle Office | 12 | 0 |
| Settlement | 10 | 0 |
| Trade Capture | 7 | 0 |
