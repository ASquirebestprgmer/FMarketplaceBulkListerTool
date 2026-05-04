# Facebook Marketplace and Poshmark Bulk Listing Generator

This project generates bulk upload files for both Facebook Marketplace and Poshmark from local product photos.
It analyzes each image with a local Ollama image-capable model, builds listing metadata, and saves the results in a spreadsheet or CSV.

## What it does

- Prompts for a local image folder path
- Sends each image to a local Ollama model (`qwen2.5vl`) for item analysis
- Generates listing fields: TITLE, PRICE, CONDITION, DESCRIPTION, CATEGORY
- Resolves the category using a cached Facebook category tree
- Saves the results to a timestamped Excel file in `GeneratedSpreadsheets/`

## Files

- `FacebookExcelGen.py` - main script for Facebook Marketplace bulk listings
- `PoshmarkExcelGen.py` - alternate script for generating a Poshmark bulk upload CSV
- `Cattrees/facebook_category_tree.json` - Facebook category tree used for category selection
- `Cattrees/poshmark_category_tree.json` - Poshmark category tree used by the Poshmark script
- `GeneratedSpreadsheets/` - output folder for generated Excel/CSV files

## Requirements

- Python 3.8+
- pandas
- openpyxl
- ollama

Install dependencies with:

```powershell
python -m pip install pandas openpyxl ollama
```

## Setup

1. Run a local Ollama server and make sure the `qwen2.5vl` model is available.
2. Place the images you want to process in a local folder.
3. Confirm the category tree files exist under `Cattrees/`.

## Usage

From the project directory, choose one of the two scripts:

```powershell
python FacebookExcelGen.py
```

or

```powershell
python PoshmarkExcelGen.py
```

Then paste the full path to your image folder when prompted.

### What happens next

1. The script scans the folder for `.jpg`, `.png`, and `.jpeg` files.
2. Each image is analyzed by the local Ollama model.
3. It builds listing metadata and selects a matching Facebook category.
4. The final bulk upload spreadsheet is saved to `GeneratedSpreadsheets/`.

## Output

- Facebook output files are saved as `GeneratedSpreadsheets\Facebook<date>.xlsx`
- Poshmark output files are saved as `GeneratedSpreadsheets\Poshmark<date>.csv`

## Notes

- Facebook does not allow auto-posting; this tool only creates the listing spreadsheet.
- Images must still be uploaded manually when you create listings on Facebook.
- The generated titles, prices, and descriptions should be reviewed before posting.

## Customization

- Modify `FacebookExcelGen.py` to adjust prompt rules, allowed conditions, or output formatting.
- Update `Cattrees/facebook_category_tree.json` to improve category matching.
- Use `PoshmarkExcelGen.py` if you want a Poshmark-compatible CSV output instead of Facebook Excel.
