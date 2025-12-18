-- ============================================================================
-- DROP EXISTING TABLES IF THEY EXIST (in correct order due to foreign keys)
-- ============================================================================
DROP TABLE IF EXISTS payment_transactions CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS payment_methods CASCADE;
DROP TABLE IF EXISTS shipping_addresses CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- ============================================================================
-- RECREATE TABLES
-- ============================================================================

-- CUSTOMERS TABLE
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_created_at ON customers(created_at);

-- PRODUCTS TABLE
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    product_sku VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(100),
    sell_price NUMERIC(10, 2) NOT NULL CHECK (sell_price >= 0),
    cost_of_goods_sold NUMERIC(10, 2) NOT NULL CHECK (cost_of_goods_sold >= 0),
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_sku ON products(product_sku);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_is_active ON products(is_active);

-- SHIPPING ADDRESSES TABLE
CREATE TABLE shipping_addresses (
    address_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100),
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(100) NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

CREATE INDEX idx_shipping_addresses_customer_id ON shipping_addresses(customer_id);
CREATE INDEX idx_shipping_addresses_is_default ON shipping_addresses(is_default);

-- PAYMENT METHODS TABLE
CREATE TABLE payment_methods (
    payment_method_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    payment_type VARCHAR(20) NOT NULL CHECK (payment_type IN ('credit_card', 'debit_card', 'paypal')),
    card_last_four VARCHAR(4),
    card_brand VARCHAR(50),
    expiry_month INTEGER CHECK (expiry_month BETWEEN 1 AND 12),
    expiry_year INTEGER CHECK (expiry_year >= EXTRACT(YEAR FROM CURRENT_DATE)),
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

CREATE INDEX idx_payment_methods_customer_id ON payment_methods(customer_id);
CREATE INDEX idx_payment_methods_is_default ON payment_methods(is_default);

-- ORDERS TABLE
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    shipping_address_id INTEGER NOT NULL,
    payment_method_id INTEGER NOT NULL,
    order_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (order_status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),
    subtotal NUMERIC(10, 2) NOT NULL CHECK (subtotal >= 0),
    tax NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (tax >= 0),
    shipping_cost NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (shipping_cost >= 0),
    total NUMERIC(10, 2) NOT NULL CHECK (total >= 0),
    order_date TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    shipped_date TIMESTAMP WITHOUT TIME ZONE,
    delivered_date TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE RESTRICT,
    FOREIGN KEY (shipping_address_id) REFERENCES shipping_addresses(address_id) ON DELETE RESTRICT,
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(payment_method_id) ON DELETE RESTRICT,
    CHECK (shipped_date IS NULL OR shipped_date >= order_date),
    CHECK (delivered_date IS NULL OR delivered_date >= shipped_date)
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_status ON orders(order_status);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- ORDER ITEMS TABLE
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    product_sku VARCHAR(100),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    total_price NUMERIC(10, 2) NOT NULL CHECK (total_price >= 0),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT,
    CHECK (total_price = quantity * unit_price)
);

CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);

-- PAYMENT TRANSACTIONS TABLE
CREATE TABLE payment_transactions (
    transaction_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    payment_method_id INTEGER NOT NULL,
    transaction_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (transaction_status IN ('pending', 'completed', 'failed', 'refunded')),
    transaction_amount NUMERIC(10, 2) NOT NULL CHECK (transaction_amount >= 0),
    transaction_date TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    payment_gateway VARCHAR(50),
    gateway_transaction_id VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE RESTRICT,
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(payment_method_id) ON DELETE RESTRICT
);

CREATE INDEX idx_payment_transactions_order_id ON payment_transactions(order_id);
CREATE INDEX idx_payment_transactions_status ON payment_transactions(transaction_status);
CREATE INDEX idx_payment_transactions_date ON payment_transactions(transaction_date);

