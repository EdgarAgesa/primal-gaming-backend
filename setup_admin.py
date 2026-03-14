import sqlite3

conn = sqlite3.connect('database.db')

# Change these to whatever you want
USERNAME = 'admin'
PASSWORD = 'primal123'

conn.execute('''
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
''')

conn.execute('DELETE FROM admin')  # clear old admin if any
conn.execute('INSERT INTO admin (username, password) VALUES (?, ?)', (USERNAME, PASSWORD))
conn.commit()
conn.close()

print('✅ Admin account created successfully!')
print(f'Username: {USERNAME}')
print(f'Password: {PASSWORD}')