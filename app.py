from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'laundry_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@localhost/laundry_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ─── MODELS ───────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='customer')
    ip_address = db.Column(db.String(50))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='customer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    price_per_piece = db.Column(db.Float, default=0)
    price_per_kg = db.Column(db.Float, default=0)
    icon = db.Column(db.String(50), default='👕')
    is_active = db.Column(db.Boolean, default=True)


class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    quantity = db.Column(db.Float, default=1)
    pricing_type = db.Column(db.String(10), default='piece')
    service = db.relationship('Service')


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(30), default='Received')
    pickup_date = db.Column(db.DateTime)
    delivery_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    customer_ip = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    quantity = db.Column(db.Float)
    pricing_type = db.Column(db.String(10))
    unit_price = db.Column(db.Float)
    subtotal = db.Column(db.Float)
    service = db.relationship('Service')


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required!', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_cart_count():
    if current_user.is_authenticated:
        return CartItem.query.filter_by(user_id=current_user.id).count()
    return 0

app.jinja_env.globals['get_cart_count'] = get_cart_count

# ─── AUTH ROUTES ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    services = Service.query.filter_by(is_active=True).all()
    return render_template('index.html', services=services)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        user = User(name=name, email=email, phone=phone, address=address,
                    ip_address=get_client_ip())
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Welcome, {name}! Account created successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            user.ip_address = get_client_ip()
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('admin_dashboard') if user.role == 'admin' else url_for('index'))
        flash('Invalid email or password!', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# ─── SERVICES ─────────────────────────────────────────────────────────────────

@app.route('/services')
def services():
    all_services = Service.query.filter_by(is_active=True).all()
    return render_template('services.html', services=all_services)

# ─── CART ─────────────────────────────────────────────────────────────────────

@app.route('/cart')
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = 0
    for item in items:
        price = item.service.price_per_kg if item.pricing_type == 'kg' else item.service.price_per_piece
        item.subtotal = price * item.quantity
        total += item.subtotal
    return render_template('cart.html', items=items, total=total)

@app.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    service_id = int(request.form['service_id'])
    quantity = float(request.form.get('quantity', 1))
    pricing_type = request.form.get('pricing_type', 'piece')
    existing = CartItem.query.filter_by(user_id=current_user.id, service_id=service_id).first()
    if existing:
        existing.quantity += quantity
    else:
        item = CartItem(user_id=current_user.id, service_id=service_id,
                        quantity=quantity, pricing_type=pricing_type)
        db.session.add(item)
    db.session.commit()
    flash('Item added to cart!', 'success')
    return redirect(url_for('services'))

@app.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('cart'))

@app.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    item_id = int(request.form['item_id'])
    quantity = float(request.form['quantity'])
    item = CartItem.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        if quantity <= 0:
            db.session.delete(item)
        else:
            item.quantity = quantity
        db.session.commit()
    return redirect(url_for('cart'))

# ─── CHECKOUT / ORDERS ────────────────────────────────────────────────────────

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Cart is empty!', 'warning')
        return redirect(url_for('services'))

    if request.method == 'POST':
        pickup_date = datetime.strptime(request.form['pickup_date'], '%Y-%m-%d')
        delivery_date = datetime.strptime(request.form['delivery_date'], '%Y-%m-%d')
        notes = request.form.get('notes', '')
        total = 0
        order = Order(
            user_id=current_user.id,
            pickup_date=pickup_date,
            delivery_date=delivery_date,
            notes=notes,
            customer_ip=get_client_ip()
        )
        db.session.add(order)
        db.session.flush()
        for cart_item in items:
            price = cart_item.service.price_per_kg if cart_item.pricing_type == 'kg' else cart_item.service.price_per_piece
            subtotal = price * cart_item.quantity
            total += subtotal
            oi = OrderItem(order_id=order.id, service_id=cart_item.service_id,
                           quantity=cart_item.quantity, pricing_type=cart_item.pricing_type,
                           unit_price=price, subtotal=subtotal)
            db.session.add(oi)
        order.total_amount = total
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash(f'Order #{order.id} placed successfully!', 'success')
        return redirect(url_for('my_orders'))

    total = sum(
        (i.service.price_per_kg if i.pricing_type == 'kg' else i.service.price_per_piece) * i.quantity
        for i in items
    )
    return render_template('checkout.html', items=items, total=total,
                           min_pickup=datetime.now().strftime('%Y-%m-%d'),
                           min_delivery=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))

