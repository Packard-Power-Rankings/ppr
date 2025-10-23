import pandas as pd
from datetime import datetime, timedelta


def get_sundays(start_date, weeks_count):
    # Generate a list of Sundays starting from the given date
    sundays = [start_date + timedelta(weeks=i) for i in range(weeks_count)]
    return [date.strftime("%m/%d/%Y") for date in sundays]


def process_csv(input_file, output_file, date_for_week):
    # Read the CSV file
    df = pd.read_csv(input_file)

    # Create a new dataframe with only the required columns
    new_df = pd.DataFrame({
        'date': date_for_week,
        'home_team': df['home_team_id'],
        'visitor_team': df['visitor_team_id'],
        'home_score': df['original_home_score'],
        'visitor_score': df['original_visitor_score'],
        'home_field_advantage': df['home_field_advantage'].map({True: 0, False: 999})
    })

    # Write to a new CSV file
    new_df.to_csv(output_file, index=False)

    return new_df


# Example usage
if __name__ == "__main__":
    start_date = datetime.strptime("10/20/2024", "%m/%d/%Y")
    weeks_count = 10  # Number of weeks to process
    sundays = get_sundays(start_date, weeks_count)
    for i in range(3, 3 + weeks_count):
        input_file = f"/app/api/utils/algorithm/csv_weeks/week{i}.csv"  # Replace with your input file name
        output_file = f"week{i}.csv"  # Replace with your desired output file name

        try:
            date_for_week = sundays[i - 3]
            result = process_csv(input_file, output_file, date_for_week)
            print("Data processing completed successfully!")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
