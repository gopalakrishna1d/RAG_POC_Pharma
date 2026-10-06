from database.db import get_connection


def main():
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            d.DeviationNumber,
            d.Status,
            d.Severity,
            s.SiteName
        FROM Deviations d
        INNER JOIN Sites s
            ON d.SiteId = s.EntityId
        ORDER BY d.CreatedOn
    """)

    rows = cursor.fetchall()

    for row in rows:
        print(
            row.DeviationNumber,
            "|",
            row.Status,
            "|",
            row.Severity,
            "|",
            row.SiteName
        )

    cursor.close()
    connection.close()


if __name__ == "__main__":
    main()