-- TRIGGERS FOR UPDATED_AT TIMESTAMPS
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shipping_addresses_updated_at BEFORE UPDATE ON shipping_addresses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payment_methods_updated_at BEFORE UPDATE ON payment_methods
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- GENERATE 100 RANDOM CUSTOMERS
-- ============================================================================
INSERT INTO customers (first_name, last_name, email, phone) VALUES
('Emma', 'Johnson', 'emma.johnson@email.com', '+1-555-0102'),
('Liam', 'Williams', 'liam.williams@email.com', '+1-555-0103'),
('Olivia', 'Brown', 'olivia.brown@email.com', '+1-555-0104'),
('Noah', 'Jones', 'noah.jones@email.com', '+1-555-0105'),
('Ava', 'Garcia', 'ava.garcia@email.com', '+1-555-0106'),
('Ethan', 'Miller', 'ethan.miller@email.com', '+1-555-0107'),
('Sophia', 'Davis', 'sophia.davis@email.com', '+1-555-0108'),
('Mason', 'Rodriguez', 'mason.rodriguez@email.com', '+1-555-0109'),
('Isabella', 'Martinez', 'isabella.martinez@email.com', '+1-555-0110'),
('William', 'Hernandez', 'william.hernandez@email.com', '+1-555-0111'),
('Mia', 'Lopez', 'mia.lopez@email.com', '+1-555-0112'),
('James', 'Gonzalez', 'james.gonzalez@email.com', '+1-555-0113'),
('Charlotte', 'Wilson', 'charlotte.wilson@email.com', '+1-555-0114'),
('Benjamin', 'Anderson', 'benjamin.anderson@email.com', '+1-555-0115'),
('Amelia', 'Thomas', 'amelia.thomas@email.com', '+1-555-0116'),
('Lucas', 'Taylor', 'lucas.taylor@email.com', '+1-555-0117'),
('Harper', 'Moore', 'harper.moore@email.com', '+1-555-0118'),
('Henry', 'Jackson', 'henry.jackson@email.com', '+1-555-0119'),
('Evelyn', 'Martin', 'evelyn.martin@email.com', '+1-555-0120'),
('Alexander', 'Lee', 'alexander.lee@email.com', '+1-555-0121'),
('Abigail', 'Perez', 'abigail.perez@email.com', '+1-555-0122'),
('Michael', 'Thompson', 'michael.thompson@email.com', '+1-555-0123'),
('Emily', 'White', 'emily.white@email.com', '+1-555-0124'),
('Daniel', 'Harris', 'daniel.harris@email.com', '+1-555-0125'),
('Elizabeth', 'Sanchez', 'elizabeth.sanchez@email.com', '+1-555-0126'),
('Matthew', 'Clark', 'matthew.clark@email.com', '+1-555-0127'),
('Sofia', 'Ramirez', 'sofia.ramirez@email.com', '+1-555-0128'),
('Joseph', 'Lewis', 'joseph.lewis@email.com', '+1-555-0129'),
('Avery', 'Robinson', 'avery.robinson@email.com', '+1-555-0130'),
('David', 'Walker', 'david.walker@email.com', '+1-555-0131'),
('Ella', 'Young', 'ella.young@email.com', '+1-555-0132'),
('Carter', 'Allen', 'carter.allen@email.com', '+1-555-0133'),
('Scarlett', 'King', 'scarlett.king@email.com', '+1-555-0134'),
('Wyatt', 'Wright', 'wyatt.wright@email.com', '+1-555-0135'),
('Grace', 'Scott', 'grace.scott@email.com', '+1-555-0136'),
('Jayden', 'Torres', 'jayden.torres@email.com', '+1-555-0137'),
('Chloe', 'Nguyen', 'chloe.nguyen@email.com', '+1-555-0138'),
('Luke', 'Hill', 'luke.hill@email.com', '+1-555-0139'),
('Victoria', 'Flores', 'victoria.flores@email.com', '+1-555-0140'),
('Jack', 'Green', 'jack.green@email.com', '+1-555-0141'),
('Lily', 'Adams', 'lily.adams@email.com', '+1-555-0142'),
('Owen', 'Nelson', 'owen.nelson@email.com', '+1-555-0143'),
('Hannah', 'Baker', 'hannah.baker@email.com', '+1-555-0144'),
('Lincoln', 'Hall', 'lincoln.hall@email.com', '+1-555-0145'),
('Addison', 'Rivera', 'addison.rivera@email.com', '+1-555-0146'),
('Gabriel', 'Campbell', 'gabriel.campbell@email.com', '+1-555-0147'),
('Natalie', 'Mitchell', 'natalie.mitchell@email.com', '+1-555-0148'),
('Grayson', 'Carter', 'grayson.carter@email.com', '+1-555-0149'),
('Zoey', 'Roberts', 'zoey.roberts@email.com', '+1-555-0150'),
('Ryan', 'Gomez', 'ryan.gomez@email.com', '+1-555-0151'),
('Nora', 'Phillips', 'nora.phillips@email.com', '+1-555-0152'),
('Sebastian', 'Evans', 'sebastian.evans@email.com', '+1-555-0153'),
('Aria', 'Turner', 'aria.turner@email.com', '+1-555-0154'),
('Isaac', 'Diaz', 'isaac.diaz@email.com', '+1-555-0155'),
('Audrey', 'Parker', 'audrey.parker@email.com', '+1-555-0156'),
('Levi', 'Cruz', 'levi.cruz@email.com', '+1-555-0157'),
('Brooklyn', 'Edwards', 'brooklyn.edwards@email.com', '+1-555-0158'),
('Mateo', 'Collins', 'mateo.collins@email.com', '+1-555-0159'),
('Layla', 'Reyes', 'layla.reyes@email.com', '+1-555-0160'),
('Nathan', 'Stewart', 'nathan.stewart@email.com', '+1-555-0161'),
('Zoe', 'Morris', 'zoe.morris@email.com', '+1-555-0162'),
('Caleb', 'Morales', 'caleb.morales@email.com', '+1-555-0163'),
('Penelope', 'Murphy', 'penelope.murphy@email.com', '+1-555-0164'),
('Joshua', 'Cook', 'joshua.cook@email.com', '+1-555-0165'),
('Riley', 'Rogers', 'riley.rogers@email.com', '+1-555-0166'),
('Christopher', 'Gutierrez', 'christopher.gutierrez@email.com', '+1-555-0167'),
('Bella', 'Ortiz', 'bella.ortiz@email.com', '+1-555-0168'),
('Andrew', 'Morgan', 'andrew.morgan@email.com', '+1-555-0169'),
('Claire', 'Cooper', 'claire.cooper@email.com', '+1-555-0170'),
('Samuel', 'Peterson', 'samuel.peterson@email.com', '+1-555-0171'),
('Lucy', 'Bailey', 'lucy.bailey@email.com', '+1-555-0172'),
('Jonathan', 'Reed', 'jonathan.reed@email.com', '+1-555-0173'),
('Anna', 'Kelly', 'anna.kelly@email.com', '+1-555-0174'),
('Julian', 'Howard', 'julian.howard@email.com', '+1-555-0175'),
('Caroline', 'Ramos', 'caroline.ramos@email.com', '+1-555-0176'),
('Christian', 'Kim', 'christian.kim@email.com', '+1-555-0177'),
('Savannah', 'Cox', 'savannah.cox@email.com', '+1-555-0178'),
('Hunter', 'Ward', 'hunter.ward@email.com', '+1-555-0179'),
('Genesis', 'Richardson', 'genesis.richardson@email.com', '+1-555-0180'),
('Eli', 'Watson', 'eli.watson@email.com', '+1-555-0181'),
('Kennedy', 'Brooks', 'kennedy.brooks@email.com', '+1-555-0182'),
('Colton', 'Chavez', 'colton.chavez@email.com', '+1-555-0183'),
('Skylar', 'Wood', 'skylar.wood@email.com', '+1-555-0184'),
('Aaron', 'James', 'aaron.james@email.com', '+1-555-0185'),
('Ellie', 'Bennett', 'ellie.bennett@email.com', '+1-555-0186'),
('Thomas', 'Gray', 'thomas.gray@email.com', '+1-555-0187'),
('Madelyn', 'Mendoza', 'madelyn.mendoza@email.com', '+1-555-0188'),
('Jeremiah', 'Ruiz', 'jeremiah.ruiz@email.com', '+1-555-0189'),
('Aubrey', 'Hughes', 'aubrey.hughes@email.com', '+1-555-0190'),
('Cameron', 'Price', 'cameron.price@email.com', '+1-555-0191'),
('Elena', 'Alvarez', 'elena.alvarez@email.com', '+1-555-0192'),
('Connor', 'Castillo', 'connor.castillo@email.com', '+1-555-0193'),
('Paisley', 'Sanders', 'paisley.sanders@email.com', '+1-555-0194'),
('Adrian', 'Patel', 'adrian.patel@email.com', '+1-555-0195'),
('Violet', 'Myers', 'violet.myers@email.com', '+1-555-0196'),
('Easton', 'Long', 'easton.long@email.com', '+1-555-0197'),
('Hazel', 'Ross', 'hazel.ross@email.com', '+1-555-0198'),
('Jaxon', 'Foster', 'jaxon.foster@email.com', '+1-555-0199'),
('Sadie', 'Jimenez', 'sadie.jimenez@email.com', '+1-555-0200'),
('Robert', 'Powell', 'robert.powell@email.com', '+1-555-0201');

