import psycopg

conn = psycopg.connect(host='127.0.0.1', port=5432, user='postgres', dbname='postgres')
conn.autocommit = True
cur = conn.cursor()

cur.execute("ALTER USER postgres WITH PASSWORD 'postgres';")
print("Password set to 'postgres' successfully!")

cur.execute("SELECT datname FROM pg_database WHERE datname = 'mydatabase';")
if not cur.fetchone():
    cur.execute("CREATE DATABASE mydatabase;")
    print("Created database 'mydatabase'!")
else:
    print("Database 'mydatabase' already exists!")

conn.close()
