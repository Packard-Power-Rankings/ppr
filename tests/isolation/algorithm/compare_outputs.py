import pandas as pd


def compare_outputs(generated_file, reference_file, key_columns, ignore_columns=None):
    """
    Compare generated and reference output files.
    :param generated_file: Path to the generated output CSV.
    :param reference_file: Path to the reference output CSV.
    :param key_columns: List of columns to compare.
    :param ignore_columns: List of columns to ignore during comparison.
    :return: DataFrame with differences, if any.
    """
    try:
        # Load files
        generated_df = pd.read_csv(generated_file)
        reference_df = pd.read_csv(reference_file)

        # Drop ignored columns
        if ignore_columns:
            generated_df = generated_df.drop(
                columns=ignore_columns, errors='ignore')
            reference_df = reference_df.drop(
                columns=ignore_columns, errors='ignore')

        # Ensure only key columns are compared
        generated_df = generated_df[key_columns]
        reference_df = reference_df[key_columns]

        # Compare DataFrames
        differences = generated_df.compare(reference_df)

        if differences.empty:
            print(
                f"No differences found between {generated_file} and {reference_file}.")
        else:
            print(
                f"Differences found between {generated_file} and {reference_file}:")

        return differences
    except Exception as e:
        raise ValueError(
            f"Error comparing files {generated_file} and {reference_file}: {e}")