-- ============================================================================
-- GENERATE SHIPPING ADDRESSES FOR ALL CUSTOMERS
-- ============================================================================
INSERT INTO shipping_addresses (customer_id, address_line1, city, state, postal_code, country, is_default)
SELECT 
    customer_id,
    CASE (customer_id % 20)
        WHEN 0 THEN '456 Oak Avenue'
        WHEN 1 THEN '789 Pine Street'
        WHEN 2 THEN '321 Maple Drive'
        WHEN 3 THEN '654 Elm Boulevard'
        WHEN 4 THEN '987 Cedar Lane'
        WHEN 5 THEN '147 Birch Road'
        WHEN 6 THEN '258 Willow Way'
        WHEN 7 THEN '369 Ash Court'
        WHEN 8 THEN '741 Spruce Avenue'
        WHEN 9 THEN '852 Poplar Street'
        WHEN 10 THEN '963 Cherry Drive'
        WHEN 11 THEN '159 Hickory Lane'
        WHEN 12 THEN '357 Walnut Road'
        WHEN 13 THEN '486 Cypress Way'
        WHEN 14 THEN '759 Magnolia Court'
        WHEN 15 THEN '864 Redwood Street'
        WHEN 16 THEN '951 Juniper Avenue'
        WHEN 17 THEN '753 Dogwood Drive'
        WHEN 18 THEN '246 Sycamore Lane'
        ELSE '135 Chestnut Boulevard'
    END,
    CASE (customer_id % 15)
        WHEN 0 THEN 'New York' WHEN 1 THEN 'Los Angeles' WHEN 2 THEN 'Chicago'
        WHEN 3 THEN 'Houston' WHEN 4 THEN 'Phoenix' WHEN 5 THEN 'Philadelphia'
        WHEN 6 THEN 'San Antonio' WHEN 7 THEN 'San Diego' WHEN 8 THEN 'Dallas'
        WHEN 9 THEN 'San Jose' WHEN 10 THEN 'Austin' WHEN 11 THEN 'Jacksonville'
        WHEN 12 THEN 'Fort Worth' WHEN 13 THEN 'Columbus' ELSE 'Charlotte'
    END,
    CASE (customer_id % 15)
        WHEN 0 THEN 'NY' WHEN 1 THEN 'CA' WHEN 2 THEN 'IL'
        WHEN 3 THEN 'TX' WHEN 4 THEN 'AZ' WHEN 5 THEN 'PA'
        WHEN 6 THEN 'TX' WHEN 7 THEN 'CA' WHEN 8 THEN 'TX'
        WHEN 9 THEN 'CA' WHEN 10 THEN 'TX' WHEN 11 THEN 'FL'
        WHEN 12 THEN 'TX' WHEN 13 THEN 'OH' ELSE 'NC'
    END,
    LPAD((10000 + (customer_id * 123) % 90000)::TEXT, 5, '0'),
    'USA',
    TRUE
