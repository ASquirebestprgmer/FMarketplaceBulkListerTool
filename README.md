# Facebook Marketplace Bulk Listing Excel Generator

This project generates an Excel file for bulk listing items on Facebook Marketplace by analyzing product images and producing listing metadata.

## Author Notes 
    Facebook does not allow you to automate the listing posting however
    they do allow you to upload text through an xlxs file on the desktop 
    version. 
    I do realize that a lot of the descriptions will be wrong, However, it'll be small details that will be fixed. 
    Facebook also hates it when you try to automate anything, You'll have to upload the images separately. This is mostly just for title and description.

    This project has a very small amount of use cases, However I thought I'd share it. 
    It saves me time because the descriptions are written and I don't have to write every description, title or category.
    
    (April 2026):The categories needs more work, will be updating it so it is better at guessing the categories. 

    - I will say that the pricing is not to be trusted. No model can accurately price out items without more information or ebay sold listing API. 


## What it does

- Reads item images from a local folder
- Uses a local Ollama image-capable model (qwen2.5vl) to analyze each image
- Generates listing fields: title, price, condition, description, and category
- Matches the AI-generated category guess to a valid Facebook Marketplace category using fuzzy matching
- Writes the final listings into Generated_Listings.xlsx

## Files

- excelGenerator.py - main script that processes images and writes Excel output
- categories.txt - list of valid Facebook Marketplace categories used for fuzzy matching

## Requirements

- Python 3.8+
- pandas
- openpyxl
- ollama
- 	hefuzz

Install dependencies with:

`powershell
python -m pip install pandas openpyxl ollama thefuzz
`

## Setup

1. Make sure a local Ollama server is running and can access the qwen2.5vl model.
2. Place images to process in the folder configured in excelGenerator.py.
   - By default the script uses:
     G:\0-PHOTOS\149___04\stuff
3. Update the image_folder variable in excelGenerator.py if you want a different source folder.

## Usage

Run the script from the project directory:

`powershell
python excelGenerator.py
`

The script will:

1. Scan the configured image folder for .jpg, .png, and .jpeg files
2. Send each image to Ollama for listing analysis
3. Match the AI category guess to an exact Facebook category
4. Save the results to Generated_Listings.xlsx

## Notes

- If the categories.txt file is missing, the script falls back to a minimal default category.
- The AI response is expected to include exactly these JSON fields: TITLE, PRICE, CONDITION, DESCRIPTION, CATEGORY_GUESS.
- The script enforces Facebook Marketplace condition values: New, Used - Like New, Used - Good, Used - Fair.
- The generated Excel file is saved in the same folder as the script.

## Customization

- Change image_folder in excelGenerator.py to point to your photo directory.
- Add or update categories in categories.txt to improve matching accuracy.
- Adjust the prompt or output fields in nalyze_and_generate_listing() if you need a different listing format.
