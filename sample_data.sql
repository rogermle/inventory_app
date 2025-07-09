-- Sample data for inventory_item table
INSERT INTO inventory_item (name, description, quantity, reorder_level, price) VALUES
  ('Widget A', 'Standard widget for general use', 50, 10, 2.99),
  ('Widget B', 'Heavy-duty widget for industrial use', 20, 5, 5.49),
  ('Gadget X', 'Compact gadget, battery powered', 100, 25, 7.99),
  ('Gadget Y', 'Large gadget with advanced features', 10, 2, 15.99),
  ('Spare Part Z', 'Replacement part for Widget A', 200, 50, 0.99);

-- Sample orders
INSERT INTO "order" (id, date, total) VALUES
  (1, '2025-07-01', 59.80),
  (2, '2025-07-02', 15.98),
  (3, '2025-07-03', 47.85);

-- Sample order_items
INSERT INTO order_item (order_id, inventory_item_id, quantity, price_at_sale) VALUES
  (1, 1, 10, 2.99),   -- 10 x Widget A for Order 1
  (1, 3, 5, 7.99),    -- 5 x Gadget X for Order 1
  (2, 2, 2, 5.49),    -- 2 x Widget B for Order 2
  (2, 5, 5, 0.99),    -- 5 x Spare Part Z for Order 2
  (3, 4, 3, 15.99);   -- 3 x Gadget Y for Order 3
