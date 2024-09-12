# Configuration for the database
DATABASE_CONFIG = {
    'name': 'sports_stats.db',
    'user': '',  # Not needed for SQLite, but useful for other databases
    'password': '',  # Not needed for SQLite, but useful for other databases
    'host': '',  # Not needed for SQLite, but useful for other databases
}

# Path to CSV files
CSV_FILE_PATH = 'path_to_your_csv_files/'

# Additional application settings
# Example: API keys, logging settings, etc.

# When you switch to MongoDB, you can add configurations like this:
MONGO_DATABASE_CONFIG = {
    'uri': 'mongodb://localhost:27017/',
    'db_name': 'your_mongodb_name',
}

# Other potential configurations might include:
LOGGING_CONFIG = {
    'level': 'DEBUG',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'datefmt': '%m/%d/%Y %I:%M:%S %p',
    'filename': 'application.log',
    'filemode': 'w',
}
