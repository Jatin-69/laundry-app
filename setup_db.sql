-- Run this in MySQL before starting the app
-- mysql -u root -p < setup_db.sql

CREATE DATABASE IF NOT EXISTS laundry_db;
USE laundry_db;

-- Tables are auto-created by SQLAlchemy when you run app.py
-- Just create the database here

-- To change MySQL credentials, edit app.py line:
-- app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://USER:PASSWORD@HOST/laundry_db'

-- Default admin credentials:
-- Email: admin@laundry.com
-- Password: admin123
