import sqlite3


def connect_db(db_name="sports_stats.db"):
    """Connect to the specified SQLite database or create it if it doesn't exist."""
    conn = sqlite3.connect(db_name)
    return conn


def init_db(conn):
    """Initialize the database with the required tables."""
    cursor = conn.cursor()

    # Create TeamWeeklyData table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TeamWeeklyData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER,
            week_id INTEGER,
            wins INTEGER,
            losses INTEGER,
            ties INTEGER,
            season_id INTEGER,
            num_games INTEGER,
            total_score REAL,
            power REAL
        )
    """)

    # Create Game table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Game (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_team_id INTEGER,
            visitor_team_id INTEGER,
            original_home_score REAL,
            original_visitor_score REAL,
            week_id INTEGER,
            season_id INTEGER
        )
    """)

    conn.commit()


def import_csv_to_db(conn, csv_file, table_name):
    """Import data from a CSV file into the specified table."""
    cursor = conn.cursor()
    import csv

    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        to_db = [(row['team_id'], row['week_id'], row['wins'], row['losses'], row['ties'], row['season_id'],
                  row['num_games'], row['total_score'], row['power']) for row in reader if table_name == "TeamWeeklyData"]
        cursor.executemany(
            f"INSERT INTO {table_name} (team_id, week_id, wins, losses, ties, season_id, num_games, total_score, power) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", to_db)

    conn.commit()


def close_db(conn):
    """Close the database connection."""
    conn.close()

# MongoDB versions of these functions can be added here later.
