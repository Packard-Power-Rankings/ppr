# Import the necessary functions from each module
from upload import upload_csv
from data_cleaning import clean_data
from data_enrichment import enrich_data
from main import run_calculations
from output import output_to_json


def main(file_path, output_file):
    """
    Main orchestration function to run the entire pipeline.
    :param file_path: Path to the input CSV file.
    :param output_file: Path to the output JSON file.
    """
    # Step 1: Upload and validate CSV
    df = upload_csv(file_path)
    if df is None:
        print("Error in CSV upload.")
        return

    # Step 2: Clean the data
    df = clean_data(df)

    # Step 3: Enrich the data with dummy values
    df = enrich_data(df)

    # Step 4: Run the core calculations (power difference, Z-scores, etc.)
    df = run_calculations(df)

    # Step 5: Output the final results to JSON
    output_to_json(df, output_file)


if __name__ == "__main__":
    # Example file paths for input and output
    input_csv_path = "CFootballEx.csv"
    output_json_path = "results_new.json"

    # Run the pipeline
    main(input_csv_path, output_json_path)
