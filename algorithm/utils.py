import csv
from datetime import datetime


def read_csv_file(csv_file_path):
    """
    Read a CSV file and return a list of dictionaries, one for each row.
    """
    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return list(reader)


def write_csv_file(data, csv_file_path, fieldnames):
    """
    Write a list of dictionaries to a CSV file.
    """
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def convert_date(date_string, date_format="%Y-%m-%d"):
    """
    Convert a date string to a datetime object based on a specified format.
    """
    try:
        return datetime.strptime(date_string, date_format)
    except ValueError:
        return None


def validate_numeric(value):
    """
    Validate if the provided string is a numeric value.
    """
    try:
        float(value)
        return True
    except ValueError:
        return False


def print_log(message, level="INFO"):
    """
    Print a log message with a timestamp.
    """
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {level} - {message}")
