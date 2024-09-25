import json


def output_to_json(df, output_file_path):
    """
    Converts the final DataFrame to JSON format and saves it to a file.
    :param df: DataFrame containing the final processed data.
    :param output_file_path: The file path where the JSON will be saved.
    :return: None
    """
    # Convert Timestamp columns to strings
    df['date'] = df['date'].astype(str)

    # Convert the DataFrame to a dictionary, then to JSON
    result_dict = df.to_dict(orient='records')

    # Write the JSON data to a file
    with open(output_file_path, 'w') as json_file:
        json.dump(result_dict, json_file, indent=4)

    print(f"Results saved to {output_file_path}")
