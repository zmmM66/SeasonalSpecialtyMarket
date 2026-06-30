CREATE DATABASE IF NOT EXISTS seasonal_market DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE seasonal_market;

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    is_frozen BOOLEAN NOT NULL DEFAULT FALSE,
    regist_time DATETIME NOT NULL,
    balance DECIMAL(10,2) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(30) NOT NULL UNIQUE,
    category_description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Product (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(30) NOT NULL,
    product_description TEXT,
    origin VARCHAR(30),
    price DECIMAL(10,2) NOT NULL,
    sales_period_start DATETIME NOT NULL,
    sales_period_end DATETIME NOT NULL,
    product_create_time DATETIME NOT NULL,
    product_status ENUM('on_sale', 'off_sale', 'sold_out') NOT NULL,
    category_id INT NOT NULL,
    publisher_id INT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES Category(category_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (publisher_id) REFERENCES User(user_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `Order` (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    total_amount DECIMAL(10,2) NOT NULL,
    order_status ENUM('pending', 'paid', 'shipped', 'received', 'completed', 'cancelled', 'refunded') NOT NULL,
    order_create_time DATETIME NOT NULL,
    payment_time DATETIME,
    receive_time DATETIME,
    seller_received BOOLEAN NOT NULL DEFAULT FALSE,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS OrderItem (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    quantity INT NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES `Order`(order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS CartItem (
    cart_item_id INT AUTO_INCREMENT PRIMARY KEY,
    product_quantity INT NOT NULL CHECK (product_quantity > 0),
    added_time DATETIME NOT NULL,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    UNIQUE KEY uk_cart_item (user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Favorite (
    favorite_id INT AUTO_INCREMENT PRIMARY KEY,
    favorite_create_time DATETIME NOT NULL,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    UNIQUE KEY uk_favorite (user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Complaint (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('quality', 'service', 'delivery', 'other') NOT NULL,
    reason TEXT NOT NULL,
    seller_reply TEXT,
    seller_reply_time DATETIME,
    complaint_status ENUM('pending', 'seller_replied', 'processed', 'cancelled') NOT NULL,
    require_refund BOOLEAN NOT NULL DEFAULT FALSE,
    refund_amount DECIMAL(10,2),
    handle_opinion TEXT,
    handle_time DATETIME,
    user_id INT NOT NULL,
    order_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (order_id) REFERENCES `Order`(order_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_product_name ON Product(product_name);

CREATE VIEW vw_product_details AS
SELECT 
    p.product_id,
    p.product_name,
    p.product_description,
    c.category_name,
    p.origin,
    p.price,
    p.sales_period_start,
    p.sales_period_end,
    u.username AS publisher_name,
    p.product_status
FROM Product p
JOIN Category c ON p.category_id = c.category_id
JOIN User u ON p.publisher_id = u.user_id;

DELIMITER //

CREATE TRIGGER trg_update_product_status
BEFORE UPDATE ON Product
FOR EACH ROW
BEGIN
    IF NEW.sales_period_end < CURDATE() THEN
        SET NEW.product_status = 'off_sale';
    END IF;
END //

CREATE PROCEDURE sp_handle_complaint(
    IN p_complaint_id INT,
    IN p_handle_opinion TEXT,
    IN p_require_refund BOOLEAN,
    IN p_refund_amount DECIMAL(10,2)
)
BEGIN
    DECLARE v_order_id INT;
    DECLARE v_user_id INT;
    DECLARE v_seller_id INT;
    
    SELECT order_id, user_id INTO v_order_id, v_user_id
    FROM Complaint WHERE complaint_id = p_complaint_id;
    
    SELECT p.publisher_id INTO v_seller_id
    FROM `Order` o
    JOIN OrderItem oi ON o.order_id = oi.order_id
    JOIN Product p ON oi.product_id = p.product_id
    WHERE o.order_id = v_order_id LIMIT 1;
    
    UPDATE Complaint 
    SET complaint_status = 'processed',
        handle_opinion = p_handle_opinion,
        require_refund = p_require_refund,
        refund_amount = p_refund_amount,
        handle_time = NOW()
    WHERE complaint_id = p_complaint_id;
    
    IF p_require_refund THEN
        UPDATE User SET balance = balance + p_refund_amount WHERE user_id = v_user_id;
        UPDATE User SET balance = balance - p_refund_amount WHERE user_id = v_seller_id;
        UPDATE `Order` SET order_status = 'refunded' WHERE order_id = v_order_id;
    END IF;
END //

CREATE PROCEDURE sp_confirm_receive(
    IN p_order_id INT
)
BEGIN
    DECLARE v_total_amount DECIMAL(10,2);
    DECLARE v_seller_id INT;
    
    SELECT total_amount INTO v_total_amount FROM `Order` WHERE order_id = p_order_id;
    
    SELECT p.publisher_id INTO v_seller_id
    FROM OrderItem oi
    JOIN Product p ON oi.product_id = p.product_id
    WHERE oi.order_id = p_order_id LIMIT 1;
    
    UPDATE `Order` 
    SET order_status = 'completed',
        receive_time = NOW(),
        seller_received = TRUE
    WHERE order_id = p_order_id;
    
    UPDATE User SET balance = balance + v_total_amount WHERE user_id = v_seller_id;
END //

DELIMITER ;
