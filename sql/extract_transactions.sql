-- Étape 1 du pipeline : extraction des transactions depuis la base.
SELECT
    row_id,
    transaction_id,
    product,
    trade_date,
    settlement_date,
    amount,
    currency,
    counterparty,
    status
FROM transactions
ORDER BY row_id;
