# 🧺 LaundryPro — Laundry Management System

A full-featured Python Flask web application for managing laundry services.

## Features
- ✅ Customer Registration & Login
- ✅ Service Catalog with Cart System
- ✅ Order Placement & Tracking (6-stage status)
- ✅ Admin Dashboard with Stats
- ✅ Customer IP Address Tracking (visible in Admin)
- ✅ Manage Services (Add/Enable/Disable)
- ✅ MySQL Database

## Setup Instructions

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup MySQL Database
```bash
mysql -u root -p -e "CREATE DATABASE laundry_db;"
```

### 3. Update MySQL credentials in app.py
Edit line in app.py:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:YOUR_PASSWORD@localhost/laundry_db'
```

### 4. Run the app
```bash
python app.py
```

### 5. Open browser
```
http://localhost:5000
```

## Default Admin Login
- **Email:** admin@laundry.com
- **Password:** admin123

## Project Structure
```
laundry_app/
├── app.py                  # Main Flask app (routes, models, logic)
├── requirements.txt        # Python dependencies
├── setup_db.sql           # MySQL setup
└── templates/
    ├── base.html          # Base layout with navbar
    ├── index.html         # Homepage
    ├── services.html      # Services catalog + Add to Cart
    ├── cart.html          # Cart page
    ├── checkout.html      # Checkout form
    ├── my_orders.html     # Customer order history
    ├── order_detail.html  # Single order with status tracker
    ├── login.html         # Login page
    ├── register.html      # Register page
    └── admin/
        ├── dashboard.html # Admin overview with IP log
        ├── orders.html    # Manage all orders + status update
        ├── customers.html # All customers with IP addresses
        └── services.html  # Add/toggle services
```

## Order Status Flow
Received → Picked Up → Washing → Drying → Ready → Delivered

## IP Address Tracking
- Customer IP is recorded at Registration
- IP is updated on every Login
- Order IP is captured at Checkout
- All IPs visible in Admin → Dashboard & Customers panel
