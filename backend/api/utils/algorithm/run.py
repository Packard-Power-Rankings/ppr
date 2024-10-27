# Import the necessary functions from each module
from io import BytesIO
from typing import Tuple
from fastapi import HTTPException
from .upload import upload_csv
from .data_cleaning import clean_data
from .data_enrichment import enrich_data
from .main import run_calculations
from .output import output_to_json
from service.teams import retrieve_csv_file


async def main(level_key: Tuple):
    """
    Main orchestration function to run the entire pipeline.
    :param file_path: Path to the input CSV file.
    :param output_file: Path to the output JSON file.
    """
    
    # Step 1: Upload and validate CSV
    query = {
        "sport_type": level_key[0],
        "gender": level_key[1],
        "level": level_key[2]
    }
    csv_file = await retrieve_csv_file(query)
    if not csv_file:
        raise HTTPException(status_code=404, detail="No CSV file found")

    csv_content = BytesIO(csv_file['file_data'])
    df = upload_csv(csv_content)
    if df is None:
        raise HTTPException(status_code=400, detail='No CSV file found')

    # Step 2: Clean the data
    df = clean_data(df)

    # Step 3: Enrich the data with dummy values
    df = enrich_data(df, level_key)

    # Step 4: Run the core calculations (power difference, Z-scores, etc.)
    df = run_calculations(df, level_key)

    # Step 5: Output the final results to JSON
    await output_to_json(df, level_key)


if __name__ == "__main__":
    # Example file paths for input and output
    input_csv_path = "CFootballEx.csv"
    output_json_path = "results.json"

    # Run the pipeline
    # main(input_csv_path, ('football', 'mens', 'college'))
