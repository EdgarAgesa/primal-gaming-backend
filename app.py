from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image TEXT,
            category TEXT DEFAULT 'Consoles'
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# ── Products ──────────────────────────────────────────
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return jsonify([dict(p) for p in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    name = request.form.get('name')
    price = request.form.get('price')
    description = request.form.get('description')
    category = request.form.get('category', 'Consoles')
    image = request.files.get('image')

    image_filename = None
    if image:
        image_filename = image.filename
        image.save(os.path.join(UPLOAD_FOLDER, image_filename))

    conn = get_db()
    conn.execute('INSERT INTO products (name, price, description, image, category) VALUES (?, ?, ?, ?, ?)',
                 (name, price, description, image_filename, category))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product added!'}), 201

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    conn = get_db()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product deleted!'})

@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    name = request.form.get('name')
    price = request.form.get('price')
    description = request.form.get('description')
    image = request.files.get('image')

    conn = get_db()
    if image:
        image_filename = image.filename
        image.save(os.path.join(UPLOAD_FOLDER, image_filename))
        conn.execute('UPDATE products SET name=?, price=?, description=?, image=? WHERE id=?',
                     (name, price, description, image_filename, id))
    else:
        conn.execute('UPDATE products SET name=?, price=?, description=? WHERE id=?',
                     (name, price, description, id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product updated!'})

# ── Images ────────────────────────────────────────────
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ── Admin Auth ────────────────────────────────────────
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db()
    admin = conn.execute('SELECT * FROM admin WHERE username=? AND password=?',
                         (username, password)).fetchone()
    conn.close()

    if admin:
        return jsonify({'message': 'Login successful!', 'success': True})
    return jsonify({'message': 'Invalid credentials', 'success': False}), 401

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)