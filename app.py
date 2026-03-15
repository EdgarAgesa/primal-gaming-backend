from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()

app = Flask(__name__)
CORS(app)

# ── Cloudinary Config ─────────────────────────────────
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

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

    image_url = None
    if image:
        upload_result = cloudinary.uploader.upload(
            image,
            folder='primal-gaming-hub',
            resource_type='image'
        )
        image_url = upload_result['secure_url']

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO products (name, price, description, image, category) VALUES (%s, %s, %s, %s, %s)',
        (name, price, description, image_url, category)
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
        upload_result = cloudinary.uploader.upload(
            image,
            folder='primal-gaming-hub',
            resource_type='image'
        )
        image_url = upload_result['secure_url']
        cur.execute(
            'UPDATE products SET name=%s, price=%s, description=%s, image=%s, category=%s WHERE id=%s',
            (name, price, description, image_url, category, id)
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