import os
import json
import pandas as pd
import ollama  # Switched from google.genai
from thefuzz import process

# Facebook's Strict Variables
ALLOWED_CONDITIONS = ["New", "Used - Like New", "Used - Good", "Used - Fair"]

def load_categories(filepath="categories.txt"):
    """
    Reads the categories from a text file, one per line.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"{filepath} not found. Using minimal fallback.")
        return ["Clothing, Shoes & Accessories > Clothing"]

# Load these once at the start to save time
ALL_CATEGORIES = load_categories("categories.txt")

def find_exact_facebook_category(ai_guess):
    """
    Uses fuzzy matching to find the closest valid Facebook category.
    """
    best_match, confidence = process.extractOne(ai_guess, ALL_CATEGORIES)
    print(f"   ↳ Matched '{ai_guess}' -> '{best_match}' ({confidence}% confidence)")
    return best_match

def analyze_and_generate_listing(image_path):
    """
    Sends the image to the local Qwen2.5-VL model via Ollama.
    """
    filename = os.path.basename(image_path)
    print(f"Ollama is reading: {filename}")
    
    prompt = f"""
    You are an expert appraiser and online reseller. 
    Analyze the attached image. Identify the item, estimate value, and generate a listing.
    
    Constraints:
    YOU SHOULD ONLY HAVE 5 OUTPUT FIELDS IN YOUR JSON RESPONSE: TITLE, PRICE, CONDITION, DESCRIPTION, CATEGORY_GUESS.
    1. TITLE: Max 150 characters. Try to Include brand. Avoid clickbait. Make it short maybe 3-5 words.
    2. PRICE: Estimate fair market value. Try to make your estimate between 30-120$ MAX. If you think it's worth more than 120$ then just put 120$. If you think it's worth less than 30$ then just put 30$. Always include 'OBO' after the price.
    3. CONDITION: Must be EXACTLY: {', '.join(ALLOWED_CONDITIONS)}. 
    4. DESCRIPTION: Max 5000 chars. Include details, brand, model, flaws. 
       ALWAYS INCLUDE: 'The price you have listed' OBO and 'PICKUP PREFERRED WILL DELIVER AT FULL PRICE PLUS A FEE'.
    5. CATEGORY_GUESS: Try to match the item to a possible CATEGORY by making 10 keywords DO NOT TRY TO MATCH THE FORMATING OF ANY OF THE REAL CATEGORIES.
    JUST GENERATE 10 KEYWORDS THAT BEST DESCRIBE THE ITEM AND THEN GUESS THE BEST FITTING CATEGORY BASED ON THOSE KEYWORDS.
    THESE ARE ALL EXAMPLES OF POSSIBLE CATIGORIES, remeber do not try to match the formatting of these categories, just generate keywords and then guess the best fitting category based on those keywords:
    Tools & Home Improvement
    Sporting Goods//Exercise & Fitness
    Toys & Games
    Video Games & Consoles//Video Game Accessories
    Sporting Goods//Sports Equipment
    Musical Instruments
    Musical Instruments//Drums & Percussion Instruments
    Musical Instruments//General Music Accessories
    Musical Instruments//Guitars & Basses
    Musical Instruments//Pianos & Keyboard Instruments
    Jewelry & Watches//Jewelry
    Jewelry & Watches//Watches & Accessories
    Electronics//Video Games & Consoles
    Electronics//Home Audio & Video
    Clothing, Shoes & Accessories
    Clothing, Shoes & Accessories//Women's Handbags//Backpacks
    Books, Movies & Music
    Antiques & Collectibles
    Electronics//Cameras & Accessories
    Electronics//Computers, Laptops & Tablets

        
    Return ONLY a valid JSON object with keys: "TITLE", "PRICE", "CONDITION", "DESCRIPTION", "CATEGORY_GUESS".
    """

    try:
        # Pinging local Ollama server
        response = ollama.chat(
            model='qwen2.5vl', 
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_path] 
            }],
            format='json',
            options={
                "num_ctx": 8192,  # Prevents the "truncating input" error from your logs
                "temperature": 0.2 # Keeps the AI focused on the facts
            }
        )

        ai_output = json.loads(response['message']['content'])
        
        guess_raw = ai_output.get("CATEGORY_GUESS", "General")

        if isinstance(guess_raw, list):
            guess_string = " ".join(guess_raw)
            f"{guess_raw} {ai_output.get('TITLE','General')}"
            print(f"Extracted keywords for category guess: {guess_string}")
        else:
            guess_string = str(guess_raw)

        exact_category = find_exact_facebook_category(guess_string)
        

        final_listing = {
            "TITLE": ai_output.get("TITLE"),
            "PRICE": ai_output.get("PRICE"),
            "CONDITION": ai_output.get("CONDITION"),
            "DESCRIPTION": ai_output.get("DESCRIPTION"),
            "CATEGORY": exact_category 
        }

        return final_listing
        
    except Exception as e:
        print(f"Offline Error processing {filename}: {e}")
        raise

def create_bulk_upload_file(processed_items, output_filename="Generated_Listings.xlsx"):
    columns = ['TITLE', 'PRICE', 'CONDITION', 'DESCRIPTION', 'CATEGORY']
    df = pd.DataFrame(processed_items, columns=columns)
    
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Template")
        
    print(f"\nSaved {len(processed_items)} items to '{output_filename}'")

def main():
    raw_path = input("Please paste the full path to your photo folder: ").strip()
    
    image_folder = raw_path.replace('"', '').replace("'", "")

    if not os.path.exists(image_folder):
        print(f"The folder '{image_folder}' does not exist.")
        return
        
    target_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    
    if not target_files:
        print(f"No images found in '{image_folder}'.")
        return

    ready_for_excel = []

    for image_file in target_files:
        image_path = os.path.join(image_folder, image_file) 
        try:
            listing_data = analyze_and_generate_listing(image_path)
            ready_for_excel.append(listing_data)
            print(f"Generated: {listing_data.get('TITLE')} - ${listing_data.get('PRICE')}")
        except Exception as e:
            print(f"Skipping {image_file} due to error.")

    if ready_for_excel:
        create_bulk_upload_file(ready_for_excel)


if __name__ == "__main__":
    main()