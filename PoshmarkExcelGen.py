import os
import json
import pandas as pd
import ollama
import time
import random
import string
import csv
ALLOWED_CONDITIONS = ["NWT", "Like New", "Good", "Fair"]

def load_cached_tree(filepath="Cattrees\\poshmark_category_tree.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

CATTREE = load_cached_tree()

def search_category_tree(tree, final, image_path):
    if not tree:
        return final
    try:
        keys_list = list(tree.keys())
        prompt = f"Which OF THESE CATEGORIES fits this item best: {keys_list}. Respond with ONE CATEGORY from the list."
        response = ollama.chat(
            model='qwen2.5vl', 
            messages=[{'role': 'user', 'content': prompt, 'images': [image_path]}]
        )
        selection = response['message']['content'].strip()
        if selection in tree:
            final.append(selection)
            return search_category_tree(tree[selection], final, image_path)
        return final
    except Exception as e:
        return final


def generate_poshmark_listing(image_path):
    filename = os.path.basename(image_path)
    print(f"reading Image: {filename}")
    
    # Prompt updated for Poshmark's specific data requirements
    prompt = f"""
    You are an expert Poshmark reseller. Analyze the image and return ONLY a JSON object.
    
    Fields required:
    1. TITLE: Max 50 chars. Brand + Item Name.
    2. DESCRIPTION: Detailed description, including flaws.
    3. BRAND: The brand name (e.g., 'John Deere', 'Esso'). Use 'Unbranded' if unknown.
    4. CONDITION: Must be EXACTLY: {', '.join(ALLOWED_CONDITIONS)}.
    5. SIZE: Best estimate (e.g., 'OS' for hats, 'L', '10'). 
    6. LISTING_PRICE: Whole number between 30-120.
    """

    try:
        response = ollama.chat(
            model='qwen2.5vl', 
            messages=[{'role': 'user', 'content': prompt, 'images': [image_path]}],
            format='json',
            options={"num_ctx": 8192, "temperature": 0.2}
        )

        ai_output = json.loads(response['message']['content'])
        
        # Category Logic
        cat_path = []
        cat_path = search_category_tree(CATTREE, cat_path, image_path)
        
        # Map to Poshmark Template Headers
        return {
            "SKU": ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
            "ProductID":'',
            "Title": ai_output.get("TITLE"),
            "Description ": ai_output.get("DESCRIPTION"),
            "Department":  cat_path[0] if len(cat_path) > 0 else "",
            "Category": cat_path[1] if len(cat_path) > 1 else "",
            "Sub-category": cat_path[2] if len(cat_path) > 2 else "",
            "Quantity ": 1,
            "Size": ai_output.get("SIZE"),
            "Condition": ai_output.get("CONDITION"),
            "Brand": ai_output.get("BRAND"),
            "Color1": "",
            "Color2": "",
            "VariantGroupID": "",
            "VariantType": "",
            "VariantAttribute": "",
            "StyleTag1": "",
            "StyleTag2": "",
            "StyleTag3": "",
            "Orig price ": 0,
            "Listing price": ai_output.get("LISTING_PRICE"),
            "Shipping Discount": "",
            "Availability": "For Sale"
        }
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        raise





def create_poshmark_csv(processed_items):
    
    
    output_filename = time.strftime("GeneratedSpreadsheets\\Poshmark%Y%B%d-%HX%MX%S.csv")
    columns = [
        'SKU', 'ProductID (GTIN)', 'Title', 'Description ', 'Department', 
        'Category', 'Sub-category', 'Quantity ', 'Size', 'Condition', 
        'Brand', 'Color1', 'Color2', 'VariantGroupID', 'VariantType', 
        'VariantAttribute', 'Style Tag1', 'Style Tag2', 'Style Tag3', 
        'Orig price ', 'Listing price', 'Shipping Discount', 'Price Floor Percent', 
        'Minimum Price', 'Availability', 'Drop time', 'Other info'
    ]
    
    # Convert list of dicts to DataFrame
    df = pd.DataFrame(processed_items)
    
    # Reindex to ensure all Poshmark columns exist, even if empty
    df = df.reindex(columns=columns)
    
    # Export to CSV
    # quoting=csv.QUOTE_ALL ensures descriptions with commas don't shift columns
    df.to_csv(output_filename, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
    
    print(f"\nSaved {len(processed_items)} items to '{output_filename}'")




def main():

    image_folder = input("Paste photo folder path: ").strip()
    if image_folder.endswith('"') and image_folder.startswith('"'):
        image_folder = image_folder[1:-1]
    if not os.path.exists(image_folder): return

    target_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    readyforcsv = []

    for image_file in target_files:
        image_path = os.path.join(image_folder, image_file)
        try:
            listing = generate_poshmark_listing(image_path)
            readyforcsv.append(listing)
        except:
            continue

    if readyforcsv:
        create_poshmark_csv(readyforcsv)

if __name__ == "__main__":
    main()