FROM customers;

-- ============================================================================
-- GENERATE PAYMENT METHODS FOR ALL CUSTOMERS
-- ============================================================================
INSERT INTO payment_methods (customer_id, payment_type, card_last_four, card_brand, expiry_month, expiry_year, is_default)
SELECT 
    customer_id,
    CASE (customer_id % 3)
        WHEN 0 THEN 'credit_card'
        WHEN 1 THEN 'debit_card'
        ELSE 'paypal'
    END,
    CASE WHEN (customer_id % 3) != 2 THEN LPAD(((customer_id * 7) % 9999)::TEXT, 4, '0') ELSE NULL END,
    CASE (customer_id % 5)
        WHEN 0 THEN 'Visa'
        WHEN 1 THEN 'Mastercard'
        WHEN 2 THEN 'American Express'
        WHEN 3 THEN 'Discover'
        ELSE 'Visa'
    END,
    ((customer_id % 12) + 1),
    2026 + (customer_id % 4),
    TRUE
FROM customers;

-- ============================================================================
-- GENERATE 100 RANDOM PRODUCTS
-- ============================================================================
INSERT INTO products (product_name, product_sku, description, category, sell_price, cost_of_goods_sold, stock_quantity) VALUES
('Wireless Mouse Pro', 'WM-002', 'Premium wireless mouse with ergonomic design', 'Electronics', 34.99, 18.50, 200),
('Mechanical Keyboard RGB', 'KB-002', 'Gaming keyboard with customizable RGB lighting', 'Electronics', 89.99, 52.00, 120),
('USB-C Hub 7-in-1', 'HUB-001', 'Multi-port USB-C hub with HDMI and USB 3.0', 'Electronics', 45.99, 24.00, 180),
('Laptop Cooling Pad', 'CP-001', 'Adjustable laptop cooling pad with dual fans', 'Accessories', 29.99, 14.50, 250),
('Bluetooth Speaker', 'SPK-001', 'Portable waterproof Bluetooth speaker', 'Audio', 59.99, 32.00, 150),
('Wireless Earbuds', 'EB-001', 'True wireless earbuds with charging case', 'Audio', 79.99, 45.00, 100),
('Phone Stand Adjustable', 'PS-001', 'Universal adjustable phone stand', 'Accessories', 15.99, 6.50, 400),
('USB Wall Charger', 'CHG-001', 'Fast charging USB wall adapter', 'Electronics', 19.99, 8.00, 500),
('Screen Protector 3-Pack', 'SPR-001', 'Tempered glass screen protector', 'Accessories', 12.99, 4.50, 600),
('Phone Case Silicone', 'PC-001', 'Soft silicone protective phone case', 'Accessories', 14.99, 5.50, 450),
('Webcam HD 1080p', 'WC-001', 'Full HD webcam with autofocus', 'Electronics', 49.99, 28.00, 180),
('Microphone USB', 'MIC-001', 'Professional USB condenser microphone', 'Audio', 69.99, 38.00, 90),
('Monitor 24 inch', 'MON-001', '24-inch Full HD LED monitor', 'Electronics', 149.99, 95.00, 60),
('Desk Lamp LED', 'DL-001', 'Adjustable LED desk lamp with touch control', 'Office', 32.99, 16.00, 200),
('Office Chair Ergonomic', 'OC-001', 'Ergonomic office chair with lumbar support', 'Office', 199.99, 120.00, 40),
('Standing Desk Converter', 'SD-001', 'Height adjustable standing desk converter', 'Office', 159.99, 95.00, 50),
('Cable Management Box', 'CMB-001', 'Cable organizer box with multiple slots', 'Accessories', 18.99, 8.50, 300),
('Power Strip Surge Protector', 'PS-002', '6-outlet surge protector power strip', 'Electronics', 24.99, 12.00, 250),
('External Hard Drive 1TB', 'HDD-001', 'Portable external hard drive 1TB', 'Storage', 59.99, 38.00, 120),
('SSD External 500GB', 'SSD-001', 'External solid state drive 500GB', 'Storage', 79.99, 52.00, 100),
('USB Flash Drive 64GB', 'USB-001', 'High-speed USB 3.0 flash drive 64GB', 'Storage', 14.99, 6.50, 500),
('Memory Card 128GB', 'MC-001', 'MicroSD card 128GB with adapter', 'Storage', 22.99, 11.00, 400),
('Graphics Tablet', 'GT-001', 'Digital drawing tablet with pen', 'Electronics', 79.99, 48.00, 70),
('Stylus Pen', 'STY-001', 'Precision stylus pen for touchscreens', 'Accessories', 19.99, 8.50, 350),
('Laptop Bag 15 inch', 'LB-001', 'Professional laptop bag with multiple compartments', 'Accessories', 39.99, 22.00, 150),
('Backpack Tech', 'BP-001', 'Tech backpack with USB charging port', 'Accessories', 49.99, 28.00, 120),
('Mouse Pad Extended', 'MP-001', 'Extended gaming mouse pad', 'Accessories', 16.99, 7.50, 300),
('Wrist Rest Keyboard', 'WR-001', 'Memory foam keyboard wrist rest', 'Accessories', 12.99, 5.50, 400),
('Monitor Stand', 'MS-001', 'Adjustable monitor stand with storage', 'Office', 34.99, 18.00, 180),
('Document Scanner', 'DS-001', 'Portable document scanner', 'Office', 89.99, 58.00, 60),
('Label Maker', 'LM-001', 'Handheld label maker machine', 'Office', 29.99, 15.50, 200),
('Shredder Paper', 'SH-001', 'Cross-cut paper shredder', 'Office', 69.99, 42.00, 50),
('Whiteboard 24x36', 'WB-001', 'Magnetic dry erase whiteboard', 'Office', 44.99, 24.00, 80),
('Desk Organizer', 'DO-001', 'Multi-compartment desk organizer', 'Office', 19.99, 9.50, 250),
('File Folder Set', 'FF-001', 'Colored file folder set 12-pack', 'Office', 14.99, 6.00, 400),
('Sticky Notes Pack', 'SN-001', 'Sticky notes variety pack', 'Office', 8.99, 3.50, 600),
('Pen Set Premium', 'PEN-001', 'Professional ballpoint pen set', 'Office', 22.99, 11.00, 300),
('Notebook Leather', 'NB-001', 'Premium leather-bound notebook', 'Office', 24.99, 12.50, 250),
('Desk Calendar', 'DC-001', 'Monthly desk calendar pad', 'Office', 11.99, 5.00, 350),
('Tape Dispenser', 'TD-001', 'Heavy-duty tape dispenser', 'Office', 13.99, 6.50, 300),
('Stapler Heavy Duty', 'ST-001', 'Heavy duty desktop stapler', 'Office', 18.99, 9.00, 200),
('Hole Punch 3-Hole', 'HP-001', 'Adjustable 3-hole punch', 'Office', 16.99, 8.50, 200),
('Scissors Professional', 'SC-001', 'Professional office scissors', 'Office', 9.99, 4.50, 400),
('Highlighter Set', 'HL-001', 'Highlighter marker set 6-pack', 'Office', 7.99, 3.00, 500),
('Correction Tape', 'CT-001', 'Correction tape roller', 'Office', 5.99, 2.50, 600),
('Binder Clips Assorted', 'BC-001', 'Assorted size binder clips', 'Office', 6.99, 2.80, 550),
('Paper Clips Box', 'PCL-001', 'Paper clips box 500 count', 'Office', 4.99, 2.00, 700),
('Rubber Bands Box', 'RB-001', 'Assorted rubber bands box', 'Office', 5.99, 2.50, 600),
('Push Pins Box', 'PP-001', 'Colored push pins 100-pack', 'Office', 4.99, 2.00, 650),
('Envelope Box Letter', 'ENV-001', 'White letter envelopes 100-pack', 'Office', 12.99, 5.50, 400),
('Router WiFi 6', 'RTR-001', 'Dual-band WiFi 6 router', 'Electronics', 129.99, 78.00, 70),
('Network Cable 25ft', 'CAT-001', 'Cat6 Ethernet cable 25 feet', 'Cables', 14.99, 6.00, 500),
('Surge Protector 12-Outlet', 'SP-003', '12-outlet surge protector with USB', 'Electronics', 39.99, 22.00, 150),
('Smart Plug 4-Pack', 'SPG-001', 'WiFi smart plug 4-pack', 'Electronics', 34.99, 18.00, 200),
('LED Light Strip', 'LED-001', 'RGB LED light strip 16.4 feet', 'Electronics', 24.99, 12.50, 250),
('Security Camera', 'CAM-001', 'Indoor WiFi security camera', 'Electronics', 44.99, 26.00, 120),
('Video Doorbell', 'VDB-001', 'Smart video doorbell with motion detection', 'Electronics', 99.99, 62.00, 80),
('Smart Thermostat', 'THM-001', 'Programmable smart thermostat', 'Electronics', 149.99, 92.00, 50),
('Air Purifier', 'AP-001', 'HEPA air purifier for home', 'Home', 89.99, 55.00, 70),
('Humidifier Cool Mist', 'HUM-001', 'Ultrasonic cool mist humidifier', 'Home', 49.99, 28.00, 100),
('Essential Oil Diffuser', 'EOD-001', 'Aromatherapy essential oil diffuser', 'Home', 29.99, 15.00, 180),
('Smart Light Bulbs', 'SLB-001', 'Color changing smart bulbs 4-pack', 'Electronics', 39.99, 22.00, 160),
('Coffee Maker', 'CM-001', 'Programmable coffee maker 12-cup', 'Kitchen', 59.99, 36.00, 90),
('Blender High Speed', 'BL-001', 'Professional blender with multiple speeds', 'Kitchen', 79.99, 48.00, 70),
('Toaster 4-Slice', 'TST-001', 'Stainless steel 4-slice toaster', 'Kitchen', 44.99, 26.00, 100),
('Electric Kettle', 'EK-001', 'Fast-boiling electric kettle', 'Kitchen', 34.99, 19.00, 120),
('Food Processor', 'FP-001', '8-cup food processor', 'Kitchen', 69.99, 42.00, 60),
('Slow Cooker', 'SC-002', 'Programmable slow cooker 6-quart', 'Kitchen', 54.99, 32.00, 80),
('Air Fryer', 'AF-001', 'Digital air fryer 5.8-quart', 'Kitchen', 89.99, 55.00, 70),
('Instant Pot', 'IP-001', 'Multi-use pressure cooker', 'Kitchen', 99.99, 62.00, 60),
('Knife Set', 'KS-001', 'Professional knife set with block', 'Kitchen', 79.99, 45.00, 50),
('Cutting Board Set', 'CB-001', 'Bamboo cutting board set 3-piece', 'Kitchen', 24.99, 12.00, 200),
('Mixing Bowl Set', 'MB-001', 'Stainless steel mixing bowl set', 'Kitchen', 29.99, 15.00, 150),
('Measuring Cup Set', 'MC-002', 'Measuring cup and spoon set', 'Kitchen', 14.99, 7.00, 250),
('Kitchen Scale Digital', 'KSC-001', 'Digital kitchen scale with bowl', 'Kitchen', 19.99, 10.00, 180),
('Can Opener Electric', 'CO-001', 'Automatic electric can opener', 'Kitchen', 24.99, 13.00, 150),
('Vegetable Peeler Set', 'VP-001', 'Vegetable peeler set 3-piece', 'Kitchen', 9.99, 4.50, 300),
('Garlic Press', 'GP-001', 'Stainless steel garlic press', 'Kitchen', 12.99, 6.00, 250),
('Pizza Cutter', 'PC-002', 'Sharp stainless steel pizza cutter', 'Kitchen', 8.99, 4.00, 300),
('Wine Opener Set', 'WO-001', 'Wine opener and accessory set', 'Kitchen', 19.99, 9.50, 200),
('Vacuum Cleaner', 'VC-001', 'Bagless upright vacuum cleaner', 'Home', 129.99, 78.00, 50),
('Robot Vacuum', 'RV-001', 'Smart robot vacuum with app control', 'Home', 249.99, 155.00, 40),
('Steam Mop', 'SM-001', 'Electric steam mop for floors', 'Home', 69.99, 42.00, 70),
('Iron Steam', 'IS-001', 'Steam iron with auto shutoff', 'Home', 34.99, 19.00, 120),
('Ironing Board', 'IB-001', 'Adjustable height ironing board', 'Home', 39.99, 22.00, 80),
('Laundry Basket', 'LBS-001', 'Collapsible laundry basket 3-pack', 'Home', 29.99, 15.00, 150),
('Clothes Hangers', 'CH-001', 'Velvet clothes hangers 50-pack', 'Home', 19.99, 9.50, 200),
('Shoe Rack', 'SR-001', '4-tier shoe rack organizer', 'Home', 24.99, 13.00, 120),
('Storage Bins', 'SB-001', 'Plastic storage bins 6-pack', 'Home', 34.99, 18.00, 150),
('Trash Can', 'TC-001', 'Stainless steel trash can with lid', 'Home', 44.99, 26.00, 100),
('Toilet Brush Set', 'TB-001', 'Toilet brush and holder set', 'Home', 14.99, 7.00, 250),
('Shower Curtain', 'SHC-001', 'Waterproof fabric shower curtain', 'Home', 19.99, 9.50, 200),
('Bath Mat', 'BM-001', 'Non-slip memory foam bath mat', 'Home', 16.99, 8.50, 220),
('Towel Set', 'TS-001', 'Bath towel set 6-piece', 'Home', 39.99, 22.00, 130),
('Soap Dispenser Set', 'SDS-001', 'Bathroom soap dispenser set', 'Home', 22.99, 11.50, 180),
('Mirror Wall Mounted', 'MIR-001', 'LED wall mounted bathroom mirror', 'Home', 79.99, 48.00, 60),
('Toilet Paper Holder', 'TPH-001', 'Wall mounted toilet paper holder', 'Home', 12.99, 6.00, 300),
('Toothbrush Holder', 'TBH-001', 'Modern toothbrush holder set', 'Home', 14.99, 7.00, 250),
('Fitness Tracker', 'FT-001', 'Activity and sleep tracker watch', 'Fitness', 49.99, 28.00, 150),
('Yoga Mat', 'YM-001', 'Non-slip exercise yoga mat', 'Fitness', 24.99, 12.50, 200);

