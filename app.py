from flask import Flask, request, jsonify, session
from flask_cors import CORS
from db import get_connection
from mysql.connector import Error
import functools
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'seasonal_market_secret_key_2026')
app.json.ensure_ascii = False
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)
CORS(app, supports_credentials=True)

class DatabaseUnavailable(Exception):
    pass

def get_request_data():
    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict()
    return data or {}

def to_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).lower() in ('true', '1', 'yes', 'on')

def to_int(value, default=None):
    try:
        if value is None or value == '':
            return default
        return int(value)
    except (TypeError, ValueError):
        return default

def to_float(value, default=None):
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (TypeError, ValueError):
        return default

def optional_text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None

def get_db_connection():
    conn = get_connection()
    if not conn:
        raise DatabaseUnavailable()
    return conn

@app.errorhandler(DatabaseUnavailable)
def handle_database_unavailable(_error):
    return jsonify({'error': '数据库连接失败，请确认 MySQL 服务已启动并监听 localhost:3306'}), 503

@app.errorhandler(Error)
def handle_mysql_error(error):
    return jsonify({'error': f'数据库操作失败: {error}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    conn = get_connection()
    if not conn:
        return jsonify({'status': 'degraded', 'database': 'unavailable'}), 503
    conn.close()
    return jsonify({'status': 'ok', 'database': 'connected'}), 200

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '请先登录'}), 401
        if not session.get('is_admin'):
            return jsonify({'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = get_request_data()
    username = optional_text(data.get('username'))
    password = optional_text(data.get('password'))
    email = optional_text(data.get('email'))
    phone = optional_text(data.get('phone'))
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM User WHERE username = %s", (username,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'error': '用户名已存在'}), 400
    
    cursor.execute(
        "INSERT INTO User (username, password, is_admin, email, phone, is_frozen, regist_time, balance) VALUES (%s, %s, FALSE, %s, %s, FALSE, NOW(), 0)",
        (username, password, email, phone)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': '注册成功'}), 200

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = get_request_data()
    username = optional_text(data.get('username'))
    password = optional_text(data.get('password'))
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM User WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        return jsonify({'error': '用户名或密码错误'}), 401
    
    if user['is_frozen']:
        return jsonify({'error': '账户已被冻结'}), 403
    
    session['user_id'] = user['user_id']
    session['username'] = user['username']
    session['is_admin'] = user['is_admin']
    
    return jsonify({
        'message': '登录成功',
        'user': {
            'user_id': user['user_id'],
            'username': user['username'],
            'is_admin': user['is_admin'],
            'balance': float(user['balance'])
        }
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': '已退出登录'}), 200

@app.route('/api/auth/user', methods=['GET'])
@login_required
def get_current_user():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, username, is_admin, balance, email, phone FROM User WHERE user_id = %s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    user['balance'] = float(user['balance'])
    return jsonify({'user': user}), 200

@app.route('/api/products', methods=['GET'])
def get_products():
    category_id = request.args.get('category_id')
    search = request.args.get('search')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT p.*, c.category_name, u.username as publisher_name 
        FROM Product p 
        JOIN Category c ON p.category_id = c.category_id 
        JOIN User u ON p.publisher_id = u.user_id 
        WHERE p.product_status = 'on_sale'
    """
    params = []
    
    if category_id:
        query += " AND p.category_id = %s"
        params.append(category_id)
    
    if search:
        query += " AND (p.product_name LIKE %s OR p.product_description LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    cursor.execute(query, params)
    products = cursor.fetchall()
    
    for p in products:
        p['price'] = float(p['price'])
        p['sales_period_start'] = str(p['sales_period_start'])[:10]
        p['sales_period_end'] = str(p['sales_period_end'])[:10]
        p['product_create_time'] = str(p['product_create_time'])[:19]
    
    cursor.close()
    conn.close()
    
    return jsonify({'products': products}), 200

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, c.category_name, u.username as publisher_name 
        FROM Product p 
        JOIN Category c ON p.category_id = c.category_id 
        JOIN User u ON p.publisher_id = u.user_id 
        WHERE p.product_id = %s
    """, (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not product:
        return jsonify({'error': '商品不存在'}), 404
    
    product['price'] = float(product['price'])
    product['sales_period_start'] = str(product['sales_period_start'])[:10]
    product['sales_period_end'] = str(product['sales_period_end'])[:10]
    
    return jsonify({'product': product}), 200

@app.route('/api/products', methods=['POST'])
@login_required
def create_product():
    data = get_request_data()
    name = optional_text(data.get('name'))
    description = optional_text(data.get('description'))
    category_id = to_int(data.get('category_id'))
    origin = optional_text(data.get('origin'))
    price = to_float(data.get('price'))
    sales_period_start = optional_text(data.get('sales_period_start'))
    sales_period_end = optional_text(data.get('sales_period_end'))
    
    if not name or not price or not category_id or not sales_period_start or not sales_period_end:
        return jsonify({'error': '请填写完整信息'}), 400
    if price <= 0:
        return jsonify({'error': '商品价格必须大于0'}), 400
    if sales_period_start > sales_period_end:
        return jsonify({'error': '销售期结束日期不能早于开始日期'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Product (product_name, product_description, origin, price, sales_period_start, sales_period_end, product_create_time, product_status, category_id, publisher_id)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), 'on_sale', %s, %s)
    """, (name, description, origin, price, sales_period_start, sales_period_end, category_id, session['user_id']))
    conn.commit()
    product_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    return jsonify({'message': '商品发布成功', 'product_id': product_id}), 200

@app.route('/api/my/products', methods=['GET'])
@login_required
def get_my_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, c.category_name
        FROM Product p
        JOIN Category c ON p.category_id = c.category_id
        WHERE p.publisher_id = %s
        ORDER BY p.product_create_time DESC
    """, (session['user_id'],))
    products = cursor.fetchall()

    for p in products:
        p['price'] = float(p['price'])
        p['sales_period_start'] = str(p['sales_period_start'])[:10]
        p['sales_period_end'] = str(p['sales_period_end'])[:10]
        p['product_create_time'] = str(p['product_create_time'])[:19]

    cursor.close()
    conn.close()

    return jsonify({'products': products}), 200

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT publisher_id FROM Product WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        conn.close()
        return jsonify({'error': '商品不存在'}), 404

    if product['publisher_id'] != session['user_id'] and not session.get('is_admin'):
        cursor.close()
        conn.close()
        return jsonify({'error': '只能删除自己发布的商品'}), 403

    cursor.execute("UPDATE Product SET product_status = 'off_sale' WHERE product_id = %s", (product_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': '商品已下架'}), 200

@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Category")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify({'categories': categories}), 200

@app.route('/api/cart', methods=['GET'])
@login_required
def get_cart():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT ci.*, p.product_name, p.price, p.origin, p.product_status
        FROM CartItem ci
        JOIN Product p ON ci.product_id = p.product_id
        WHERE ci.user_id = %s
    """, (session['user_id'],))
    cart_items = cursor.fetchall()
    
    total = 0
    for item in cart_items:
        item['price'] = float(item['price'])
        item['subtotal'] = item['price'] * item['product_quantity']
        total += item['subtotal']
        item['added_time'] = str(item['added_time'])[:19]
    
    cursor.close()
    conn.close()
    
    return jsonify({'cart_items': cart_items, 'total': total}), 200

@app.route('/api/cart', methods=['POST'])
@login_required
def add_to_cart():
    data = get_request_data()
    product_id = to_int(data.get('product_id'))
    quantity = to_int(data.get('quantity'), 1)

    if not product_id:
        return jsonify({'error': '商品ID不能为空'}), 400
    if not quantity or quantity <= 0:
        return jsonify({'error': '数量必须大于0'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT product_status FROM Product WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()
    if not product:
        cursor.close()
        conn.close()
        return jsonify({'error': '商品不存在'}), 404
    if product['product_status'] != 'on_sale':
        cursor.close()
        conn.close()
        return jsonify({'error': '商品当前不可购买'}), 400
    
    cursor.execute("SELECT * FROM CartItem WHERE user_id = %s AND product_id = %s", (session['user_id'], product_id))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("UPDATE CartItem SET product_quantity = product_quantity + %s WHERE cart_item_id = %s", (quantity, existing['cart_item_id']))
    else:
        cursor.execute("INSERT INTO CartItem (product_quantity, added_time, user_id, product_id) VALUES (%s, NOW(), %s, %s)", (quantity, session['user_id'], product_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': '已加入购物车'}), 200

@app.route('/api/cart/<int:cart_item_id>', methods=['PUT'])
@login_required
def update_cart_item(cart_item_id):
    data = get_request_data()
    quantity = to_int(data.get('quantity'))
    
    if not quantity or quantity <= 0:
        return jsonify({'error': '数量必须大于0'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE CartItem SET product_quantity = %s WHERE cart_item_id = %s AND user_id = %s", (quantity, cart_item_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': '购物车已更新'}), 200

@app.route('/api/cart/<int:cart_item_id>', methods=['DELETE'])
@login_required
def remove_cart_item(cart_item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM CartItem WHERE cart_item_id = %s AND user_id = %s", (cart_item_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': '已从购物车移除'}), 200

@app.route('/api/cart/clear', methods=['DELETE'])
@login_required
def clear_cart():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM CartItem WHERE user_id = %s", (session['user_id'],))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': '购物车已清空'}), 200

@app.route('/api/orders', methods=['GET'])
@login_required
def get_orders():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM `Order` WHERE user_id = %s ORDER BY order_create_time DESC", (session['user_id'],))
    orders = cursor.fetchall()
    
    for order in orders:
        order['total_amount'] = float(order['total_amount'])
        order['order_create_time'] = str(order['order_create_time'])[:19]
        order['payment_time'] = str(order['payment_time'])[:19] if order['payment_time'] else None
        order['receive_time'] = str(order['receive_time'])[:19] if order['receive_time'] else None
    
    cursor.close()
    conn.close()
    
    return jsonify({'orders': orders}), 200

@app.route('/api/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM `Order` WHERE order_id = %s AND user_id = %s", (order_id, session['user_id']))
    order = cursor.fetchone()
    
    if not order:
        cursor.close()
        conn.close()
        return jsonify({'error': '订单不存在'}), 404
    
    cursor.execute("""
        SELECT oi.*, p.product_name, p.origin
        FROM OrderItem oi
        JOIN Product p ON oi.product_id = p.product_id
        WHERE oi.order_id = %s
    """, (order_id,))
    items = cursor.fetchall()
    
    order['total_amount'] = float(order['total_amount'])
    order['order_create_time'] = str(order['order_create_time'])[:19]
    
    for item in items:
        item['total_price'] = float(item['total_price'])
        item['price'] = item['total_price'] / item['quantity']
    
    order['items'] = items
    
    cursor.close()
    conn.close()
    
    return jsonify({'order': order}), 200

@app.route('/api/orders/checkout', methods=['POST'])
@login_required
def checkout():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT balance FROM User WHERE user_id = %s", (session['user_id'],))
    user = cursor.fetchone()
    balance = float(user['balance'])
    
    cursor.execute("""
        SELECT ci.*, p.price, p.product_status, p.publisher_id
        FROM CartItem ci
        JOIN Product p ON ci.product_id = p.product_id
        WHERE ci.user_id = %s
    """, (session['user_id'],))
    cart_items = cursor.fetchall()
    
    if not cart_items:
        cursor.close()
        conn.close()
        return jsonify({'error': '购物车为空'}), 400
    
    unavailable_items = [item for item in cart_items if item['product_status'] != 'on_sale']
    if unavailable_items:
        cursor.close()
        conn.close()
        return jsonify({'error': '购物车包含已下架商品，请先移除后再结算'}), 400
    
    seller_ids = {item['publisher_id'] for item in cart_items}
    if len(seller_ids) > 1:
        cursor.close()
        conn.close()
        return jsonify({'error': '一次订单只能购买同一卖家的商品，请分开结算'}), 400
    
    total = sum(float(item['price']) * item['product_quantity'] for item in cart_items)
    
    if balance < total:
        cursor.close()
        conn.close()
        return jsonify({'error': '余额不足，请先充值'}), 400
    
    cursor.execute(
        "INSERT INTO `Order` (total_amount, order_status, order_create_time, user_id, payment_time) VALUES (%s, 'paid', NOW(), %s, NOW())",
        (total, session['user_id'])
    )
    order_id = cursor.lastrowid
    
    for item in cart_items:
        cursor.execute(
            "INSERT INTO OrderItem (quantity, total_price, order_id, product_id) VALUES (%s, %s, %s, %s)",
            (item['product_quantity'], float(item['price']) * item['product_quantity'], order_id, item['product_id'])
        )
    
    cursor.execute("DELETE FROM CartItem WHERE user_id = %s", (session['user_id'],))
    cursor.execute("UPDATE User SET balance = balance - %s WHERE user_id = %s", (total, session['user_id']))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': '下单成功', 'order_id': order_id, 'total': total}), 200

@app.route('/api/orders/<int:order_id>/confirm', methods=['POST'])
@login_required
def confirm_receive(order_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM `Order` WHERE order_id = %s AND user_id = %s", (order_id, session['user_id']))
    order = cursor.fetchone()
    
    if not order:
        cursor.close()
        conn.close()
        return jsonify({'error': '订单不存在'}), 404
    
    if order['order_status'] not in ['paid', 'shipped']:
        cursor.close()
        conn.close()
        return jsonify({'error': '订单状态不允许确认收货'}), 400
    
    cursor.callproc('sp_confirm_receive', (order_id,))
    conn.commit()
    
    cursor.execute("SELECT balance FROM User WHERE user_id = %s", (session['user_id'],))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return jsonify({'message': '确认收货成功', 'balance': float(user['balance'])}), 200

@app.route('/api/favorites', methods=['GET'])
@login_required
def get_favorites():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT f.*, p.product_name, p.price, p.origin, p.product_status
        FROM Favorite f
        JOIN Product p ON f.product_id = p.product_id
        WHERE f.user_id = %s
    """, (session['user_id'],))
    favorites = cursor.fetchall()
    
    for fav in favorites:
        fav['price'] = float(fav['price'])
        fav['favorite_create_time'] = str(fav['favorite_create_time'])[:19]
    
    cursor.close()
    conn.close()
    
    return jsonify({'favorites': favorites}), 200

@app.route('/api/favorites', methods=['POST'])
@login_required
def add_favorite():
    data = get_request_data()
    product_id = to_int(data.get('product_id'))
    
    if not product_id:
        return jsonify({'error': '商品ID不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT product_id FROM Product WHERE product_id = %s", (product_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'error': '商品不存在'}), 404
    
    cursor.execute("SELECT * FROM Favorite WHERE user_id = %s AND product_id = %s", (session['user_id'], product_id))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'error': '已在收藏中'}), 400
    
    cursor.execute("INSERT INTO Favorite (favorite_create_time, user_id, product_id) VALUES (NOW(), %s, %s)", (session['user_id'], product_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': '已加入收藏'}), 200

@app.route('/api/favorites/<int:favorite_id>', methods=['DELETE'])
@login_required
def remove_favorite(favorite_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Favorite WHERE favorite_id = %s AND user_id = %s", (favorite_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': '已取消收藏'}), 200

@app.route('/api/complaints', methods=['GET'])
@login_required
def get_complaints():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if session.get('is_admin'):
        cursor.execute("""
            SELECT c.*, u.username, o.total_amount
            FROM Complaint c
            JOIN User u ON c.user_id = u.user_id
            JOIN `Order` o ON c.order_id = o.order_id
            ORDER BY c.complaint_status, c.complaint_id DESC
        """)
    else:
        cursor.execute("SELECT * FROM Complaint WHERE user_id = %s ORDER BY complaint_id DESC", (session['user_id'],))
    
    complaints = cursor.fetchall()
    
    for comp in complaints:
        comp['handle_time'] = str(comp['handle_time'])[:19] if comp['handle_time'] else None
        if 'total_amount' in comp:
            comp['total_amount'] = float(comp['total_amount'])
    
    cursor.close()
    conn.close()
    
    return jsonify({'complaints': complaints}), 200

@app.route('/api/complaints', methods=['POST'])
@login_required
def create_complaint():
    data = get_request_data()
    order_id = to_int(data.get('order_id'))
    type_ = optional_text(data.get('type'))
    reason = optional_text(data.get('reason'))
    
    if not order_id or type_ not in ('quality', 'service', 'delivery', 'other') or not reason:
        return jsonify({'error': '请填写有效的投诉信息'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT order_id FROM `Order` WHERE order_id = %s AND user_id = %s", (order_id, session['user_id']))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'error': '只能投诉自己的订单'}), 403

    cursor.execute(
        "INSERT INTO Complaint (type, reason, complaint_status, user_id, order_id) VALUES (%s, %s, 'pending', %s, %s)",
        (type_, reason, session['user_id'], order_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': '投诉提交成功'}), 200

@app.route('/api/complaints/<int:complaint_id>', methods=['PUT'])
@admin_required
def handle_complaint(complaint_id):
    data = get_request_data()
    opinion = optional_text(data.get('opinion'))
    require_refund = to_bool(data.get('require_refund'), False)
    refund_amount = to_float(data.get('refund_amount'), 0)
    
    if not opinion:
        return jsonify({'error': '处理意见不能为空'}), 400
    if require_refund and refund_amount <= 0:
        return jsonify({'error': '退款金额必须大于0'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.callproc('sp_handle_complaint', (complaint_id, opinion, require_refund, refund_amount))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': '投诉处理成功'}), 200

@app.route('/api/user/recharge', methods=['POST'])
@login_required
def recharge():
    data = get_request_data()
    amount = to_float(data.get('amount'), 0)
    
    if amount <= 0:
        return jsonify({'error': '充值金额必须大于0'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE User SET balance = balance + %s WHERE user_id = %s", (amount, session['user_id']))
    conn.commit()
    
    cursor.execute("SELECT balance FROM User WHERE user_id = %s", (session['user_id'],))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return jsonify({'message': '充值成功', 'balance': float(user[0])}), 200

@app.route('/api/seller/orders', methods=['GET'])
@login_required
def seller_get_orders():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT o.*, u.username AS buyer_name
        FROM `Order` o
        JOIN User u ON o.user_id = u.user_id
        JOIN OrderItem oi ON o.order_id = oi.order_id
        JOIN Product p ON oi.product_id = p.product_id
        WHERE p.publisher_id = %s
        ORDER BY o.order_create_time DESC
    """, (session['user_id'],))
    orders = cursor.fetchall()

    for order in orders:
        order['total_amount'] = float(order['total_amount'])
        order['order_create_time'] = str(order['order_create_time'])[:19]
        order['payment_time'] = str(order['payment_time'])[:19] if order['payment_time'] else None
        order['receive_time'] = str(order['receive_time'])[:19] if order['receive_time'] else None
        cursor.execute("""
            SELECT oi.*, p.product_name, p.origin
            FROM OrderItem oi
            JOIN Product p ON oi.product_id = p.product_id
            WHERE oi.order_id = %s AND p.publisher_id = %s
        """, (order['order_id'], session['user_id']))
        items = cursor.fetchall()
        for item in items:
            item['total_price'] = float(item['total_price'])
            item['price'] = item['total_price'] / item['quantity']
        order['items'] = items

    cursor.close()
    conn.close()

    return jsonify({'orders': orders}), 200

@app.route('/api/seller/orders/<int:order_id>/ship', methods=['POST'])
@login_required
def seller_ship_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT o.*
        FROM `Order` o
        JOIN OrderItem oi ON o.order_id = oi.order_id
        JOIN Product p ON oi.product_id = p.product_id
        WHERE o.order_id = %s AND p.publisher_id = %s
    """, (order_id, session['user_id']))
    order = cursor.fetchone()

    if not order:
        cursor.close()
        conn.close()
        return jsonify({'error': '订单不存在或不属于当前卖家'}), 404

    if order['order_status'] != 'paid':
        cursor.close()
        conn.close()
        return jsonify({'error': '只有已支付订单可以发货'}), 400

    cursor.execute("UPDATE `Order` SET order_status = 'shipped' WHERE order_id = %s", (order_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': '订单已发货'}), 200

@app.route('/api/seller/complaints', methods=['GET'])
@login_required
def seller_get_complaints():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.*, u.username AS buyer_name, o.total_amount, o.order_status
        FROM Complaint c
        JOIN `Order` o ON c.order_id = o.order_id
        JOIN User u ON c.user_id = u.user_id
        WHERE EXISTS (
            SELECT 1
            FROM OrderItem oi
            JOIN Product p ON oi.product_id = p.product_id
            WHERE oi.order_id = c.order_id AND p.publisher_id = %s
        )
        ORDER BY c.complaint_status, c.complaint_id DESC
    """, (session['user_id'],))
    complaints = cursor.fetchall()

    for comp in complaints:
        comp['total_amount'] = float(comp['total_amount'])
        comp['seller_reply_time'] = str(comp['seller_reply_time'])[:19] if comp['seller_reply_time'] else None
        comp['handle_time'] = str(comp['handle_time'])[:19] if comp['handle_time'] else None
        cursor.execute("""
            SELECT DISTINCT p.product_name
            FROM OrderItem oi
            JOIN Product p ON oi.product_id = p.product_id
            WHERE oi.order_id = %s AND p.publisher_id = %s
        """, (comp['order_id'], session['user_id']))
        comp['product_names'] = [row['product_name'] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return jsonify({'complaints': complaints}), 200

@app.route('/api/seller/complaints/<int:complaint_id>/reply', methods=['PUT'])
@login_required
def seller_reply_complaint(complaint_id):
    data = get_request_data()
    reply = optional_text(data.get('reply'))

    if not reply:
        return jsonify({'error': '回复内容不能为空'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.complaint_status
        FROM Complaint c
        WHERE c.complaint_id = %s
          AND EXISTS (
              SELECT 1
              FROM OrderItem oi
              JOIN Product p ON oi.product_id = p.product_id
              WHERE oi.order_id = c.order_id AND p.publisher_id = %s
          )
    """, (complaint_id, session['user_id']))
    complaint = cursor.fetchone()

    if not complaint:
        cursor.close()
        conn.close()
        return jsonify({'error': '投诉不存在或不属于当前卖家'}), 404

    if complaint['complaint_status'] in ('processed', 'cancelled'):
        cursor.close()
        conn.close()
        return jsonify({'error': '该投诉已结束，不能回复'}), 400

    cursor.execute("""
        UPDATE Complaint
        SET seller_reply = %s,
            seller_reply_time = NOW(),
            complaint_status = 'seller_replied'
        WHERE complaint_id = %s
    """, (reply, complaint_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': '卖家回复已提交'}), 200

@app.route('/api/admin/products', methods=['GET'])
@admin_required
def admin_get_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, c.category_name, u.username as publisher_name
        FROM Product p
        JOIN Category c ON p.category_id = c.category_id
        JOIN User u ON p.publisher_id = u.user_id
    """)
    products = cursor.fetchall()
    
    for p in products:
        p['price'] = float(p['price'])
        p['sales_period_start'] = str(p['sales_period_start'])[:10]
        p['sales_period_end'] = str(p['sales_period_end'])[:10]
    
    cursor.close()
    conn.close()
    
    return jsonify({'products': products}), 200

@app.route('/api/admin/products/<int:product_id>', methods=['DELETE'])
@admin_required
def admin_delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Product SET product_status = 'off_sale' WHERE product_id = %s", (product_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': '商品已下架'}), 200

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, username, email, phone, is_admin, is_frozen, balance, regist_time FROM User")
    users = cursor.fetchall()
    
    for user in users:
        user['balance'] = float(user['balance'])
        user['regist_time'] = str(user['regist_time'])[:19]
    
    cursor.close()
    conn.close()
    
    return jsonify({'users': users}), 200

@app.route('/api/admin/users/<int:user_id>/freeze', methods=['POST'])
@admin_required
def admin_freeze_user(user_id):
    data = get_request_data()
    freeze = to_bool(data.get('freeze'), True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE User SET is_frozen = %s WHERE user_id = %s", (freeze, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    action = '冻结' if freeze else '解冻'
    return jsonify({'message': f'用户已{action}'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
