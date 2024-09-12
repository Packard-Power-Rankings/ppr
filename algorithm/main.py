import database
import csv
import sys


def main(csv_file):
    db_conn = database.connect_db()
    database.init_db(db_conn)

    # Load CSV data into the database
    database.import_csv_to_db(db_conn, csv_file)

    # Run the algorithm
    # Example: update_record(db_conn, 1, 2, 3)

    db_conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_csv_file>")
        sys.exit(1)

    main(sys.argv[1])