-- ============================================================================
-- GENERATE 500 ORDERS WITH ORDER ITEMS
-- ============================================================================

-- Create a temporary table to hold order data
CREATE TEMP TABLE temp_orders AS
SELECT 
    order_num,
    ((order_num % 100) + 1) as customer_id,
    ((order_num % 100) + 1) as shipping_address_id,
    ((order_num % 100) + 1) as payment_method_id,
    CASE (order_num % 5)
        WHEN 0 THEN 'pending'
        WHEN 1 THEN 'processing'
        WHEN 2 THEN 'shipped'
        WHEN 3 THEN 'delivered'
        ELSE 'processing'
    END as order_status,
    NOW() - INTERVAL '1 day' * (RANDOM() * 90)::INTEGER as order_date
FROM generate_series(1, 500) as order_num;

-- Insert orders
INSERT INTO orders (customer_id, shipping_address_id, payment_method_id, order_status, subtotal, tax, shipping_cost, total, order_date, created_at, updated_at)
SELECT 
    customer_id,
    shipping_address_id,
    payment_method_id,
    order_status,
    0, -- Will be updated after order items
    0, -- Will be updated after order items
    CASE 
        WHEN RANDOM() < 0.3 THEN 0 -- 30% free shipping
        ELSE ROUND((5 + RANDOM() * 15)::NUMERIC, 2) -- $5-20 shipping
    END as shipping_cost,
    0, -- Will be updated after order items
    order_date,
    order_date,
    order_date
