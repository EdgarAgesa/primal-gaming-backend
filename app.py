from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image TEXT,
            category TEXT DEFAULT 'Consoles'
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cur.execute('SELECT COUNT(*) FROM admin')
    count = cur.fetchone()[0]
    if count == 0:
        username = os.getenv('ADMIN_USERNAME', 'admin')
        password = os.getenv('ADMIN_PASSWORD', 'primal123')
        cur.execute('INSERT INTO admin (username, password) VALUES (%s, %s)',
                    (username, password))
    conn.commit()
    cur.close()
    conn.close()

# ── Products ──────────────────────────────────────────
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM products')
    products = cur.fetchall()
    cur.close()
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
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO products (name, price, description, image, category) VALUES (%s, %s, %s, %s, %s)',
        (name, price, description, image_filename, category)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Product added!'}), 201

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM products WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Product deleted!'})

@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    name = request.form.get('name')
    price = request.form.get('price')
    description = request.form.get('description')
    category = request.form.get('category')
    image = request.files.get('image')

    conn = get_db()
    cur = conn.cursor()
    if image:
        image_filename = image.filename
        image.save(os.path.join(UPLOAD_FOLDER, image_filename))
        cur.execute(
            'UPDATE products SET name=%s, price=%s, description=%s, image=%s, category=%s WHERE id=%s',
            (name, price, description, image_filename, category, id)
        )
    else:
        cur.execute(
            'UPDATE products SET name=%s, price=%s, description=%s, category=%s WHERE id=%s',
            (name, price, description, category, id)
        )
    conn.commit()
    cur.close()
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
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM admin WHERE username=%s AND password=%s',
                (username, password))
    admin = cur.fetchone()
    cur.close()
    conn.close()

    if admin:
        return jsonify({'message': 'Login successful!', 'success': True})
    return jsonify({'message': 'Invalid credentials', 'success': False}), 401

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)