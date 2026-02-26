import json
import os

BASE_PATH = r"C:\Users\gcboo\OneDrive\Desktop\blinkit_knowledge_graph\data\json"
OUTPUT_PATH = r"C:\Users\gcboo\OneDrive\Desktop\blinkit_knowledge_graph\data\processed"

os.makedirs(OUTPUT_PATH, exist_ok=True)

input_file = os.path.join(BASE_PATH, "products_clean.json")
output_file = os.path.join(OUTPUT_PATH, "products_clean_graph.json")

clean_products = []

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        # Use 'title' instead of 'name'
        clean_products.append({
            "product_id": record["product_id"],
            "title": record.get("title", "")  # fallback to empty string
        })

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(clean_products, f, indent=2)

print(f"Clean products saved: {len(clean_products)} records")