FROM temp_orders;

-- Generate order items (1-5 items per order)
WITH order_items_data AS (
    SELECT 
        o.order_id,
        p.product_id,
        p.product_name,
        p.product_sku,
        (1 + (RANDOM() * 3)::INTEGER) as quantity, -- 1-4 items
        p.sell_price,
        o.order_date
    FROM orders o
    CROSS JOIN LATERAL (
        SELECT product_id, product_name, product_sku, sell_price
        FROM products
        ORDER BY RANDOM()
        LIMIT (1 + (RANDOM() * 4)::INTEGER) -- 1-5 different products per order
    ) p
)
INSERT INTO order_items (order_id, product_id, product_name, product_sku, quantity, unit_price, total_price, created_at)
SELECT 
    order_id,
    product_id,
    product_name,
    product_sku,
    quantity,
    sell_price as unit_price,
    sell_price * quantity as total_price, -- Correctly calculate total_price
    order_date
FROM order_items_data;

-- Update order totals based on order items
UPDATE orders o
SET 
    subtotal = (SELECT COALESCE(SUM(total_price), 0) FROM order_items WHERE order_id = o.order_id),
    tax = (SELECT COALESCE(SUM(total_price), 0) * 0.08 FROM order_items WHERE order_id = o.order_id),
    total = (SELECT COALESCE(SUM(total_price), 0) FROM order_items WHERE order_id = o.order_id) * 1.08 + o.shipping_cost;