@app.route('/orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('my_orders'))
    return render_template('order_detail.html', order=order)

# ─── ADMIN ────────────────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    pending_orders = Order.query.filter(Order.status.notin_(['Delivered'])).count()
    total_customers = User.query.filter_by(role='customer').count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    customers = User.query.filter_by(role='customer').order_by(User.last_login.desc()).all()
    status_counts = {}
    for s in ['Received', 'Picked Up', 'Washing', 'Drying', 'Ready', 'Delivered']:
        status_counts[s] = Order.query.filter_by(status=s).count()
    return render_template('admin/dashboard.html',
                           total_orders=total_orders,
                           total_revenue=total_revenue,
                           pending_orders=pending_orders,
                           total_customers=total_customers,
                           recent_orders=recent_orders,
                           customers=customers,
                           status_counts=status_counts)

@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    status_filter = request.args.get('status', '')
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    orders = query.order_by(Order.created_at.desc()).all()
    statuses = ['Received', 'Picked Up', 'Washing', 'Drying', 'Ready', 'Delivered']
    return render_template('admin/orders.html', orders=orders, statuses=statuses, current_status=status_filter)

@app.route('/admin/orders/<int:order_id>/update_status', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = request.form['status']
    order.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f'Order #{order_id} status updated to {order.status}', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/customers')
@login_required
@admin_required
def admin_customers():
    customers = User.query.filter_by(role='customer').order_by(User.created_at.desc()).all()
    return render_template('admin/customers.html', customers=customers)

@app.route('/admin/services', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_services():
    if request.method == 'POST':
        s = Service(
            name=request.form['name'],
            category=request.form['category'],
            description=request.form['description'],
            price_per_piece=float(request.form.get('price_per_piece', 0)),
            price_per_kg=float(request.form.get('price_per_kg', 0)),
            icon=request.form.get('icon', '👕')
        )
        db.session.add(s)
        db.session.commit()
        flash('Service added!', 'success')
    services = Service.query.all()
    return render_template('admin/services.html', services=services)

@app.route('/admin/services/<int:sid>/toggle')
@login_required
@admin_required
def toggle_service(sid):
    s = Service.query.get_or_404(sid)
    s.is_active = not s.is_active
    db.session.commit()
    return redirect(url_for('admin_services'))

# ─── SEED DATA ────────────────────────────────────────────────────────────────

def seed_data():
    if not User.query.filter_by(email='admin@laundry.com').first():
        admin = User(name='Admin', email='admin@laundry.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

    if Service.query.count() == 0:
        services = [
            Service(name='Shirt Wash & Iron', category='wash_iron', description='Full wash and press for shirts', price_per_piece=40, icon='👔'),
            Service(name='Trouser Wash & Iron', category='wash_iron', description='Wash and crease for trousers', price_per_piece=50, icon='👖'),
            Service(name='Saree Dry Clean', category='dry_clean', description='Delicate dry cleaning for sarees', price_per_piece=150, icon='🥻'),
            Service(name='Bed Sheet Wash', category='wash', description='Wash & dry bed sheets', price_per_piece=80, icon='🛏️'),
            Service(name='Bulk Wash (per kg)', category='wash', description='Machine wash per kilogram', price_per_kg=60, icon='⚖️'),
            Service(name='Jacket Dry Clean', category='dry_clean', description='Professional jacket cleaning', price_per_piece=200, icon='🧥'),
            Service(name='Woolen Sweater', category='dry_clean', description='Gentle wool care', price_per_piece=120, icon='🧶'),
            Service(name='Express Iron Only', category='iron', description='Quick press service', price_per_piece=20, icon='🔥'),
        ]
        db.session.add_all(services)
    db.session.commit()

# ─── INIT ─────────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
