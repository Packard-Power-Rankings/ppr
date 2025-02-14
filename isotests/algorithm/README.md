# **Packard Power Rankings Pipeline**

## **Overview**
This part of the project processes sports game data from a sample CSV file, performs data cleaning, adds enrichment values (e.g., R-values, power rankings), runs key calculations (Z-scores, power differences, expected and actual performance), and outputs the results in JSON format. The project is designed to be modular and database-agnostic, allowing easy future integration with different data sources.

---

## **Structure**

### 1. **`run.py`**
   - **Description**: The main orchestrating script that ties all the modules together.
   - **Functionality**: 
     - Loads the CSV file.
     - Calls data cleaning, enrichment, calculation, and output functions in sequence.
     - The entry point for running the entire pipeline.

### 2. **`upload.py`**
   - **Description**: Handles uploading and validating the CSV data.
   - **Functionality**:
     - Loads the CSV file into a DataFrame.
     - Checks for required columns and validates the input format.
     - **Future integration**: If you later decide to pull data from APIs or databases instead of CSV files, this module should be updated accordingly.

### 3. **`data_cleaning.py`**
   - **Description**: Cleans and normalizes the raw data.
   - **Functionality**:
     - Ensures all numeric fields (e.g., scores) are correctly formatted.
     - Handles missing values and ensures the integrity of the data.
     - **Future integration**: This module can be expanded to include additional validation rules based on real-world data constraints or specific database requirements.

### 4. **`data_enrichment.py`**
   - **Description**: Enriches the cleaned data with additional fields.
   - **Functionality**:
     - Adds placeholder values such as R-values, power rankings, and win/loss ratios.
     - **Future integration**: Replace dummy values with real data fetched from a database or external data sources (e.g., team performance history). This module is the ideal place to integrate database getters for power rankings and other stats.

### 5. **`main.py`**
   - **Description**: Runs the main algorithm for calculations.
   - **Functionality**:
     - Calculates Z-scores, power differences, expected and actual performance, and predicts scores.
     - **Future integration**: This module can remain largely unchanged, as the calculations rely on the enriched data, which will eventually come from a database.

### 6. **`output.py`**
   - **Description**: Formats and saves the final results.
   - **Functionality**:
     - Converts the final processed DataFrame into JSON format.
     - Saves the JSON file to disk.
     - **Future integration**: Modify this module to write the results directly to a database or integrate with a REST API for real-time data reporting.

---

## **Future Database Integration Points**

1. **`data_enrichment.py`**:
   - Replace the placeholder values (power rankings, win/loss ratios) with real data from a database.
   - Integrate database queries to pull R-values, power rankings, team statistics, or even historical data.
   
2. **`upload.py`** (Optional):
   - If CSV input is replaced by a database or API feed, modify `upload.py` to pull data directly from those sources instead of loading from files.

3. **`output.py`**:
   - Replace the JSON file output with direct database writes.
   - Modify to integrate with SQL, MongoDB, or other databases using the chosen database driver or ORM (e.g., SQLAlchemy or MongoEngine).

---

## **How to Run**
1. Place your input CSV file in the project folder.
2. Modify the `file_path` and `output_file` variables in `run.py` with your input CSV path and desired output path.
3. Run the script:
   ```bash
   python run.py
