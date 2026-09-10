-- ============================================
-- TBX Finance — indexes for large transaction ledger
-- Apply after schema + seed / large-scale load.
--
-- Usage:
--   mysql -u tiby -p tiby_hackathon < database/mysql_indexes.sql
-- ============================================

-- Date + type filters ("this month" debits)
ALTER TABLE `transaction`
  ADD INDEX idx_txn_date_type (transaction_date, transaction_type);

ALTER TABLE `transaction`
  ADD INDEX idx_txn_type_date (transaction_type, transaction_date);

-- Merchant / narration search (BOOLEAN MODE in app when available)
-- LIKE '%token%' still cannot use this index; MATCH() can.
ALTER TABLE `transaction`
  ADD FULLTEXT INDEX ft_txn_description (description);