-- Update shipped_date for shipped and delivered orders
UPDATE orders
SET shipped_date = order_date + INTERVAL '1 day' * (1 + RANDOM() * 3)::INTEGER
WHERE order_status IN ('shipped', 'delivered');

-- Update delivered_date for delivered orders
UPDATE orders
SET delivered_date = shipped_date + INTERVAL '1 day' * (2 + RANDOM() * 5)::INTEGER
WHERE order_status = 'delivered';

-- ============================================================================
-- GENERATE PAYMENT TRANSACTIONS FOR ALL ORDERS
-- ============================================================================
INSERT INTO payment_transactions (order_id, payment_method_id, transaction_status, transaction_amount, transaction_date, payment_gateway, created_at)
SELECT 
    order_id,
    payment_method_id,
    CASE 
        WHEN order_status IN ('delivered', 'shipped', 'processing') THEN 'completed'
        WHEN order_status = 'pending' THEN 
            CASE WHEN RANDOM() < 0.8 THEN 'pending' ELSE 'failed' END
        ELSE 'completed'
    END as transaction_status,
    total,
    order_date + INTERVAL '5 minutes',
    CASE (order_id % 3)
        WHEN 0 THEN 'Stripe'
        WHEN 1 THEN 'PayPal'
        ELSE 'Square'
    END,
    order_date + INTERVAL '5 minutes'
FROM orders;

-- Drop temporary table
DROP TABLE temp_orders;

-- ============================================================================
-- SUMMARY STATISTICS
-- ============================================================================
SELECT 'Data Generation Complete!' as status;
SELECT COUNT(*) as total_customers FROM customers;
SELECT COUNT(*) as total_products FROM products;
SELECT COUNT(*) as total_orders FROM orders;
SELECT COUNT(*) as total_order_items FROM order_items;
SELECT COUNT(*) as total_transactions FROM payment_transactions;
SELECT 
    order_status,
    COUNT(*) as count,
    ROUND(AVG(total)::NUMERIC, 2) as avg_order_value,
    ROUND(SUM(total)::NUMERIC, 2) as total_revenue
FROM orders
GROUP BY order_status
ORDER BY order_status;