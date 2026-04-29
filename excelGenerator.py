import os
import json
import pandas as pd
import ollama  

# Facebook's Strict Variables
ALLOWED_CONDITIONS = ["New", "Used - Like New", "Used - Good", "Used - Fair"]



def load_cached_tree(filepath="category_tree.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


CATTREE = load_cached_tree()

def search_category_tree(tree,final, image_path):
    """
    Recursively searches the category tree for a match to the guess.
    """
    
    if not tree:
        print(final)
        return final
    
    try:
        # Prompting with current keys: ['Bird Supplies', 'Cat Supplies', etc.]
        keys_list = list(tree.keys())
        prompt = f"Which OF THESE CATEGORIES fits this item best: {keys_list}. Respond with ONE CATEGORY from the list."
        
        response = ollama.chat(
            model='qwen2.5vl', 
            messages=[{'role': 'user', 'content': prompt, 'images': [image_path]}]
        )
        
        # Clean the response (LLMs sometimes add extra whitespace or dots)
        selection = response['message']['content'].strip()

        if selection in tree:
            final.append(selection)
            # Recursive call into the next level
            return search_category_tree(tree[selection], final, image_path)
        else:
            print(f"AI returned '{selection}', which isn't in {keys_list}")
            return final # Or handle 'None' logic here
            
    except Exception as e:
        print(f"Error: {e}")
        return final


def generate_listing(image_path):
    """
    Sends the image to the local Qwen2.5-VL model via Ollama.
    """
    filename = os.path.basename(image_path)
    print(f"Ollama is reading: {filename}")
    
    prompt = f"""
    You are an expert appraiser and online reseller. 
    Analyze the attached image. Identify the item, estimate value, and generate a listing.
    
    Constraints:
    YOU SHOULD ONLY HAVE 4 OUTPUT FIELDS IN YOUR JSON RESPONSE: TITLE, PRICE, CONDITION, DESCRIPTION.
    1. TITLE: Max 150 characters. Try to Include brand. Avoid clickbait. Make it short maybe 3-5 words.
    2. PRICE: ALWAYS A WHOLE NUMBER NO TEXT Estimate fair market value. Try to make your estimate between 30-120$ MAX. If you think it's worth more than 120$ then just put 120$. If you think it's worth less than 30$ then just put 30$. Always include 'OBO' after the price.
    3. CONDITION: Must be EXACTLY: {', '.join(ALLOWED_CONDITIONS)}. 
    4. DESCRIPTION: Max 5000 chars. Include details, brand, model, flaws. 
       ALWAYS INCLUDE: 'The price you have listed' OBO ONLY IN THE DESCRIPTION and 'PICKUP PREFERRED WILL DELIVER AT FULL PRICE PLUS A FEE'.
        
    Return ONLY a valid JSON object with keys: "TITLE", "PRICE", "CONDITION", "DESCRIPTION"
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
        
        
        final = []
        final = search_category_tree(CATTREE, final,image_path)
        print(f"Exact category found: {final}")
        final_category = "//".join(final) 
        
        print(f"Final category for {filename}: {final_category}")
        final_listing = {
            "TITLE": ai_output.get("TITLE"),
            "PRICE": ai_output.get("PRICE"),
            "CONDITION": ai_output.get("CONDITION"),
            "DESCRIPTION": ai_output.get("DESCRIPTION"),
            "CATEGORY": final_category 
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

    image_folder = input("Please paste the full path to your photo folder: ").strip() # "G:\0-PHOTOS\149___04\stuff"

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
            listing_data = generate_listing(image_path)
            ready_for_excel.append(listing_data)
            print(f"Generated: {listing_data.get('TITLE')} - ${listing_data.get('PRICE')}")
        except Exception as e:
            print(f"Skipping {image_file} due to error.")

    if ready_for_excel:
        create_bulk_upload_file(ready_for_excel)


if __name__ == "__main__":
    main()