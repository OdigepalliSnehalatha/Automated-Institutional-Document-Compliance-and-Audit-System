import psycopg2
try:
    connection = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="mydatabase",
        user="postgres",
        password="sneha@429reddy"
    )

    print("Database connection successful!")

    connection.close()

except Exception as error:
    print("Database connection failed:")
    print(error)