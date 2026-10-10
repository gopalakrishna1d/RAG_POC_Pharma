from database.db import get_connection


def main():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM CAPA LIMIT 10
    """)

    rows = cursor.fetchall()

    for row in rows:
        print(row)

    cursor.close()
    connection.close()


if __name__ == "__main__":
    main()